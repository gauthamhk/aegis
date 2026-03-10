import math

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

from src.embeddings.encoder import encode_texts
from src.proxy.llm_client import llm_client
from src.proxy.request_models import EntropyResult
from src.utils.config import get_default_config, settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _calculate_entropy(labels: np.ndarray) -> float:
    unique, counts = np.unique(labels, return_counts=True)
    total = len(labels)
    probabilities = counts / total
    entropy = -sum(p * math.log(p) for p in probabilities if p > 0)
    return entropy


def _classify_risk(entropy: float, config: dict) -> str:
    se_config = config.get("semantic_entropy", {})
    low = se_config.get("low_entropy", 0.5)
    medium = se_config.get("medium_entropy", 1.5)
    if entropy < low:
        return "low"
    elif entropy < medium:
        return "medium"
    else:
        return "high"


async def detect_semantic_entropy(
    prompt: str, original_response: str
) -> EntropyResult:
    config = get_default_config()
    se_config = config.get("semantic_entropy", {})
    n = settings.entropy_sample_count
    temperature = se_config.get("temperature", 0.7)
    distance_threshold = se_config.get("cluster_distance_threshold", 0.3)

    responses = await llm_client.generate_multiple(
        prompt, n=n, temperature=temperature
    )
    responses.insert(0, original_response)

    if len(responses) < 2:
        return EntropyResult(
            entropy=0.0,
            num_clusters=1,
            risk_level="low",
            cluster_details=[{"cluster_id": 0, "count": len(responses)}],
        )

    embeddings = encode_texts(responses)
    distance_matrix = 1 - np.dot(embeddings, embeddings.T)
    np.fill_diagonal(distance_matrix, 0)
    condensed = distance_matrix[np.triu_indices(len(responses), k=1)]

    linkage_matrix = linkage(condensed, method="average")
    labels = fcluster(linkage_matrix, t=distance_threshold, criterion="distance")

    entropy = _calculate_entropy(labels)
    risk_level = _classify_risk(entropy, config)

    cluster_details = []
    for cluster_id in np.unique(labels):
        member_indices = np.where(labels == cluster_id)[0]
        cluster_details.append({
            "cluster_id": int(cluster_id),
            "count": int(len(member_indices)),
            "sample": responses[member_indices[0]][:200],
        })

    logger.info(
        "semantic_entropy.complete",
        entropy=round(entropy, 3),
        clusters=len(cluster_details),
        risk=risk_level,
    )

    return EntropyResult(
        entropy=round(entropy, 3),
        num_clusters=len(cluster_details),
        risk_level=risk_level,
        cluster_details=cluster_details,
    )
