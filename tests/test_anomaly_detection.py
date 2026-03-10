import numpy as np

from src.statistics.anomaly import grubbs_test, rolling_zscore, iqr_outliers


def test_grubbs_no_outlier():
    data = [1.0, 1.1, 0.9, 1.0, 1.05, 0.95, 1.02, 0.98]
    result = grubbs_test(data)
    assert result["is_outlier"] is False


def test_grubbs_with_outlier():
    data = [1.0, 1.1, 0.9, 1.0, 1.05, 0.95, 1.02, 0.98, 5.0]
    result = grubbs_test(data)
    assert result["is_outlier"] is True
    assert result["outlier_value"] == 5.0


def test_grubbs_small_dataset():
    data = [1.0, 2.0]
    result = grubbs_test(data)
    assert result["is_outlier"] is False


def test_rolling_zscore():
    data = [1.0] * 50 + [5.0]
    zscores = rolling_zscore(data, window=30)
    assert len(zscores) == len(data)
    assert zscores[-1] > 2.0


def test_rolling_zscore_short():
    data = [1.0, 2.0, 3.0]
    zscores = rolling_zscore(data, window=30)
    assert all(z == 0.0 for z in zscores)


def test_iqr_outliers():
    data = [1, 2, 3, 4, 5, 100]
    result = iqr_outliers(data)
    assert 100 in result["outliers"]


def test_iqr_no_outliers():
    data = [1.0, 1.5, 2.0, 2.5, 3.0]
    result = iqr_outliers(data)
    assert len(result["outliers"]) == 0
