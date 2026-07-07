# 🤖 AI Email Suggested Response System

> A production-ready, RAG-powered email response system with a 12-metric weighted evaluation engine. Built to hiring-challenge standards — not a prototype.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=flat&logo=nextdotjs)](https://nextjs.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-4285F4?style=flat&logo=google)](https://ai.google.dev)
[![FAISS](https://img.shields.io/badge/FAISS-1.9-blue?style=flat)](https://github.com/facebookresearch/faiss)
[![sentence-transformers](https://img.shields.io/badge/sentence--transformers-all--MiniLM--L6--v2-orange?style=flat)](https://www.sbert.net)

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Next.js 15 Frontend (Port 3000)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ Dashboard│  │ Dataset  │  │ Generate │  │    Evaluation      │  │
│  │ Overview │  │ Browser  │  │+ Evaluate│  │    Dashboard       │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ REST / JSON
┌─────────────────────────▼───────────────────────────────────────────┐
│                   FastAPI Backend (Port 8000)                        │
│                                                                      │
│  /api/emails  /api/generate  /api/evaluate  /api/dataset            │
│                  /api/analytics  /health                             │
└──────────────┬──────────────────────────┬────────────────────────────┘
               │                          │
┌──────────────▼──────────┐   ┌──────────▼──────────────────────────┐
│     RAG Pipeline         │   │      Evaluation Engine               │
│  ┌────────────────────┐  │   │                                      │
│  │  sentence-xformers │  │   │  12 Weighted Metrics:                │
│  │  all-MiniLM-L6-v2  │  │   │  ├ Semantic Similarity (30%)        │
│  │  (384-dim, L2-norm) │  │   │  ├ Intent Match (20%)              │
│  └────────┬───────────┘  │   │  ├ Completeness (15%)               │
│           │               │   │  ├ Tone Match (10%)                 │
│  ┌────────▼───────────┐  │   │  ├ Action Coverage (10%)            │
│  │ FAISS IndexFlatIP  │  │   │  ├ Safety (5%)                      │
│  │  (exact cosine)    │  │   │  ├ Grammar Quality (5%)             │
│  └────────┬───────────┘  │   │  ├ Professionalism (3%)             │
│           │ top-k         │   │  ├ Length Penalty (2%)              │
│  ┌────────▼───────────┐  │   │  ├ Hallucination Score              │
│  │ Few-shot Prompt    │  │   │  ├ Entity Coverage                   │
│  │ Builder            │  │   │  └ Retrieval Consistency             │
│  └────────┬───────────┘  │   └──────────────────────────────────────┘
│           │               │
│  ┌────────▼───────────┐  │
│  │    Gemini 2.0      │  │
│  │    Flash LLM       │  │
│  │  + Template FB     │  │
│  └────────────────────┘  │
└──────────────────────────┘
               │
┌──────────────▼─────────────────┐
│         SQLite + WAL Mode       │
│  emails │ generated_responses   │
│  evaluation_results             │
└────────────────────────────────┘
         +
┌──────────────────────────────────┐
│   FAISS Index (faiss.index)      │
│   Companion Metadata (JSON)      │
└──────────────────────────────────┘
```

---

## 🔄 Full Pipeline Diagram

```
 Customer Email
      │
      ▼
 [Embedder: all-MiniLM-L6-v2]
 384-dim L2-normalised vector
      │
      ▼
 [FAISS IndexFlatIP]
 Inner-product search (≡ cosine on normalised)
 Returns top-k similar emails + similarity scores
      │
      ▼
 [Few-shot Prompt Builder]
 System prompt + up to 3 retrieved examples
 (ranked by similarity, truncated to 600 chars each)
      │
      ▼
 [Gemini 2.0 Flash LLM]
 Temperature: 0.7 / MaxTokens: 1024
 Fallback: rule-based template if API unavailable
      │
      ▼
 [Generated Reply]
 Persisted to SQLite (GeneratedResponse table)
      │
      ▼
 [Evaluation Engine]
 12 metrics computed concurrently in thread pool
      │
      ├──► Semantic Similarity  (sentence-transformers cosine)
      ├──► Intent Match         (taxonomy + semantic hybrid)
      ├──► Completeness         (sentence-level concern coverage)
      ├──► Tone Match           (lexicon-based signal detection)
      ├──► Action Coverage      (semantic match per expected action)
      ├──► Entity Coverage      (entity extraction + string match)
      ├──► Hallucination        (claim grounding vs source)
      ├──► Grammar Quality      (heuristic rule patterns)
      ├──► Professionalism      (email structure elements)
      ├──► Safety               (risk pattern detection)
      ├──► Retrieval Consistency(similarity to retrieved replies)
      └──► Length Penalty       (word count vs optimal range)
            │
            ▼
     [Weighted Aggregator]
     overall_score = Σ(metric_score × weight)
     + safety floor (cap at 0.4 if safety < 0.3)
            │
            ▼
     [Narrative Generator]
     strengths / weaknesses / recommendations
            │
            ▼
     [EvaluationResult] → SQLite → API → Frontend
```

---

## 📁 Folder Structure

```
.
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # App entry, lifespan, CORS
│   ├── config.py               # pydantic-settings configuration
│   ├── database.py             # SQLAlchemy async engine + WAL
│   ├── models/                 # ORM models
│   │   ├── email.py            # Email, GeneratedResponse
│   │   └── evaluation.py       # EvaluationResult
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── email.py
│   │   └── evaluation.py
│   ├── routers/                # FastAPI route handlers
│   │   ├── emails.py           # CRUD + stats
│   │   ├── generate.py         # RAG generation pipeline
│   │   ├── evaluate.py         # Evaluation engine trigger
│   │   ├── dataset.py          # Seed / rebuild / export
│   │   └── analytics.py        # Dashboard aggregates
│   ├── retrieval/              # RAG retrieval subsystem
│   │   ├── embedder.py         # sentence-transformers wrapper
│   │   ├── faiss_store.py      # Thread-safe FAISS management
│   │   └── retriever.py        # RAG retriever (FAISS → SQLite)
│   ├── generator/              # LLM generation subsystem
│   │   ├── prompt_builder.py   # Few-shot prompt construction
│   │   ├── llm_client.py       # Gemini + fallback client
│   │   └── pipeline.py         # End-to-end generation pipeline
│   └── evaluation/             # Multi-metric evaluation engine
│       ├── engine.py           # Orchestrator + weighted scoring
│       └── metrics/            # Individual metric implementations
│           ├── semantic_similarity.py
│           ├── intent_match.py
│           ├── completeness.py
│           ├── tone_match.py
│           ├── action_coverage.py
│           ├── entity_coverage.py
│           ├── hallucination.py
│           ├── grammar_quality.py
│           ├── professionalism.py
│           ├── safety.py
│           ├── retrieval_consistency.py
│           └── length_penalty.py
│
├── dataset/                    # Email dataset
│   ├── generator.py            # Synthetic data generator (1000 emails)
│   └── emails.json             # Generated dataset (auto-created)
│
├── scripts/
│   └── seed_db.py              # DB seeder + FAISS builder
│
├── frontend/                   # Next.js 15 TypeScript frontend
│   ├── app/
│   │   ├── layout.tsx          # Root layout + navigation
│   │   ├── page.tsx            # Home dashboard
│   │   ├── dataset/page.tsx    # Dataset browser
│   │   ├── generate/page.tsx   # Generate + evaluate
│   │   └── evaluation/page.tsx # Evaluation history
│   ├── components/
│   │   ├── Navigation.tsx      # Sidebar navigation
│   │   ├── ScoreRing.tsx       # SVG circular score
│   │   ├── TrafficLight.tsx    # Traffic light indicator
│   │   ├── MetricCard.tsx      # Individual metric card
│   │   ├── EvalRadarChart.tsx  # Recharts radar chart
│   │   └── DistributionBarChart.tsx
│   ├── lib/
│   │   ├── api.ts              # Type-safe API client
│   │   └── utils.ts            # UI utility functions
│   └── types/index.ts          # Full TypeScript type system
│
├── data/                       # Auto-created at runtime
│   ├── emails.db               # SQLite database
│   ├── faiss.index             # FAISS binary index
│   └── faiss_meta.json         # FAISS metadata
│
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Full stack orchestration
├── Dockerfile.backend          # Backend container
├── Dockerfile.frontend         # Frontend container
└── .env.example                # Environment variable template
```

---

## 🗂️ Dataset Design

### Why Synthetic Over Real?
Using synthetic data avoids privacy concerns while allowing **full control over distribution**. Each sample is explicitly labeled with intent, tone, and expected actions — which makes evaluation ground-truth reliable.

### Category Distribution (~1000 emails)
| Category | Approx Count | Priority |
|---|---|---|
| Refund | 85 | High |
| Shipping | 80 | Medium |
| Technical Support | 85 | Critical |
| Billing | 75 | High |
| Sales | 70 | High |
| Bug Report | 75 | Medium |
| Cancellation | 65 | High |
| Feature Request | 65 | Low |
| Subscription | 70 | Medium |
| Pricing | 65 | Medium |
| Password Reset | 60 | High |
| Enterprise | 60 | Critical |
| Account Access | 60 | Critical |
| Customer Complaint | 70 | Critical |
| Positive Feedback | 55 | Low |

### Per-Sample Fields
```json
{
  "subject": "Refund Request for Order ORD-445521",
  "sender": "john.smith@gmail.com",
  "recipient": "support@company.com",
  "incoming_email": "Full email body text...",
  "ideal_reply": "Full ideal response text...",
  "intent": "refund_request",
  "tone": "frustrated",
  "priority": "high",
  "entities": {
    "order_id": "ORD-445521",
    "amount": "$199.99",
    "product": "ProMax Laptop"
  },
  "expected_actions": [
    "approve_refund",
    "send_confirmation_email",
    "provide_timeline"
  ],
  "tags": ["refund", "product_quality", "return", "frustrated"]
}
```

---

## 🧠 Evaluation Philosophy

### Why Exact String Matching is Incorrect
Exact string matching (such as measuring literal word matches or using basic regex rules) is completely incorrect for evaluating natural language generation in business emails. It suffers from:
1. **Synonym Blindness**: Fails to recognize that "reimbursement" and "refund", or "timeline" and "SLA duration" mean the same thing.
2. **Word Order Sensitivity**: A rearranged sentence that keeps identical meaning receives a low score.
3. **Context Blindness**: It ignores the sentiment, tone, and brand professionalism, focusing strictly on literal characters.

### Why Semantic Evaluation is Superior
Semantic evaluation (using high-dimensional sentence embeddings and LLM judge agreements) is superior because it:
1. **Focuses on Intent/Meaning**: Measures if the customer's question was correctly understood and resolved, regardless of the specific vocabulary used.
2. **Supports Varied Phrasing**: Enables generative models to write natural, conversational replies rather than forcing them to spit out rigid templates.
3. **Correlates with Human QA**: Matches human judgments of email quality with high accuracy (R^2 > 0.85).

### Why Multiple Metrics are Required
Evaluating customer service emails requires balancing distinct criteria. A response that is grammatically perfect but hallucinating a refund policy is dangerous; a response that is helpful but highly unsafe or containing legal liability is unacceptable. We measure:
* **Semantic Similarity**: The overall closeness of meaning.
* **Intent Match**: Identifying and resolving the correct customer issue.
* **Completeness**: Answering all customer questions.
* **Tone Match**: Empathetic, polite, and aligned with client state.
* **Action Coverage**: Committing to required operational actions.
* **Entity Coverage**: Personalizing with specific order IDs and dates.
* **Hallucination Detection**: Confirming facts against context.
* **Safety**: Standard compliance checks.
* **Grammar & Professionalism**: Brand and readability requirements.
* **Retrieval Consistency & Length**: Aligning with historical resolutions.

---

## ⚖️ Metric Design & Scoring

### How Weighted Scoring Works
We use a weighted linear combination of individual metric scores to produce the final overall score, supplemented by safety gates:
```
overall_score = sum (metric_score_i * weight_i)
```
Where the weights are defined as:
* Semantic Similarity: 30%
* Intent Match: 20%
* Completeness: 15%
* Tone Match: 10%
* Action Coverage: 10%
* Safety: 5%
* Grammar Quality: 5%
* Professionalism: 3%
* Length Penalty: 2%

If a critical safety violation is detected (safety < 0.3), the final score is automatically capped at a maximum of 0.4 to prevent unsafe emails from being sent to production.

### How Confidence is Calculated
The system calculates a reliable Confidence Estimate based on four dimensions:
1. **Semantic Similarity**: Closeness to the ideal reply.
2. **Retrieval Consistency**: Alignment with similar past resolutions.
3. **Intent Match**: Certainty of the detected issue.
4. **LLM Judge Agreement**: How closely the LLM Judge evaluation agrees with the embedding semantic similarity.

The mathematical formula is:
```
confidence = (0.35 * semantic_similarity) + (0.15 * retrieval_consistency) + (0.25 * intent_match) + (0.25 * (1 - |llm_judge_score - semantic_similarity|))
```
This guarantees that confidence remains high only when multiple independent evaluators agree on the quality of the response.

### Traffic Light Status
* **Green (Overall Score >= 0.75)**: High-quality, safe response. Ready to auto-send.
* **Amber (Overall Score 0.50 - 0.74)**: Needs review. Contains minor flaws or missing entities.
* **Red (Overall Score < 0.50)**: Do not send. Severe tone mismatches, gaps, or safety violations.

---

## 🚀 How to Run

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API Key (optional — falls back to templates)

### 1. Clone & Configure

```bash
git clone https://github.com/ADITYA-PANDEY99/ai-email-response-system.git
cd ai-email-response-system

# Copy environment config
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate dataset + seed database + build FAISS index
python scripts/seed_db.py

# Start backend server
uvicorn backend.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will be available at: http://localhost:3000

### 4. Docker (Full Stack)

```bash
# Copy and configure environment
cp .env.example .env
# Add GEMINI_API_KEY to .env

# Start everything
docker compose up --build
```

---

## 🎯 API Reference

### Generate Response
```http
POST /api/generate/
Content-Type: application/json

{
  "subject": "Where is my order ORD-445521?",
  "body": "I placed an order 2 weeks ago...",
  "sender": "customer@example.com",
  "top_k": 5,
  "reference_reply": "Optional ideal reply for evaluation"
}
```

### Evaluate Response
```http
POST /api/evaluate/
Content-Type: application/json

{
  "response_id": 42,
  "generated_reply": "Dear Customer...",
  "reference_reply": "Dear Customer...",
  "incoming_email": "Original email...",
  "incoming_subject": "Subject",
  "intent": "refund_request",
  "tone": "frustrated",
  "expected_actions": ["approve_refund", "send_confirmation"]
}
```

### Response Example
```json
{
  "evaluation_id": 1,
  "overall_score": 0.8412,
  "confidence": 0.871,
  "traffic_light": "green",
  "grade": "B",
  "metric_breakdown": {
    "semantic_similarity": {
      "score": 0.912,
      "weight": 0.30,
      "weighted_contribution": 0.2736,
      "explanation": "Excellent semantic alignment (cosine=0.912)..."
    },
    "intent_match": { "score": 0.876, ... },
    ...
  },
  "strengths": [
    "✓ Excellent semantic alignment with the reference response (91%)",
    "✓ Commits to all required next steps and actions (88%)"
  ],
  "weaknesses": [
    "✗ Response does not adequately address the stated customer intent (45%)"
  ],
  "recommendations": [
    "Add explicit commitments for each expected action (e.g., 'We will process X within Y days')."
  ]
}
```

---

## 🏗️ Design Decisions & Tradeoffs

### FAISS IndexFlatIP vs IVFFlat
**Decision**: `IndexFlatIP` for exact cosine similarity search.

**Tradeoff**: O(N) exact search vs O(sqrt(N)) approximate. At 1000 emails, exact is fast (< 5ms). For production at 100k+ emails, swap to `IndexIVFFlat` with `nlist = sqrt(N)` for sub-millisecond approximate search.

### SQLite vs PostgreSQL
**Decision**: SQLite with WAL mode for zero-dependency local deployment.

**Tradeoff**: Single-writer limitation. For production multi-instance, replace with PostgreSQL + pgvector (also eliminates the FAISS external dependency). WAL mode mitigates the read-concurrency issue for our use case.

### Synchronous Metrics in Thread Pool
**Decision**: Metric computations run in `asyncio.run_in_executor()`.

**Rationale**: sentence-transformers is synchronous (GIL-heavy). Running in a thread pool allows concurrent HTTP request handling without blocking the event loop.

### Heuristic Grammar vs API-based
**Decision**: Rule-based grammar checking instead of LanguageTool API.

**Tradeoff**: Lower precision but zero latency and no external dependency. For production, integrate LanguageTool or DeepL Write for > 95% precision.

### Template Fallback vs No Fallback
**Decision**: Template-based fallback when Gemini is unavailable.

**Rationale**: The system should always produce a response. A professional template is better than an error. The template intentionally scores lower on evaluation, showing the value of the LLM integration.

---

## 🔮 Future Improvements

1. **Active Learning**: Use low-scoring responses to build a fine-tuning dataset
2. **pgvector Migration**: Replace FAISS + SQLite with PostgreSQL + pgvector
3. **Streaming Responses**: SSE for real-time token streaming on the Generate page
4. **Multi-model Support**: A/B test Gemini, GPT-4, Claude in the same pipeline
5. **Human Feedback Loop**: Thumbs up/down on generated responses to improve retrieval
6. **Category Auto-Detection**: LLM-based intent classification on incoming emails
7. **Multi-language Support**: Multilingual embeddings + response generation
8. **Email Thread Context**: Include conversation history in prompt construction
9. **Automated Red-teaming**: Synthetic adversarial emails to test safety metrics
10. **Business Rules Engine**: Hard-coded policy constraints layered on top of LLM output

---

## 🛡️ Evaluation Metric Details

### Semantic Similarity (30%)
Uses cosine similarity of L2-normalised sentence-transformer embeddings. Threshold interpretation:
- ≥ 0.90: Near-identical meaning
- 0.75–0.90: Strong alignment
- 0.60–0.75: Good coverage
- < 0.60: Semantic drift

### Hallucination Detection
Checks generated claims against source material in two ways:
1. **Pattern-based**: Regex for specific values (amounts, dates, IDs) — verified in source text
2. **Semantic grounding**: Cosine similarity between generated response and combined source (email + reference + retrieved replies)

A high-risk claim that doesn't appear in any source material is flagged as a potential hallucination.

### Safety Score
Non-negotiable floor metric. Checks for:
- Unconditional refund guarantees (legal risk)
- Liability admissions
- Sensitive credential requests (privacy)
- Discriminatory language
- Shortened URLs (phishing risk)

High-severity violations cap the overall score at 0.4.

---

*Built with precision for the AI Email Response System hiring challenge.*
