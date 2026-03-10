import math

import numpy as np


def shannon_entropy(probabilities: list[float]) -> float:
    return -sum(p * math.log(p) for p in probabilities if p > 0)


def semantic_entropy_from_clusters(labels: np.ndarray) -> float:
    unique, counts = np.unique(labels, return_counts=True)
    probabilities = counts / len(labels)
    return shannon_entropy(probabilities.tolist())
