# API Reference

## Endpoints

### POST /v1/verify
Verify an LLM response for hallucinations.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| response_text | string | Yes | The LLM response to verify |
| context | string | No | Context/documents provided to the LLM |
| prompt | string | No | Original prompt (enables entropy detection) |
| domain | string | No | Domain config: general, medical, legal |

**Response:** `Decision` object (see below)

### POST /v1/proxy
Proxy mode — Aegis calls the LLM, verifies the response, and returns the result.

**Request Body:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| prompt | string | Yes | | Prompt to send to LLM |
| provider | string | No | gemini | LLM provider: gemini, groq, openrouter |
| model | string | No | auto | Specific model to use |
| context | string | No | | Context for faithfulness checking |
| domain | string | No | general | Domain config |
| temperature | float | No | 0.7 | Generation temperature |
| max_tokens | int | No | 1024 | Max tokens to generate |

### GET /v1/metrics
Prometheus-format metrics.

### GET /v1/analytics/summary
Hallucination rate summary for 24h, 7d, 30d windows.

### GET /v1/analytics/drift
Recent drift detection events.

### GET /v1/analytics/report
Full quality report.

### GET /v1/dashboard/stats
Real-time stats for dashboard UI.

### WS /v1/dashboard/live
WebSocket feed for live dashboard updates (sends stats every 5s).

### GET /health
Health check.

### GET /ready
Readiness check.

## Decision Object

```json
{
  "action": "PASS | WARN | BLOCK | ESCALATE",
  "composite_score": 0.85,
  "explanation": "Human-readable explanation",
  "faithfulness": {
    "score": 0.9,
    "total_claims": 5,
    "supported_claims": 4,
    "claims": [],
    "unsupported_claims": []
  },
  "entropy": {
    "entropy": 0.3,
    "num_clusters": 1,
    "risk_level": "low",
    "cluster_details": []
  },
  "citations": {
    "total_citations": 2,
    "valid": 2,
    "invalid": 0,
    "score": 1.0,
    "details": []
  },
  "response_text": "Original response",
  "modified_response": "Modified response (if WARN/BLOCK)"
}
```
