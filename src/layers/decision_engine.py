from src.proxy.request_models import (
    Action,
    CitationResult,
    Decision,
    EntropyResult,
    FaithfulnessResult,
)
from src.utils.config import get_domain_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

DISCLAIMER = (
    "\n\n---\n⚠️ **Aegis Warning**: This response contains potentially unsupported claims. "
    "Please verify the information independently before relying on it."
)

BLOCK_RESPONSE = (
    "This response has been blocked by Aegis due to a high likelihood of containing "
    "inaccurate or hallucinated information. Please rephrase your query or provide "
    "additional context for a more reliable response."
)


def _normalize_entropy(entropy: float, max_entropy: float = 2.0) -> float:
    return min(entropy / max_entropy, 1.0)


def make_decision(
    faithfulness: FaithfulnessResult | None = None,
    entropy: EntropyResult | None = None,
    citations: CitationResult | None = None,
    response_text: str = "",
    domain: str | None = None,
) -> Decision:
    config = get_domain_config(domain)
    weights = config.get("weights", {"faithfulness": 0.5, "entropy": 0.3, "citation": 0.2})
    w_f = weights.get("faithfulness", 0.5)
    w_e = weights.get("entropy", 0.3)
    w_c = weights.get("citation", 0.2)

    f_score = faithfulness.score if faithfulness else 0.5
    e_score = 1 - _normalize_entropy(entropy.entropy) if entropy else 0.5
    c_score = citations.score if citations and citations.score is not None else 0.5

    active_weights = w_f + w_e + w_c
    if citations is None or citations.score is None:
        active_weights = w_f + w_e
        composite = (w_f * f_score + w_e * e_score) / active_weights if active_weights else 0.5
    else:
        composite = (w_f * f_score + w_e * e_score + w_c * c_score) / active_weights if active_weights else 0.5

    composite = round(composite, 3)

    pass_threshold = config.get("pass_threshold", 0.7)
    warn_threshold = config.get("warn_threshold", 0.5)
    escalate_threshold = config.get("escalate_threshold", 0.3)
    action_on_uncertain = config.get("action_on_uncertain", "WARN")

    if composite >= pass_threshold:
        action = Action.PASS
    elif composite >= warn_threshold:
        action = Action.WARN
    elif action_on_uncertain == "ESCALATE" and composite >= escalate_threshold:
        action = Action.ESCALATE
    else:
        action = Action.BLOCK

    parts = []
    if faithfulness:
        parts.append(
            f"Faithfulness: {f_score:.2f} ({faithfulness.supported_claims}/{faithfulness.total_claims} claims supported)"
        )
        if faithfulness.unsupported_claims:
            unsupported = [c.text for c in faithfulness.unsupported_claims[:3]]
            parts.append(f"Unsupported claims: {unsupported}")
    if entropy:
        parts.append(f"Semantic entropy: {entropy.entropy:.2f} (risk: {entropy.risk_level})")
    if citations and citations.score is not None:
        parts.append(f"Citations: {citations.valid}/{citations.total_citations} valid")
    parts.append(f"Composite score: {composite}. Action: {action.value}")
    explanation = " | ".join(parts)

    modified_response = None
    if action == Action.WARN:
        modified_response = response_text + DISCLAIMER
    elif action == Action.BLOCK:
        modified_response = BLOCK_RESPONSE

    logger.info(
        "decision_engine.complete",
        action=action.value,
        composite=composite,
        faithfulness=f_score,
        entropy=e_score,
    )

    return Decision(
        action=action,
        composite_score=composite,
        explanation=explanation,
        faithfulness=faithfulness,
        entropy=entropy,
        citations=citations,
        response_text=response_text,
        modified_response=modified_response,
    )
