"use client";

import { useState } from "react";
import {
  ArrowRight,
  Database,
  Eye,
  FileText,
  Gavel,
  Mail,
  Scale,
  Sparkles,
} from "lucide-react";

interface StepDetails {
  title: string;
  desc: string;
  icon: React.ElementType;
  color: string;
  mathExplanation: string;
}

const FLOW_STEPS: StepDetails[] = [
  {
    title: "1. Incoming Email",
    desc: "The pipeline triggers when a new customer email is received. The text is parsed to extract subject, body, and customer identity.",
    icon: Mail,
    color: "from-blue-500 to-indigo-500 text-blue-400 border-blue-500/20 bg-blue-500/5",
    mathExplanation: "Inputs: Subject + Body text, Sender email address.",
  },
  {
    title: "2. RAG Retrieval",
    desc: "A sentence-transformers model (all-MiniLM-L6-v2) embeds the incoming email into a 384-dimensional vector. FAISS performs an exact IndexFlatIP inner-product search (cosine similarity) to retrieve the top 5 most similar historical emails.",
    icon: Database,
    color: "from-violet-500 to-fuchsia-500 text-violet-400 border-violet-500/20 bg-violet-500/5",
    mathExplanation: "Sim(q, d) = cos(theta) = (q · d) / (||q|| ||d||) using L2 normalisation.",
  },
  {
    title: "3. LLM Generation",
    desc: "The prompt builder embeds the retrieved email/reply pairs as few-shot prompt contexts. Gemini 2.0 Flash synthesizes the suggested email reply under a 1024 token limit. Reverts to safe rules if the LLM is overloaded.",
    icon: Sparkles,
    color: "from-fuchsia-500 to-pink-500 text-fuchsia-400 border-fuchsia-500/20 bg-fuchsia-500/5",
    mathExplanation: "Prompt = [Few-shot examples] + [New Context] -> temperature=0.7",
  },
  {
    title: "4. Multi-Metric Evaluation",
    desc: "The evaluation engine computes 12 weighted NLP and heuristic metrics concurrently in a thread pool (completeness, tone matching, safety check, grammar quality, etc.).",
    icon: Scale,
    color: "from-emerald-500 to-teal-500 text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    mathExplanation: "Weights: Semantic Similarity (30%), Intent Match (20%), Completeness (15%), Tone (10%), Actions (10%), Safety (5%), Grammar (5%), Professionalism (3%), Length (2%).",
  },
  {
    title: "5. LLM Judge Alignment",
    desc: "Gemini is invoked a second time as a quality control auditor. It compares the generated email against the ideal reference on Correctness and Helpfulness. The result is combined with the embedding semantic similarity.",
    icon: Gavel,
    color: "from-amber-500 to-orange-500 text-amber-400 border-amber-500/20 bg-amber-500/5",
    mathExplanation: "Final Semantic score = 0.5 * embedding_similarity + 0.3 * judge_correctness + 0.2 * judge_helpfulness.",
  },
  {
    title: "6. Final Aggregation",
    desc: "Calculates the overall weighted score and assigns a letter grade (A+, A, B...). Computes confidence based on agreement. Triggers traffic light signals (Green, Amber, Red).",
    icon: Eye,
    color: "from-rose-500 to-red-500 text-rose-400 border-rose-500/20 bg-rose-500/5",
    mathExplanation: "Confidence = (0.35 * similarity) + (0.15 * consistency) + (0.25 * intent) + (0.25 * judge_agreement). If Safety < 0.3, overall score is capped at 0.4.",
  },
];

export function ExplainabilityFlow() {
  const [activeStep, setActiveStep] = useState<number>(0);

  const current = FLOW_STEPS[activeStep];
  const Icon = current.icon;

  return (
    <div className="glass rounded-2xl p-5 border border-white/5 space-y-4">
      <h3 className="text-sm font-semibold text-zinc-200">⛓️ System Explainability Pipeline Flow</h3>
      <p className="text-[11px] text-zinc-500">
        Click any pipeline node to inspect technical execution details, algorithms, and mathematical models.
      </p>

      {/* Pipeline Row */}
      <div className="flex items-center justify-between gap-1 p-2 bg-zinc-950/40 rounded-xl border border-white/5 overflow-x-auto">
        {FLOW_STEPS.map((step, idx) => {
          const StepIcon = step.icon;
          const isActive = idx === activeStep;
          return (
            <div key={idx} className="flex items-center shrink-0">
              <button
                onClick={() => setActiveStep(idx)}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-lg border text-center transition-all min-w-[100px] cursor-pointer ${
                  isActive
                    ? "bg-violet-500/15 border-violet-500/40 text-violet-300 shadow-md shadow-violet-500/5"
                    : "bg-transparent border-transparent text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <StepIcon className={`w-5 h-5 ${isActive ? "text-violet-400" : "text-zinc-500"}`} />
                <span className="text-[9px] font-bold tracking-wider uppercase">
                  {step.title.split(". ")[1]}
                </span>
              </button>
              {idx < FLOW_STEPS.length - 1 && (
                <ArrowRight className="w-3.5 h-3.5 text-zinc-700 mx-1.5 shrink-0" />
              )}
            </div>
          );
        })}
      </div>

      {/* Explanatory detail card */}
      <div className={`rounded-xl border p-4 bg-gradient-to-br ${current.color} transition-all duration-300 animate-fade-in`}>
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-white/5 border border-white/10 shrink-0">
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-white leading-tight">{current.title}</h4>
            <p className="text-xs text-zinc-300 leading-relaxed">{current.desc}</p>
            <div className="mt-3 bg-zinc-950/40 rounded-lg p-2.5 border border-white/5">
              <span className="text-[9px] uppercase tracking-wider text-zinc-500 font-semibold block mb-0.5">
                Technical Mechanism & Math Formulation:
              </span>
              <code className="text-[10px] text-violet-300 font-mono">{current.mathExplanation}</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
