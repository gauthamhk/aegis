import numpy as np
from scipy import stats


def grubbs_test(data: list[float], alpha: float = 0.05) -> dict:
    if len(data) < 3:
        return {"is_outlier": False, "statistic": 0, "critical_value": 0}

    arr = np.array(data)
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)

    if std == 0:
        return {"is_outlier": False, "statistic": 0, "critical_value": 0}

    deviations = np.abs(arr - mean)
    max_idx = np.argmax(deviations)
    G = deviations[max_idx] / std

    n = len(data)
    t_crit = stats.t.ppf(1 - alpha / (2 * n), n - 2)
    critical_value = ((n - 1) / np.sqrt(n)) * np.sqrt(t_crit**2 / (n - 2 + t_crit**2))

    return {
        "is_outlier": G > critical_value,
        "statistic": float(G),
        "critical_value": float(critical_value),
        "outlier_value": float(arr[max_idx]),
        "outlier_index": int(max_idx),
    }


def rolling_zscore(values: list[float], window: int = 30) -> list[float]:
    if len(values) < window:
        return [0.0] * len(values)

    arr = np.array(values)
    zscores = []
    for i in range(len(arr)):
        if i < window:
            zscores.append(0.0)
        else:
            window_data = arr[i - window : i]
            mean = np.mean(window_data)
            std = np.std(window_data, ddof=1)
            if std == 0:
                zscores.append(0.0)
            else:
                zscores.append(float((arr[i] - mean) / std))
    return zscores


def iqr_outliers(data: list[float]) -> dict:
    if len(data) < 4:
        return {"lower_bound": 0, "upper_bound": 0, "outliers": []}

    arr = np.array(data)
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outlier_mask = (arr < lower) | (arr > upper)
    return {
        "lower_bound": float(lower),
        "upper_bound": float(upper),
        "outliers": arr[outlier_mask].tolist(),
        "outlier_indices": np.where(outlier_mask)[0].tolist(),
    }
