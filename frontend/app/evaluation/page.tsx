"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  FlaskConical,
  Loader2,
  TrendingUp,
} from "lucide-react";
import { evaluateApi, analyticsApi } from "@/lib/api";
import type { EvalHistoryItem, SystemEvalSummary } from "@/types";
import { MetricCard } from "@/components/MetricCard";
import { TrafficLight } from "@/components/TrafficLight";
import { EvalRadarChart } from "@/components/EvalRadarChart";
import { DistributionBarChart } from "@/components/DistributionBarChart";
import { formatScore, timeAgo } from "@/lib/utils";
import { TimelineChart } from "@/components/TimelineChart";

export default function EvaluationPage() {
  const [history, setHistory] = useState<EvalHistoryItem[]>([]);
  const [summary, setSummary] = useState<SystemEvalSummary | null>(null);
  const [radarData, setRadarData] = useState<{ metric: string; score: number }[]>([]);
  const [distribution, setDistribution] = useState<{ range: string; count: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<EvalHistoryItem | null>(null);
  const [selectedFull, setSelectedFull] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    Promise.all([
      evaluateApi.history(50),
      evaluateApi.summary(),
      analyticsApi.radarData(),
      analyticsApi.scoreDistribution(),
    ]).then(([h, s, r, d]) => {
      setHistory(h);
      setSummary(s);
      setRadarData(r);
      setDistribution(d);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleSelectEval = async (item: EvalHistoryItem) => {
    setSelected(item);
    try {
      const full = await evaluateApi.get(item.id) as unknown as Record<string, unknown>;
      setSelectedFull(full);
    } catch {
      setSelectedFull(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
      </div>
    );
  }

  const gradeColors: Record<string, string> = {
    A: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
    B: "text-green-400 bg-green-400/10 border-green-400/20",
    C: "text-amber-400 bg-amber-400/10 border-amber-400/20",
    D: "text-orange-400 bg-orange-400/10 border-orange-400/20",
    F: "text-red-400 bg-red-400/10 border-red-400/20",
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <FlaskConical className="w-6 h-6 text-emerald-400" />
          Evaluation Dashboard
        </h1>
        <p className="text-zinc-400 text-sm mt-1">
          12-metric weighted scoring engine · {summary?.total_evaluations ?? 0} evaluations
        </p>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-3 gap-4">
          <div className="glass rounded-2xl p-5 border border-white/5">
            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Average Score</p>
            <p className="text-3xl font-bold text-white">{formatScore(summary.average_score)}</p>
            <div className="h-1.5 bg-zinc-800 rounded-full mt-3">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-500 to-blue-500"
                style={{ width: `${summary.average_score * 100}%` }}
              />
            </div>
          </div>

          <div className="glass rounded-2xl p-5 border border-white/5">
            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Grade Distribution</p>
            <div className="flex items-end gap-2">
              {Object.entries(summary.score_distribution).map(([grade, count]) => (
                <div key={grade} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-zinc-400">{count}</span>
                  <div
                    className={`w-full rounded-t border ${gradeColors[grade] ?? ""}`}
                    style={{
                      height: `${Math.max(8, (count / Math.max(...Object.values(summary.score_distribution))) * 60)}px`,
                    }}
                  />
                  <span className={`text-xs font-bold ${gradeColors[grade]?.split(" ")[0] ?? ""}`}>
                    {grade}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass rounded-2xl p-5 border border-white/5">
            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Top Metrics</p>
            <div className="space-y-2">
              {Object.entries(summary.metric_averages)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 4)
                .map(([metric, score]) => (
                  <div key={metric} className="flex items-center gap-2">
                    <div className="h-1.5 bg-zinc-800 rounded-full flex-1">
                      <div
                        className="h-full rounded-full bg-emerald-400"
                        style={{ width: `${score * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-zinc-400 w-24 truncate">
                      {metric.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs text-zinc-300 w-10 text-right">{formatScore(score)}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-3 gap-6">
        <div className="glass rounded-2xl p-5 border border-white/5">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="w-4 h-4 text-violet-400" />
            <h2 className="text-sm font-semibold text-zinc-200">Average Metric Performance</h2>
          </div>
          {radarData.length > 0 ? (
            <EvalRadarChart data={radarData} />
          ) : (
            <div className="h-64 flex items-center justify-center text-zinc-600 text-sm">
              No evaluations yet
            </div>
          )}
        </div>

        <div className="glass rounded-2xl p-5 border border-white/5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-violet-400" />
            <h2 className="text-sm font-semibold text-zinc-200">Score Distribution</h2>
          </div>
          {distribution.length > 0 ? (
            <DistributionBarChart data={distribution} />
          ) : (
            <div className="h-64 flex items-center justify-center text-zinc-600 text-sm">
              No data yet
            </div>
          )}
        </div>

        <div className="glass rounded-2xl p-5 border border-white/5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-zinc-200">Evaluation Timeline Trend</h2>
          </div>
          {summary?.improvement_trend && summary.improvement_trend.length > 0 ? (
            <TimelineChart data={summary.improvement_trend} />
          ) : (
            <div className="h-64 flex items-center justify-center text-zinc-600 text-sm">
              No data yet
            </div>
          )}
        </div>
      </div>

      {/* History + Detail */}
      <div className="grid grid-cols-3 gap-6">
        {/* History list */}
        <div className="col-span-1 glass rounded-2xl border border-white/5 overflow-hidden">
          <div className="p-4 border-b border-white/5">
            <h2 className="text-sm font-semibold text-zinc-200">
              Evaluation History ({history.length})
            </h2>
          </div>
          <div className="divide-y divide-white/5 max-h-96 overflow-y-auto">
            {history.length === 0 ? (
              <div className="p-8 text-center text-zinc-600 text-sm">
                No evaluations yet
              </div>
            ) : (
              history.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSelectEval(item)}
                  className={`p-3 cursor-pointer transition-all hover:bg-white/3 ${
                    selected?.id === item.id ? "bg-violet-500/5 border-l-2 border-violet-500" : ""
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <TrafficLight status={item.traffic_light} size="sm" showLabel={false} />
                    <span className={`text-sm font-bold ${
                      item.overall_score >= 0.75 ? "text-emerald-400"
                        : item.overall_score >= 0.50 ? "text-amber-400"
                        : "text-red-400"
                    }`}>
                      {formatScore(item.overall_score)}
                    </span>
                    <span className="text-[10px] text-zinc-600 ml-auto">
                      {timeAgo(item.created_at)}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-1 text-[10px] text-zinc-500">
                    <span>Sem: {formatScore(item.semantic_similarity)}</span>
                    <span>Intent: {formatScore(item.intent_match)}</span>
                    <span>Complete: {formatScore(item.completeness)}</span>
                    <span>Safety: {formatScore(item.safety)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Detail panel */}
        <div className="col-span-2 glass rounded-2xl border border-white/5 p-5 overflow-y-auto max-h-[500px]">
          {selectedFull ? (
            <div className="space-y-4 animate-fade-in">
              <h3 className="text-sm font-semibold text-zinc-200">
                Evaluation #{(selectedFull as { id: number }).id} — Detailed Breakdown
              </h3>

              <div className="grid grid-cols-3 gap-3">
                {[
                  "semantic_similarity", "intent_match", "completeness",
                  "tone_match", "action_coverage", "safety",
                  "grammar_quality", "professionalism", "length_penalty",
                  "hallucination_score", "entity_coverage", "retrieval_consistency",
                ].map((metric) => {
                  const score = (selectedFull as Record<string, number>)[metric] ?? 0;
                  const metricExpObj = ((selectedFull as Record<string, Record<string, any>>)["metric_explanations"] ?? {})[metric] || {};
                  const explanation = typeof metricExpObj === "string" ? metricExpObj : (metricExpObj.explanation || "");
                  const why_lost_points = typeof metricExpObj === "object" ? metricExpObj.why_lost_points : undefined;
                  const how_to_improve = typeof metricExpObj === "object" ? metricExpObj.how_to_improve : undefined;
                  return (
                    <MetricCard
                      key={metric}
                      label={metric.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                      score={score}
                      explanation={explanation}
                      why_lost_points={why_lost_points}
                      how_to_improve={how_to_improve}
                    />
                  );
                })}
              </div>

              {/* Recommendations */}
              {Array.isArray((selectedFull as { recommendations: string[] }).recommendations) &&
                (selectedFull as { recommendations: string[] }).recommendations.length > 0 && (
                <div className="bg-amber-500/5 rounded-xl p-4 border border-amber-500/15">
                  <h4 className="text-xs font-semibold text-amber-400 mb-2">Recommendations</h4>
                  {(selectedFull as { recommendations: string[] }).recommendations.map((r: string, i: number) => (
                    <p key={i} className="text-xs text-zinc-300 mb-1">• {r}</p>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full py-16 text-zinc-600">
              <FlaskConical className="w-8 h-8 mb-2 opacity-30" />
              <p className="text-sm">Select an evaluation to see full breakdown</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
