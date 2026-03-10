from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Action(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class VerifyRequest(BaseModel):
    response_text: str = Field(..., description="The LLM response to verify")
    context: Optional[str] = Field(None, description="Context/documents provided to the LLM")
    prompt: Optional[str] = Field(None, description="Original prompt sent to the LLM")
    domain: Optional[str] = Field(None, description="Domain for threshold config (general, medical, legal)")


class ProxyRequest(BaseModel):
    prompt: str = Field(..., description="Prompt to send to the LLM")
    provider: str = Field("gemini", description="LLM provider: gemini, groq, openrouter")
    model: Optional[str] = Field(None, description="Specific model to use")
    context: Optional[str] = Field(None, description="Context/documents for faithfulness checking")
    domain: Optional[str] = Field(None, description="Domain for threshold config")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, ge=1, le=8192)


class Claim(BaseModel):
    text: str
    claim_type: str  # factual, opinion, hedged
    verdict: Optional[str] = None  # SUPPORTED, CONTRADICTED, NOT_MENTIONED
    confidence: Optional[float] = None
    supporting_context: Optional[str] = None


class FaithfulnessResult(BaseModel):
    score: float
    total_claims: int
    supported_claims: int
    claims: list[Claim]
    unsupported_claims: list[Claim]


class EntropyResult(BaseModel):
    entropy: float
    num_clusters: int
    risk_level: str  # low, medium, high
    cluster_details: list[dict]


class CitationResult(BaseModel):
    total_citations: int
    valid: int
    invalid: int
    score: Optional[float] = None
    details: list[dict]


class Decision(BaseModel):
    action: Action
    composite_score: float
    explanation: str
    faithfulness: Optional[FaithfulnessResult] = None
    entropy: Optional[EntropyResult] = None
    citations: Optional[CitationResult] = None
    response_text: str
    modified_response: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"
