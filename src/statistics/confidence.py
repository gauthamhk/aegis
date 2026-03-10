import math

import numpy as np
from scipy import stats


def wilson_score_interval(
    successes: int, total: int, confidence: float = 0.95
) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p = successes / total
    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
    return (max(0, center - spread), min(1, center + spread))


def bootstrap_confidence_interval(
    data: list[float], n_bootstrap: int = 1000, confidence: float = 0.95
) -> tuple[float, float]:
    if not data:
        return (0.0, 0.0)
    arr = np.array(data)
    means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
    alpha = (1 - confidence) / 2
    lower = float(np.percentile(means, alpha * 100))
    upper = float(np.percentile(means, (1 - alpha) * 100))
    return (lower, upper)
