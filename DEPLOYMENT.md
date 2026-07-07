# 🚀 Production Deployment Guide

This document describes how to deploy the **AI Email Suggested Response System** to production using **Vercel** (for the Next.js frontend) and **Render** (for the FastAPI backend).

---

## 📋 Environment Variables Reference

| Variable | Description | Location | Example |
|---|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API Key | Backend | `AIzaSy...` |
| `DATABASE_URL` | SQLAlchemy Connection URL | Backend | `sqlite+aiosqlite:////data/emails.db` |
| `FAISS_INDEX_PATH` | Path to FAISS binary | Backend | `/data/faiss.index` |
| `LOG_LEVEL` | Logging level | Backend | `INFO` / `DEBUG` |
| `NEXT_PUBLIC_API_URL` | Address of deployed backend | Frontend | `https://api-email-response.onrender.com` |

---

## 🛠️ Deploying the Backend (Render)

1. **Sign in** to [Render](https://render.com).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository. Render will automatically parse `render.yaml`.
4. Configure variables in the dashboard:
   - Provide your `GEMINI_API_KEY`.
5. Render mounts a persistent SSD at `/opt/render/project/src/data` automatically to house your SQLite database and FAISS index files across backend redeploys.
6. The build command will automatically run `scripts/seed_db.py` to compile the FAISS index and populate standard database entries.

---

## 🎨 Deploying the Frontend (Vercel)

1. **Sign in** to [Vercel](https://vercel.com).
2. Click **Add New** -> **Project** and import your repository.
3. Select `frontend` as the **Root Directory**.
4. Configure the **Build Settings**:
   - Framework: `Next.js`
   - Build Command: `npm run build`
   - Output Directory: `.next`
5. Under **Environment Variables**, add:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://<your-render-backend-url>.onrender.com`
6. Click **Deploy**.

---

## 🔍 Troubleshooting & QA

### 1. CORS Errors (Blocked Request)
- **Problem**: Next.js frontend is blocked from contacting the backend.
- **Solution**: The backend automatically reads allowed origins. In Render, set the environment variable `ALLOWED_ORIGINS` to `["https://<your-vercel-domain>.vercel.app"]` and restart the backend.

### 2. SQLite Database is Locked / Wiped
- **Problem**: Database transactions fail, or previous emails disappear on reboot.
- **Solution**: Ensure your Render service has persistent storage defined in `render.yaml` and the database URL uses that absolute folder path. We enable SQLite **WAL (Write-Ahead Logging)** mode automatically to support concurrent reads and prevent writer locks.

### 3. Hugging Face Timeout on Start
- **Problem**: Cold starts take too long because sentence-transformers is fetching the embedding model.
- **Solution**: The `all-MiniLM-L6-v2` model is cached locally on disk. On persistent storage, this model downloads exactly once and then loads in under 300ms on reboot.
