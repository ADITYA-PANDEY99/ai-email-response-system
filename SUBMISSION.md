# 🏆 Hiver Open AI Engineering Challenge Submission

This document serves as the official submission package for the **AI Email Suggested Response & Evaluation System**.

---

## 🌟 Project Links

- **GitHub Repository**: [https://github.com/ADITYA-PANDEY99/ai-email-response-system](https://github.com/ADITYA-PANDEY99/ai-email-response-system)
- **Frontend Dashboard (Vercel)**: [https://frontend-iota-henna-20.vercel.app](https://frontend-iota-henna-20.vercel.app)
- **Backend API (Render)**: [https://ai-email-backend-x4g2.onrender.com](https://ai-email-backend-x4g2.onrender.com)

---

## 🧠 Key Technical Innovations

### 1. True Explainable AI (XAI)
Every evaluation run grades the reply against 12 custom NLP metrics. Deductions are not hidden; the system generates exact diagnostic insights (`why_lost_points`) and remediation strategies (`how_to_improve`) shown in visual alert panels.

### 2. Dual-Engine LLM Judge
Blends embedding cosine similarity with a Gemini-powered audit. Gemini reviews the response for correctness, helpfulness, and style. The final rating combines lexical similarity with natural-language quality metrics.

### 3. Integrated Gap Analysis
The cockpit UI matches expected next-step actions and entity extractions between the reference and suggestion, outputting lists of missing elements and hallucinated ungrounded claims.

### 4. Build-Time Database Compilations
To deploy PyTorch and Sentence-Transformers on Render's 512MB RAM tier, the SQLite database and FAISS index are seeded at build time inside the Docker container, bypassing runtime memory overhead.

---

## 📈 System Architecture & Pipelines

### overall flow
1. **RAG Step**: COSINE vector search maps incoming subject + body against FAISS Index Flat IP to pull 5 historical pairs.
2. **LLM Generation**: Few-shot context built dynamically and passed to Gemini 2.0 Flash to synthesize response.
3. **Multi-Metric Evaluation**: Concurrently evaluates safety, tone matching, hallucination rules, and entity bounds.
4. **Final Scoring**: Grade (A+, A, B...) and traffic light status generated.

---

## ⚖️ Why This Design Beats BLEU / ROUGE
Traditional overlap metrics (like BLEU/ROUGE) grade word matches:
- Fails synonymy checks (e.g. "reimburse" vs "refund").
- Fails compliance checks (cannot check if incorrect dates are introduced).
- Fails safety (does not flag hostile or toxic statements if word-counts align).

Our system parses semantic intent, checks safety, runs regex claim checking, and scores alignment to ensure corporate compliance.
