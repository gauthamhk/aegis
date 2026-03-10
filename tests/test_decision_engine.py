from src.layers.decision_engine import make_decision
from src.proxy.request_models import (
    Action,
    CitationResult,
    Claim,
    EntropyResult,
    FaithfulnessResult,
)


def _make_faithfulness(score: float) -> FaithfulnessResult:
    return FaithfulnessResult(
        score=score,
        total_claims=10,
        supported_claims=int(score * 10),
        claims=[],
        unsupported_claims=[],
    )


def test_high_score_passes():
    decision = make_decision(
        faithfulness=_make_faithfulness(0.95),
        entropy=EntropyResult(entropy=0.1, num_clusters=1, risk_level="low", cluster_details=[]),
        response_text="test",
    )
    assert decision.action == Action.PASS
    assert decision.composite_score >= 0.7


def test_low_score_blocks():
    decision = make_decision(
        faithfulness=_make_faithfulness(0.1),
        entropy=EntropyResult(entropy=1.8, num_clusters=5, risk_level="high", cluster_details=[]),
        response_text="test",
    )
    assert decision.action == Action.BLOCK
    assert decision.modified_response is not None


def test_medium_score_warns():
    decision = make_decision(
        faithfulness=_make_faithfulness(0.6),
        entropy=EntropyResult(entropy=0.8, num_clusters=2, risk_level="medium", cluster_details=[]),
        response_text="test",
    )
    assert decision.action == Action.WARN
    assert "Warning" in (decision.modified_response or "")


def test_medical_domain_stricter():
    decision = make_decision(
        faithfulness=_make_faithfulness(0.75),
        entropy=EntropyResult(entropy=0.5, num_clusters=2, risk_level="medium", cluster_details=[]),
        response_text="test",
        domain="medical",
    )
    assert decision.action in (Action.WARN, Action.ESCALATE, Action.BLOCK)


def test_no_citations_excluded_from_scoring():
    decision = make_decision(
        faithfulness=_make_faithfulness(0.9),
        citations=CitationResult(total_citations=0, valid=0, invalid=0, score=None, details=[]),
        response_text="test",
    )
    assert decision.action == Action.PASS
