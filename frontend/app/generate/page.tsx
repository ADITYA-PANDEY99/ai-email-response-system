"use client";

import { useState } from "react";
import {
  AlertCircle,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Clock,
  Loader2,
  Send,
  Sparkles,
  Zap,
} from "lucide-react";
import { evaluateApi, generateApi } from "@/lib/api";
import type { EvaluationResponse, GenerateResponse } from "@/types";
import { MetricCard } from "@/components/MetricCard";
import { ScoreRing } from "@/components/ScoreRing";
import { TrafficLight } from "@/components/TrafficLight";
import { EvalRadarChart } from "@/components/EvalRadarChart";
import { formatMs, formatScore, gradeColor } from "@/lib/utils";
import { EmailDiff } from "@/components/EmailDiff";
import { ExplainabilityFlow } from "@/components/ExplainabilityFlow";

const EXAMPLE_EMAILS = [
  {
    subject: "Order Still Not Arrived - ORD-445521",
    body: `Hi,

I placed order ORD-445521 two weeks ago for a ProMax Laptop worth $999.99 and it still hasn't arrived. The estimated delivery was last Friday.

I've been waiting patiently but this is getting really concerning. Can you please provide tracking information and let me know what's happening?

Thanks,
Sarah Johnson`,
    reference: `Dear Sarah,

Thank you for reaching out about your order ORD-445521. I completely understand how concerning this must be, especially when waiting for a significant purchase.

I've looked into your order and I can see that your ProMax Laptop was dispatched on June 28th. Here are your shipment details:
- Tracking Number: TRK9847263641
- Carrier: FedEx
- Current Status: In transit, delayed due to weather conditions

I sincerely apologize for the delay. Our logistics team is monitoring your shipment closely. You can expect delivery within the next 2 business days.

As a goodwill gesture for this inconvenience, I've applied a $50 credit to your account. If your order doesn't arrive by Friday, please contact us immediately and we'll arrange a replacement.

Best regards,
Customer Support Team`,
    intent: "shipping_inquiry",
    tone: "concerned",
    expected_actions: ["provide_tracking_info", "give_delivery_estimate", "offer_compensation"],
    entities: { order_id: "ORD-445521", amount: "$999.99", product: "ProMax Laptop" },
  },
  {
    subject: "Unexpected Charge on My Account",
    body: `Dear Billing Team,

I noticed a charge of $149.99 on my credit card dated July 1st that I didn't authorize. My account email is john.doe@example.com.

I've never signed up for this service and am requesting an immediate investigation and refund.

Regards,
John Doe`,
    reference: `Dear John,

Thank you for bringing this unauthorized charge to our attention. I completely understand your concern, and I want to assure you this is our top priority.

I have immediately placed a hold on the charge of $149.99 and opened an investigation (Case ID: CASE-88421).

Our billing team will review this within 24 hours. If confirmed as unauthorized, we will:
1. Issue a full refund of $149.99 within 3-5 business days
2. Secure your account
3. Send a written explanation

You will receive an update by email tomorrow morning. I sincerely apologize for this experience.

Sincerely,
Billing Security Team`,
    intent: "billing_dispute",
    tone: "concerned",
    expected_actions: ["investigate_charge", "place_hold", "provide_timeline"],
    entities: { amount: "$149.99", date: "July 1st" },
  },
];

export default function GeneratePage() {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sender, setSender] = useState("customer@example.com");
  const [reference, setReference] = useState("");
  const [topK, setTopK] = useState(5);

  const [generating, setGenerating] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [genResult, setGenResult] = useState<GenerateResponse | null>(null);
  const [evalResult, setEvalResult] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRetrieved, setShowRetrieved] = useState(false);

  const loadExample = (ex: typeof EXAMPLE_EMAILS[0]) => {
    setSubject(ex.subject);
    setBody(ex.body);
    setReference(ex.reference);
  };

  const handleGenerate = async () => {
    if (!subject.trim() || !body.trim()) return;
    setGenerating(true);
    setError(null);
    setGenResult(null);
    setEvalResult(null);
    try {
      const result = await generateApi.generate({
        subject,
        body,
        sender,
        top_k: topK,
        reference_reply: reference || undefined,
      });
      setGenResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleEvaluate = async () => {
    if (!genResult) return;
    setEvaluating(true);
    setError(null);
    try {
      const result = await evaluateApi.evaluate({
        response_id: genResult.response_id,
        generated_reply: genResult.generated_reply,
        reference_reply: reference || undefined,
        incoming_email: body,
        incoming_subject: subject,
        retrieval_ids: genResult.retrieved_emails.map((r) => r.id),
      });
      setEvalResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  };

  const radarData = evalResult
    ? Object.entries(evalResult.metric_breakdown).map(([key, val]) => ({
        metric: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        score: (val as { score: number }).score,
      }))
    : [];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Zap className="w-6 h-6 text-violet-400" />
          Generate Response
        </h1>
        <p className="text-zinc-400 text-sm mt-1">
          Enter an email to generate an AI response using RAG + Gemini
        </p>
      </div>

      {/* Examples */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-zinc-500">Try an example:</span>
        {EXAMPLE_EMAILS.map((ex, i) => (
          <button
            key={i}
            onClick={() => loadExample(ex)}
            className="text-xs px-3 py-1.5 bg-zinc-900 border border-white/10 rounded-xl text-zinc-300 hover:border-violet-500/40 hover:text-violet-300 transition-all"
          >
            {ex.subject.substring(0, 30)}…
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Input panel */}
        <div className="space-y-4">
          <div className="glass rounded-2xl p-5 border border-white/5 space-y-4">
            <h2 className="text-sm font-semibold text-zinc-200">Incoming Email</h2>

            <div>
              <label className="text-xs text-zinc-500 mb-1 block">From</label>
              <input
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                className="w-full bg-zinc-900/60 border border-white/5 rounded-xl px-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500/50 transition-all"
              />
            </div>

            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Subject</label>
              <input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Email subject..."
                className="w-full bg-zinc-900/60 border border-white/5 rounded-xl px-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500/50 transition-all"
              />
            </div>

            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Email Body</label>
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={8}
                placeholder="Paste the customer's email here..."
                className="w-full bg-zinc-900/60 border border-white/5 rounded-xl px-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500/50 transition-all resize-none"
              />
            </div>

            <div>
              <label className="text-xs text-zinc-500 mb-1 block">
                Reference Reply (optional — for evaluation)
              </label>
              <textarea
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                rows={4}
                placeholder="Paste ideal/expected reply for evaluation comparison..."
                className="w-full bg-zinc-900/60 border border-white/5 rounded-xl px-3 py-2 text-sm text-zinc-200 outline-none focus:border-violet-500/50 transition-all resize-none"
              />
            </div>

            <div className="flex items-center gap-3">
              <label className="text-xs text-zinc-500">Retrieved examples (k):</label>
              <input
                type="number"
                min={1}
                max={10}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-16 bg-zinc-900/60 border border-white/5 rounded-lg px-2 py-1 text-sm text-zinc-200 outline-none text-center"
              />
            </div>

            <button
              onClick={handleGenerate}
              disabled={generating || !subject.trim() || !body.trim()}
              className="w-full flex items-center justify-center gap-2 bg-violet-500 hover:bg-violet-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl py-2.5 text-sm font-medium transition-all pulse-glow"
            >
              {generating ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Generating…</>
              ) : (
                <><Send className="w-4 h-4" /> Generate Response</>
              )}
            </button>
          </div>
        </div>

        {/* Output panel */}
        <div className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400 text-sm animate-fade-in">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          {genResult && (
            <div className="space-y-4 animate-fade-in">
              {/* Generated reply */}
              <div className="glass rounded-2xl p-5 border border-violet-500/20">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-violet-400" />
                    <h2 className="text-sm font-semibold text-zinc-200">Generated Reply</h2>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-zinc-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatMs(genResult.generation_time_ms)}
                    </span>
                    <span className="bg-zinc-800 px-2 py-0.5 rounded-full">
                      {genResult.model_used}
                    </span>
                    <span>{genResult.prompt_tokens + genResult.completion_tokens} tokens</span>
                  </div>
                </div>
                <div className="bg-zinc-900/60 rounded-xl p-4 text-sm text-zinc-200 leading-relaxed border border-white/5 whitespace-pre-wrap max-h-72 overflow-y-auto">
                  {genResult.generated_reply}
                </div>

                {/* Evaluate button */}
                <button
                  onClick={handleEvaluate}
                  disabled={evaluating}
                  className="mt-3 w-full flex items-center justify-center gap-2 bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/20 text-emerald-400 rounded-xl py-2 text-sm font-medium transition-all disabled:opacity-50"
                >
                  {evaluating ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Evaluating…</>
                  ) : (
                    <><BookOpen className="w-4 h-4" /> Evaluate Response</>
                  )}
                </button>
              </div>

              {/* Retrieved emails */}
              {genResult.retrieved_emails.length > 0 && (
                <div className="glass rounded-2xl border border-white/5 overflow-hidden">
                  <button
                    onClick={() => setShowRetrieved(!showRetrieved)}
                    className="w-full flex items-center justify-between p-4 text-sm text-zinc-200 hover:bg-white/3 transition-all"
                  >
                    <span className="font-medium">
                      Retrieved Examples ({genResult.retrieved_emails.length})
                    </span>
                    {showRetrieved ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                  {showRetrieved && (
                    <div className="divide-y divide-white/5">
                      {genResult.retrieved_emails.map((r) => (
                        <div key={r.id} className="p-4 space-y-2">
                          <div className="flex items-center justify-between">
                            <p className="text-xs font-medium text-zinc-300 truncate">{r.subject}</p>
                            <span className="text-[10px] text-violet-300 bg-violet-500/10 px-2 py-0.5 rounded-full">
                              {(r.similarity_score * 100).toFixed(0)}% match
                            </span>
                          </div>
                          <p className="text-[11px] text-zinc-500 truncate">{r.body.substring(0, 100)}…</p>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-500">{r.category}</span>
                            <span className="text-[10px] text-zinc-600">{r.intent}</span>
                          </div>
                          {r.retrieval_reason && (
                            <p className="text-[10px] text-violet-300/80 bg-violet-950/20 border border-violet-900/30 rounded-lg p-2 leading-relaxed italic">
                              <span className="font-semibold not-italic">Why retrieved:</span> {r.retrieval_reason}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Evaluation results */}
      {evalResult && (
        <div className="space-y-6 animate-fade-in border-t border-white/5 pt-6">
          <h2 className="text-xl font-bold text-white mb-4">Evaluation Results Dashboard</h2>

          {/* Upgraded Evaluation Summary Grid */}
          <div className="grid grid-cols-4 gap-4">
            <div className="glass rounded-2xl p-5 border border-white/5 flex flex-col justify-center">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Overall Grade</span>
              <p className={`text-4xl font-black mt-1 ${gradeColor(evalResult.grade)}`}>{evalResult.grade}</p>
            </div>
            <div className="glass rounded-2xl p-5 border border-white/5 flex flex-col justify-center">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Overall Score</span>
              <p className="text-3xl font-bold text-white mt-1">{formatScore(evalResult.overall_score)}</p>
            </div>
            <div className="glass rounded-2xl p-5 border border-white/5 flex flex-col justify-center">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Confidence Estimate</span>
              <p className="text-3xl font-bold text-violet-400 mt-1">{formatScore(evalResult.confidence)}</p>
            </div>
            <div className="glass rounded-2xl p-5 border border-white/5 flex flex-col justify-center">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Action Status</span>
              {evalResult.traffic_light === "green" ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl text-xs font-semibold mt-2 self-start uppercase">
                  Ready to Send
                </span>
              ) : evalResult.traffic_light === "amber" ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-xl text-xs font-semibold mt-2 self-start uppercase">
                  Needs Revision
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl text-xs font-semibold mt-2 self-start uppercase">
                  Reject / Rewrite
                </span>
              )}
            </div>
          </div>

          {/* Executive Summary */}
          {evalResult.executive_summary && (
            <div className="glass rounded-2xl p-5 border border-violet-500/20 bg-violet-950/5">
              <p className="text-xs text-violet-400 font-semibold uppercase tracking-wider mb-1.5">Executive QA Summary</p>
              <p className="text-sm text-zinc-300 leading-relaxed italic">"{evalResult.executive_summary}"</p>
            </div>
          )}

          {/* Explainability Pipeline Flow */}
          <ExplainabilityFlow />

          {/* Email Diff View */}
          <EmailDiff
            generated={genResult?.generated_reply || ""}
            reference={reference || ""}
            missingActions={(evalResult.metric_breakdown.action_coverage.details.missing_actions as string[]) || []}
            hallucinatedStatements={
              (evalResult.metric_breakdown.hallucination_score.details.ungrounded_examples as string[]) || []
            }
          />

          {/* Top-level score & Radar Chart */}
          <div className="glass rounded-2xl p-6 border border-white/5">
            <div className="flex items-center gap-8">
              <ScoreRing score={evalResult.overall_score} size={120} label="Overall Score" />

              <div className="flex-1 space-y-4">
                <div className="flex items-center gap-6">
                  <TrafficLight status={evalResult.traffic_light} />
                  <div>
                    <span className="text-xs text-zinc-500">Confidence Score</span>
                    <p className="text-lg font-bold text-zinc-200">
                      {formatScore(evalResult.confidence)}
                    </p>
                  </div>
                </div>

                <div className="space-y-1">
                  {evalResult.strengths.slice(0, 2).map((s, i) => (
                    <p key={i} className="text-xs text-emerald-400">{s}</p>
                  ))}
                  {evalResult.weaknesses.slice(0, 2).map((w, i) => (
                    <p key={i} className="text-xs text-red-400">{w}</p>
                  ))}
                </div>
              </div>

              <div className="w-72">
                <EvalRadarChart data={radarData} />
              </div>
            </div>
          </div>

          {/* Explainability & Gap Analysis Panel */}
          <div className="glass rounded-2xl p-5 border border-white/5 space-y-4">
            <h3 className="text-sm font-semibold text-zinc-200">🔍 Gap Analysis & Detail Matrix</h3>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="bg-zinc-900/60 rounded-xl p-4 border border-white/5 space-y-3">
                <p className="font-semibold text-rose-300">Identified Gaps & Missing Elements</p>
                <ul className="space-y-2 text-zinc-400">
                  <li>
                    <span className="font-semibold text-zinc-300">Missing Actions:</span>{" "}
                    {Array.isArray(evalResult.metric_breakdown.action_coverage.details.missing_actions) &&
                    evalResult.metric_breakdown.action_coverage.details.missing_actions.length > 0
                      ? evalResult.metric_breakdown.action_coverage.details.missing_actions.join(", ")
                      : "None"}
                  </li>
                  <li>
                    <span className="font-semibold text-zinc-300">Missing Entities:</span>{" "}
                    {Array.isArray(evalResult.metric_breakdown.entity_coverage.details.missing_entities) &&
                    evalResult.metric_breakdown.entity_coverage.details.missing_entities.length > 0
                      ? evalResult.metric_breakdown.entity_coverage.details.missing_entities.join(", ")
                      : "None"}
                  </li>
                  <li>
                    <span className="font-semibold text-zinc-300">Expected Tone Match:</span>{" "}
                    {evalResult.metric_breakdown.tone_match.score < 0.8
                      ? `Expected tone was not achieved.`
                      : "Successfully matched tone standards."}
                  </li>
                </ul>
              </div>
              <div className="bg-zinc-900/60 rounded-xl p-4 border border-white/5 space-y-2">
                <div>
                  <p className="font-semibold text-emerald-300">Strengths</p>
                  <div className="text-zinc-400 mt-1 max-h-24 overflow-y-auto space-y-0.5">
                    {evalResult.strengths.map((str, idx) => (
                      <p key={idx}>• {str}</p>
                    ))}
                  </div>
                </div>
                {evalResult.weaknesses.length > 0 && (
                  <div>
                    <p className="font-semibold text-red-300">Weaknesses</p>
                    <div className="text-zinc-400 mt-1 max-h-24 overflow-y-auto space-y-0.5">
                      {evalResult.weaknesses.map((weak, idx) => (
                        <p key={idx}>• {weak}</p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Metric cards grid */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            {Object.entries(evalResult.metric_breakdown).map(([key, val]) => {
              const v = val as {
                score: number;
                weight: number;
                explanation: string;
                why_lost_points?: string;
                how_to_improve?: string;
              };
              return (
                <MetricCard
                  key={key}
                  label={key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  score={v.score}
                  weight={v.weight > 0 ? v.weight : undefined}
                  explanation={v.explanation}
                  why_lost_points={v.why_lost_points}
                  how_to_improve={v.how_to_improve}
                />
              );
            })}
          </div>

          {/* Recommendations */}
          {evalResult.recommendations.length > 0 && (
            <div className="glass rounded-2xl p-5 border border-amber-500/20">
              <h3 className="text-sm font-semibold text-amber-400 mb-3">💡 Recommendations</h3>
              <ul className="space-y-2">
                {evalResult.recommendations.map((rec, i) => (
                  <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                    <span className="text-amber-400 mt-0.5">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
