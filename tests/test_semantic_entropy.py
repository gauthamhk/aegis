import numpy as np

from src.statistics.entropy import shannon_entropy, semantic_entropy_from_clusters


def test_shannon_entropy_uniform():
    probs = [0.5, 0.5]
    entropy = shannon_entropy(probs)
    assert abs(entropy - 0.693) < 0.01


def test_shannon_entropy_certain():
    probs = [1.0]
    entropy = shannon_entropy(probs)
    assert entropy == 0.0


def test_semantic_entropy_single_cluster():
    labels = np.array([1, 1, 1, 1, 1])
    entropy = semantic_entropy_from_clusters(labels)
    assert entropy == 0.0


def test_semantic_entropy_multiple_clusters():
    labels = np.array([1, 2, 3, 4, 5])
    entropy = semantic_entropy_from_clusters(labels)
    assert entropy > 1.5
