# Aegis Architecture

## Overview

Aegis operates as a reverse proxy middleware between LLM-powered applications and end users. It intercepts LLM responses and runs them through a multi-layer verification pipeline.

## Request Flow

```
Client Request
    │
    ▼
┌─────────────┐
│ FastAPI App  │ ── POST /v1/verify or /v1/proxy
└──────┬──────┘
       │
       ▼
┌──────────────┐
│   Pipeline   │ ── Orchestrates all layers
└──────┬───────┘
       │
       ├──── Layer 1: Faithfulness Verifier (parallel)
       │         ├── Claim decomposition (LLM)
       │         ├── Embedding similarity check
       │         └── LLM judge verification
       │
       ├──── Layer 3: Citation Auditor (parallel)
       │         ├── URL extraction (regex)
       │         ├── HTTP HEAD verification
       │         └── Content similarity check
       │
       ▼
  [If faithfulness score ambiguous: 0.4-0.7]
       │
       ├──── Layer 2: Semantic Entropy (conditional)
       │         ├── Multi-provider response generation
       │         ├── Embedding + clustering
       │         └── Shannon entropy calculation
       │
       ▼
┌──────────────────┐
│ Decision Engine  │ ── Weighted composite score + domain thresholds
└──────┬───────────┘
       │
       ├── PASS: Return original response
       ├── WARN: Append disclaimer
       ├── BLOCK: Return fallback message
       └── ESCALATE: Flag for human review
       │
       ▼
┌──────────────┐
│   Storage    │ ── SQLite (evaluation log)
│   Analytics  │ ── Drift detection, Prometheus metrics
└──────────────┘
```

## Key Design Decisions

1. **Layers 1 & 3 run in parallel** — no dependency between faithfulness and citation checking
2. **Layer 2 is conditional** — only triggered when faithfulness score is ambiguous (0.4-0.7), saving cost and latency
3. **Embeddings run locally** — all-MiniLM-L6-v2 (~90MB) avoids external API calls for similarity
4. **Multi-provider LLM** — fan out to Gemini/Groq/OpenRouter for diversity in entropy detection
5. **SQLite over Postgres** — lightweight, zero-config, sufficient for single-instance deployments

## Performance Budget

- Fast path (Layer 1 + 4): target <500ms
- Full path (all layers): target <3s
- The embedding model loads once at startup (~200MB RAM)
- Async throughout — uvicorn + asyncio for concurrent request handling
