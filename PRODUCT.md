# Aegis — The Truth Layer for AI

**Stop AI hallucinations before they reach your users.**

---

## What is Aegis?

### The Simple Version

AI chatbots sometimes make things up. They'll state false information with complete confidence — inventing statistics, citing papers that don't exist, or giving medical advice based on nothing. This is called **hallucination**, and it's the #1 reason enterprises don't trust AI.

**Aegis is a filter that sits between your AI and your users.** Every AI response passes through Aegis before delivery. If the response contains made-up information, Aegis catches it — and either warns the user, blocks the response entirely, or escalates it for human review.

Think of it like a spell-checker, but instead of catching typos, it catches lies.

### The Technical Version

Aegis is a self-hosted FastAPI reverse proxy that intercepts LLM responses and runs them through a **5-layer statistical verification pipeline** in real-time. It decomposes responses into atomic claims, verifies each against source documents using embedding similarity and LLM-as-judge, measures response consistency via semantic entropy, validates cited URLs, and produces a composite trust score with domain-configurable action thresholds (PASS / WARN / BLOCK / ESCALATE).

Latency overhead: **<500ms** for the fast path (faithfulness + decision only), **<3s** for the full pipeline including entropy sampling.

---

## Why Does This Matter?

### The $250M Problem

Hallucination-related incidents cost enterprises over **$250 million annually** — from incorrect customer support answers that create liability, to fabricated legal citations that get lawyers sanctioned, to medical chatbots recommending dangerous drug interactions.

The fundamental issue: **LLMs deliver false information with the same confidence as accurate information.** There is no built-in "I'm not sure" signal. Every response sounds equally authoritative.

### Who Gets Hurt

| Scenario | What Happens | Real-World Impact |
|----------|-------------|-------------------|
| Customer support bot | Invents a refund policy that doesn't exist | Company legally bound to honor the fabricated policy |
| Medical chatbot | Recommends a drug interaction that's actually dangerous | Patient harm, regulatory action |
| Legal research tool | Cites case law that doesn't exist | Lawyer sanctioned by court (this has happened multiple times) |
| Financial advisor bot | Fabricates historical returns or regulatory requirements | Compliance violations, fines |
| Education platform | Teaches incorrect scientific facts with full confidence | Students learn misinformation |

### Why Prompt Engineering Isn't Enough

You might think: "I'll just tell the AI not to hallucinate." Teams have tried every variation of:
- *"Only respond based on the provided documents"*
- *"Say 'I don't know' if you're unsure"*
- *"Never make up information"*

**It doesn't work reliably.** Hallucination is a fundamental property of how language models generate text — it's not a bug that can be prompted away. The model doesn't *know* when it's hallucinating. You need an external verification system. That's Aegis.

---

## How Aegis Works

### The 5-Layer Pipeline

Every response passes through up to 5 verification layers before reaching the end user:

```
User Question → Your LLM → Aegis Pipeline → Verified Response → User
```

#### Layer 1: Faithfulness Verifier
**What it does:** Breaks the LLM response into individual factual claims and checks each one against the source documents you provided.

**How:** Each claim is embedded using a local sentence-transformer model and compared against document chunks via cosine similarity. Claims that don't pass the similarity threshold are escalated to an LLM judge for a second opinion.

**Output:** A faithfulness score (0.0 to 1.0) — the fraction of claims that are supported by the provided context. A score of 0.8 means 80% of factual claims were verified.

#### Layer 2: Semantic Entropy Detector
**What it does:** Asks the same question multiple times across different LLM providers and measures how consistent the answers are.

**Why:** If an LLM is confident about the truth, different models and temperatures will give similar answers. If it's hallucinating, responses will scatter — each model makes up something different.

**How:** Generates 5 responses from Gemini, Groq, and OpenRouter. Embeds all responses, clusters them using agglomerative clustering, and calculates Shannon entropy across clusters. High entropy = high hallucination risk.

**Smart trigger:** This layer only runs when the faithfulness score falls in an uncertain range (0.4–0.7 by default). Clear passes and clear failures skip this step, keeping latency low.

#### Layer 3: Citation Auditor
**What it does:** Finds every URL, reference, and citation in the response and checks whether they're real.

**How:** Extracts URLs via regex, performs HTTP HEAD requests to verify they resolve, then optionally fetches page content and compares it to the claims being cited. Also detects named references ("according to Dr. Smith...") for logging.

**Output:** A citation validity score and a list of confirmed/broken/hallucinated URLs.

#### Layer 4: Decision Engine
**What it does:** Combines scores from all layers into a single composite score and maps it to an action.

**How:** Weighted average (default: faithfulness 50%, entropy 30%, citations 20%) compared against domain-specific thresholds:

| Action | Meaning | Default Threshold |
|--------|---------|-------------------|
| **PASS** | Response is trustworthy, deliver as-is | Score >= 0.7 |
| **WARN** | Potentially unreliable, append a disclaimer | Score 0.5–0.7 |
| **BLOCK** | High hallucination risk, replace with safe fallback | Score < 0.3 |
| **ESCALATE** | Uncertain in a high-stakes domain, route to human | Score 0.3–0.5 (medical/legal) |

#### Layer 5: Analytics & Drift Detection
**What it does:** Tracks hallucination trends over time and alerts when the LLM's accuracy is drifting — before it becomes a crisis.

**How:** Applies Grubbs' Test (statistical outlier detection) and rolling z-scores to composite score time series. Detects when recent scores are statistically different from the historical baseline.

**Why it matters:** LLM providers silently update models. A model that was 95% faithful last month might drop to 80% after a provider update. Aegis catches this drift automatically.

---

## Who Should Use Aegis?

### By Role

| Role | Why Aegis Matters |
|------|-------------------|
| **CTO / VP Engineering** | Ship AI features with confidence. Aegis is a safety net that lets you move fast without risking your brand. |
| **AI/ML Engineer** | Drop-in middleware — no changes to your existing LLM pipeline. Just point your app at Aegis instead of directly at the LLM. |
| **Compliance Officer** | Auditable verification logs for every AI response. Domain-specific thresholds for medical and legal use cases. |
| **Product Manager** | Quantifiable trust metrics. Dashboard shows exactly how reliable your AI is, with trends over time. |
| **DevOps / Platform** | Docker-compose deployment. Prometheus + Grafana monitoring out of the box. Self-hosted — your data never leaves your infrastructure. |

### By Industry

| Industry | Configuration | Key Benefit |
|----------|--------------|-------------|
| **Healthcare** | Medical domain (0.9 faithfulness threshold, ESCALATE on uncertain) | Prevents dangerous medical misinformation |
| **Legal** | Legal domain (0.85 threshold, citations required) | Catches fabricated case law and statutes |
| **Finance** | General domain with custom thresholds | Compliance-grade audit trail |
| **Customer Support** | General domain, WARN mode | Reduces incorrect answers without blocking the flow |
| **Education** | General domain | Flags unverified claims before students see them |

### By Company Size

| Size | Use Case |
|------|----------|
| **Startup** | You're building an AI product and need to ship trust, not just features. Aegis lets a 5-person team deliver enterprise-grade reliability. |
| **Mid-Market** | You're deploying AI across departments. Aegis gives you a centralized quality gate with per-domain policies. |
| **Enterprise** | You need compliance, auditability, and self-hosting. Aegis checks every box without a SaaS dependency. |

---

## How to Use Aegis

### Quick Start (5 Minutes)

```bash
# 1. Clone and configure
git clone https://github.com/gauthamhk/aegis.git
cd aegis
cp .env.example .env
# Add your API keys to .env (at least one of: GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY)

# 2. Run with Docker
docker-compose up -d

# 3. Verify it's running
curl http://localhost:8000/health
# → {"status": "healthy", "version": "0.1.0"}
```

### Option A: Verify Mode (You Call the LLM, Aegis Checks the Response)

Your app calls the LLM as usual, then sends the response to Aegis for verification before showing it to the user.

```bash
curl -X POST http://localhost:8000/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "response_text": "Python was created by Guido van Rossum in 1991.",
    "context": "Python is a programming language first released in 1991 by Guido van Rossum.",
    "prompt": "Who created Python?",
    "domain": "general"
  }'
```

**Response:**
```json
{
  "action": "PASS",
  "composite_score": 0.95,
  "explanation": "Faithfulness: 1.00 (2/2 claims supported) | Composite score: 0.95. Action: PASS",
  "response_text": "Python was created by Guido van Rossum in 1991.",
  "modified_response": null
}
```

The `action` field tells your app what to do:
- `PASS` → show the response as-is
- `WARN` → show it with the disclaimer in `modified_response`
- `BLOCK` → show the safe fallback in `modified_response` instead
- `ESCALATE` → route to a human reviewer

### Option B: Proxy Mode (Aegis Calls the LLM + Verifies)

Aegis handles the entire flow — calls the LLM, verifies the response, and returns the result.

```bash
curl -X POST http://localhost:8000/v1/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "provider": "gemini",
    "context": "Your reference documents here...",
    "domain": "general"
  }'
```

### Integration Patterns

**Python (requests):**
```python
import requests

def ask_ai(question, context, domain="general"):
    # Your existing LLM call
    llm_response = your_llm.generate(question)

    # Verify through Aegis
    result = requests.post("http://localhost:8000/v1/verify", json={
        "response_text": llm_response,
        "context": context,
        "prompt": question,
        "domain": domain,
    }).json()

    if result["action"] == "BLOCK":
        return result["modified_response"]  # Safe fallback
    elif result["action"] == "WARN":
        return result["modified_response"]  # Response + disclaimer
    else:
        return result["response_text"]      # Original response
```

**JavaScript (fetch):**
```javascript
async function verifiedAsk(question, context) {
  const llmResponse = await yourLLM.generate(question);

  const result = await fetch('http://localhost:8000/v1/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      response_text: llmResponse,
      context: context,
      prompt: question,
    }),
  }).then(r => r.json());

  return result.action === 'PASS'
    ? result.response_text
    : result.modified_response;
}
```

### Monitoring

```bash
# Live dashboard
open http://localhost:8000/dashboard

# Prometheus metrics
curl http://localhost:8000/v1/metrics

# Analytics summary (24h / 7d / 30d)
curl http://localhost:8000/v1/analytics/summary

# Recent drift events
curl http://localhost:8000/v1/analytics/drift

# Full report
curl http://localhost:8000/v1/analytics/report

# Grafana dashboards
open http://localhost:3000  # admin / aegis
```

### Domain Configuration

Create custom domain configs by adding YAML files to `config/domains/`:

```yaml
# config/domains/finance.yaml
domain: finance
faithfulness_threshold: 0.85
entropy_threshold: 0.4
citation_required: true
pass_threshold: 0.8
warn_threshold: 0.6
escalate_threshold: 0.4
action_on_uncertain: ESCALATE
weights:
  faithfulness: 0.55
  entropy: 0.25
  citation: 0.2
```

Then use it in requests: `"domain": "finance"`.

---

## What Makes Aegis Different

### vs. Guardrails / NeMo Guardrails
Guardrails focus on **input filtering** (blocking bad prompts). Aegis focuses on **output verification** (catching bad responses). They're complementary — use Guardrails to filter inputs, Aegis to verify outputs.

### vs. Galileo / Patronus AI
| | Aegis | Galileo | Patronus |
|---|---|---|---|
| **Deployment** | Self-hosted, your infra | SaaS only | SaaS only |
| **Cost** | Free (open source) | Enterprise pricing | Enterprise pricing |
| **Data privacy** | Your data never leaves your servers | Data sent to third party | Data sent to third party |
| **Latency** | <500ms fast path | Near real-time | Batch processing |
| **Customization** | Full source access, YAML configs | Dashboard configs | Dashboard configs |
| **Statistical methods** | Open (Grubbs' Test, Shannon entropy) | Proprietary black box | Proprietary black box |

### vs. "Just Use GPT-4 to Check"
Using another LLM to verify the first LLM's output sounds logical, but:
1. **LLMs can't reliably detect their own hallucinations** — they have the same blind spots
2. **No statistical rigor** — you get a yes/no opinion, not a calibrated probability
3. **No drift detection** — you won't know when accuracy degrades over time
4. **No audit trail** — no structured logs, no metrics, no dashboards

Aegis combines LLM judgment with embedding similarity, statistical tests, and URL verification for a multi-signal approach that's far more robust than any single check.

---

## Architecture & Performance

```
┌─────────────┐     ┌──────────────────────────────────────────────────────┐
│  Your App   │────▸│                    Aegis Proxy                       │
└─────────────┘     │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
                    │  │Faithfulness │  │  Citation    │  │  Semantic  │  │
                    │  │  Verifier   │  │   Auditor    │  │  Entropy   │  │
                    │  │  (Layer 1)  │  │  (Layer 3)   │  │ (Layer 2)  │  │
                    │  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  │
                    │         └────────┬───────┘               │         │
                    │           ┌──────▾──────┐                │         │
                    │           │  Decision   │◂───────────────┘         │
                    │           │  Engine (4) │                          │
                    │           └──────┬──────┘                          │
                    │           ┌──────▾──────┐                          │
                    │           │ Analytics & │                          │
                    │           │  Drift (5)  │                          │
                    │           └──────┬──────┘                          │
                    └──────────────────┼──────────────────────────────────┘
                                       │
                              Verified Response
```

### Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Fast path latency | <500ms | Layers 1 + 4 only (when faithfulness is clearly high or low) |
| Full path latency | <3s | All 5 layers including entropy sampling |
| Memory footprint | ~1.5GB | Embedding model (~200MB) + Python runtime |
| Concurrency | 50+ simultaneous | Configurable via `MAX_CONCURRENT_VERIFICATIONS` |
| Storage | SQLite (zero config) | Every evaluation logged with full layer details |
| Cache | Redis (optional) | Repeated identical checks served from cache |

### Tech Stack

- **Runtime:** Python 3.11+, FastAPI, uvicorn
- **Verification:** sentence-transformers (all-MiniLM-L6-v2, runs locally)
- **LLM Providers:** Google Gemini, Groq, OpenRouter (all have free tiers)
- **Database:** SQLite with WAL mode (zero configuration)
- **Cache:** Redis (optional, graceful degradation if unavailable)
- **Monitoring:** Prometheus + Grafana (included in docker-compose)
- **Statistics:** NumPy, SciPy (Grubbs' Test, Shannon entropy, agglomerative clustering)

---

## Security & Privacy

- **Self-hosted:** Your data never leaves your infrastructure. No telemetry, no external calls except to the LLM providers you configure.
- **PII redaction:** Aegis automatically strips emails, phone numbers, SSNs, and credit card numbers from stored evaluation logs. Configurable via `PII_REDACTION_ENABLED`.
- **No data retention required:** The verification pipeline works in real-time. Database logging is for analytics — disable it if you don't need it.
- **API keys stay local:** All provider keys are read from environment variables, never logged or transmitted.

---

## Getting Started Checklist

- [ ] Clone the repository
- [ ] Copy `.env.example` to `.env` and add at least one LLM API key
- [ ] Run `docker-compose up -d`
- [ ] Hit `http://localhost:8000/health` to confirm it's running
- [ ] Send your first `/v1/verify` request
- [ ] Open `http://localhost:8000/dashboard` to see real-time stats
- [ ] Configure domain thresholds for your use case
- [ ] Point your application at Aegis and deploy

---

*Built by [Gautham Yerramareddy](https://ultrathink.in) — because AI should be trustworthy, not just capable.*

*Licensed under MIT. Free to use, modify, and deploy.*
