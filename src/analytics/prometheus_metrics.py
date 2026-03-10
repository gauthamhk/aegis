from prometheus_client import Counter, Histogram, Gauge, generate_latest

requests_total = Counter(
    "aegis_requests_total",
    "Total verification requests",
    ["action", "domain"],
)

verification_latency = Histogram(
    "aegis_verification_latency_seconds",
    "Verification pipeline latency",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0],
)

faithfulness_score = Histogram(
    "aegis_faithfulness_score",
    "Faithfulness scores distribution",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

entropy_score = Histogram(
    "aegis_entropy_score",
    "Semantic entropy scores distribution",
    buckets=[0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
)

active_verifications = Gauge(
    "aegis_active_verifications",
    "Currently running verifications",
)

drift_events_total = Counter(
    "aegis_drift_events_total",
    "Total drift detection events",
    ["severity"],
)


def get_metrics() -> bytes:
    return generate_latest()
