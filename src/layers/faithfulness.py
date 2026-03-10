import asyncio
import json
import math

import numpy as np

from src.embeddings.encoder import encode_texts, cosine_similarity
from src.proxy.llm_client import llm_client
from src.proxy.request_models import Claim, FaithfulnessResult
from src.utils.config import get_default_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

DECOMPOSE_PROMPT = """Decompose the following text into individual atomic factual claims.
Return ONLY a JSON array, no other text: [{"claim": "string", "claim_type": "factual|opinion|hedged"}]

Text:
{text}"""

VERIFY_PROMPT = """Given this context:
{context}

Is this claim supported by the context?
Claim: {claim}

Respond with exactly one word: SUPPORTED or CONTRADICTED or NOT_MENTIONED"""


def _wilson_score(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
    return (max(0, center - spread), min(1, center + spread))


async def _decompose_claims(text: str) -> list[Claim]:
    prompt = DECOMPOSE_PROMPT.format(text=text)
    try:
        response = await llm_client.generate(
            prompt, provider="gemini", temperature=0.0, max_tokens=2048
        )
        response = response.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[1].rsplit("```", 1)[0]
        claims_data = json.loads(response)
        return [
            Claim(text=c["claim"], claim_type=c.get("claim_type", "factual"))
            for c in claims_data
        ]
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("faithfulness.decompose_failed", error=str(e))
        return [Claim(text=text, claim_type="factual")]


async def _verify_claim(
    claim: Claim, context_chunks: list[str], context_embeddings: np.ndarray, config: dict
) -> Claim:
    if claim.claim_type != "factual":
        claim.verdict = "OPINION"
        claim.confidence = 1.0
        return claim

    claim_embedding = encode_texts([claim.text])[0]
    similarities = [cosine_similarity(claim_embedding, ce) for ce in context_embeddings]
    max_sim = max(similarities) if similarities else 0.0
    best_chunk_idx = int(np.argmax(similarities)) if similarities else 0

    threshold = config.get("faithfulness", {}).get("similarity_threshold", 0.75)

    if max_sim >= threshold:
        claim.verdict = "SUPPORTED"
        claim.confidence = float(max_sim)
        claim.supporting_context = context_chunks[best_chunk_idx] if context_chunks else None
    else:
        try:
            verify_prompt = VERIFY_PROMPT.format(
                context=context_chunks[best_chunk_idx] if context_chunks else "No context provided",
                claim=claim.text,
            )
            result = await llm_client.generate(
                verify_prompt, provider="gemini", temperature=0.0, max_tokens=20
            )
            verdict = result.strip().upper()
            if verdict in ("SUPPORTED", "CONTRADICTED", "NOT_MENTIONED"):
                claim.verdict = verdict
            else:
                claim.verdict = "NOT_MENTIONED"
            claim.confidence = float(max_sim)
            if claim.verdict == "SUPPORTED":
                claim.supporting_context = context_chunks[best_chunk_idx] if context_chunks else None
        except Exception as e:
            logger.warning("faithfulness.verify_failed", claim=claim.text, error=str(e))
            claim.verdict = "NOT_MENTIONED"
            claim.confidence = float(max_sim)

    return claim


def _chunk_context(context: str, chunk_size: int = 500) -> list[str]:
    words = context.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i : i + chunk_size]))
    return chunks if chunks else [""]


async def verify_faithfulness(
    response_text: str, context: str | None = None
) -> FaithfulnessResult:
    config = get_default_config()
    claims = await _decompose_claims(response_text)

    if not context:
        return FaithfulnessResult(
            score=0.5,
            total_claims=len(claims),
            supported_claims=0,
            claims=claims,
            unsupported_claims=[c for c in claims if c.claim_type == "factual"],
        )

    context_chunks = _chunk_context(context)
    context_embeddings = encode_texts(context_chunks)

    max_claims = config.get("faithfulness", {}).get("max_claims_per_response", 20)
    factual_claims = [c for c in claims if c.claim_type == "factual"][:max_claims]
    other_claims = [c for c in claims if c.claim_type != "factual"]

    verified = await asyncio.gather(
        *[_verify_claim(c, context_chunks, context_embeddings, config) for c in factual_claims]
    )

    supported = [c for c in verified if c.verdict == "SUPPORTED"]
    unsupported = [c for c in verified if c.verdict != "SUPPORTED"]
    total_factual = len(factual_claims)
    score = len(supported) / total_factual if total_factual > 0 else 1.0

    all_claims = list(verified) + other_claims

    logger.info(
        "faithfulness.complete",
        score=score,
        total=total_factual,
        supported=len(supported),
    )

    return FaithfulnessResult(
        score=score,
        total_claims=len(all_claims),
        supported_claims=len(supported),
        claims=all_claims,
        unsupported_claims=unsupported,
    )
