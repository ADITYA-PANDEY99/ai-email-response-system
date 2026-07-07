"""
Run the complete end-to-end test to verify the system works.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def test_pipeline():
    print("=" * 60)
    print("AI Email Response System — End-to-End Test")
    print("=" * 60)

    # 1. Config
    from backend.config import get_settings
    s = get_settings()
    print(f"\n[OK] Config loaded | Gemini: {'configured' if s.has_gemini_key else 'fallback'}")

    # 2. Dataset
    dataset_path = Path(s.dataset_path)
    if not dataset_path.exists():
        from dataset.generator import main
        main()
    with dataset_path.open() as f:
        data = json.load(f)
    print(f"[OK] Dataset: {len(data)} emails across {len(set(d['category'] for d in data))} categories")

    # 3. DB
    from backend.database import init_db
    await init_db()
    print("[OK] Database initialized")

    # 4. Embedder
    from backend.retrieval.embedder import get_embedder
    emb = get_embedder()
    vec = emb.embed_text("Test email about refund")
    print(f"[OK] Embedder: {vec.shape[0]}-dim vector produced")

    # 5. FAISS
    from backend.retrieval.faiss_store import get_faiss_store
    store = get_faiss_store()
    print(f"[OK] FAISS store: {store.size} vectors")

    # 6. LLM (test fallback)
    from backend.generator.llm_client import TemplateFallbackClient
    fb = TemplateFallbackClient()
    r = await fb.generate("", "I need a refund for my order")
    print(f"[OK] Fallback LLM: {len(r.text)} char response")

    # 7. Evaluation metrics
    from backend.evaluation.metrics import semantic_similarity, safety
    test_text = "Dear Customer, thank you for reaching out. We will process your refund."
    ref_text = "Dear Customer, we appreciate your patience. Your refund will be processed."
    sim = semantic_similarity.compute(test_text, ref_text)
    safe = safety.compute(test_text)
    print(f"[OK] Eval metrics: sim={sim.score:.3f}, safety={safe.score:.3f}")

    print("\n[SUCCESS] All core systems operational!")
    print("\nNext steps:")
    print("  1. Add your GEMINI_API_KEY to .env")
    print("  2. Run: python scripts/seed_db.py")
    print("  3. Run: uvicorn backend.main:app --reload")
    print("  4. In another terminal: cd frontend && npm run dev")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
