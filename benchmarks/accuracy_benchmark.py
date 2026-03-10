"""Test against known hallucination datasets."""

import asyncio
import json
from pathlib import Path


async def run_accuracy_benchmark():
    from src.layers.pipeline import run_pipeline

    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures"

    results = {"correct": 0, "incorrect": 0, "total": 0, "details": []}

    for fixture_file in ["hallucinated_responses.json", "faithful_responses.json", "mixed_responses.json"]:
        filepath = fixtures_dir / fixture_file
        if not filepath.exists():
            continue

        with open(filepath) as f:
            test_cases = json.load(f)

        for case in test_cases:
            try:
                decision = await run_pipeline(
                    response_text=case["response"],
                    context=case.get("context"),
                    prompt=case.get("prompt"),
                )
                expected = case["expected_action"]
                actual = decision.action.value
                correct = actual == expected

                results["total"] += 1
                if correct:
                    results["correct"] += 1
                else:
                    results["incorrect"] += 1

                results["details"].append({
                    "fixture": fixture_file,
                    "expected": expected,
                    "actual": actual,
                    "correct": correct,
                    "composite_score": decision.composite_score,
                })
            except Exception as e:
                results["details"].append({
                    "fixture": fixture_file,
                    "error": str(e),
                })

    accuracy = results["correct"] / results["total"] if results["total"] > 0 else 0
    print(f"\nAccuracy: {accuracy:.1%} ({results['correct']}/{results['total']})")
    for detail in results["details"]:
        status = "PASS" if detail.get("correct") else "FAIL"
        print(f"  [{status}] {detail.get('fixture')}: expected={detail.get('expected')}, got={detail.get('actual')}")

    return results


if __name__ == "__main__":
    asyncio.run(run_accuracy_benchmark())
