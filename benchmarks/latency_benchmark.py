"""Measure added latency per verification layer."""

import asyncio
import time
import statistics


async def benchmark_layer(layer_fn, *args, iterations=10, **kwargs):
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await layer_fn(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return {
        "mean_ms": round(statistics.mean(times), 1),
        "median_ms": round(statistics.median(times), 1),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 1),
        "min_ms": round(min(times), 1),
        "max_ms": round(max(times), 1),
    }


async def main():
    from src.layers.faithfulness import verify_faithfulness
    from src.layers.citation_auditor import audit_citations

    context = "Python is a programming language created by Guido van Rossum in 1991."
    response = "Python was created by Guido van Rossum. It is widely used for web development."

    print("Benchmarking Faithfulness Layer...")
    faith_results = await benchmark_layer(verify_faithfulness, response, context, iterations=5)
    print(f"  Results: {faith_results}")

    print("\nBenchmarking Citation Auditor...")
    citation_response = "See https://python.org for details about https://docs.python.org/3/"
    cite_results = await benchmark_layer(audit_citations, citation_response, iterations=5)
    print(f"  Results: {cite_results}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
