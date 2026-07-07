"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Brain,
  CheckCircle,
  Database,
  Loader2,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { analyticsApi, healthApi } from "@/lib/api";
import type { OverviewStats, RadarDataPoint, RecentActivity } from "@/types";
import { EvalRadarChart } from "@/components/EvalRadarChart";
import { TrafficLight } from "@/components/TrafficLight";
import { formatScore, timeAgo } from "@/lib/utils";

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  sub,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  sub?: string;
}) {
  return (
    <div className="glass rounded-2xl p-6 border border-white/5 hover:border-white/10 transition-all group animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">{label}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
          {sub && <p className="text-xs text-zinc-500 mt-1">{sub}</p>}
        </div>
        <div className={`w-11 h-11 rounded-xl ${color} flex items-center justify-center shadow-lg`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </div>
  );
}

export default function HomePage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [radarData, setRadarData] = useState<RadarDataPoint[]>([]);
  const [activity, setActivity] = useState<RecentActivity[]>([]);
  const [health, setHealth] = useState<{
    faiss_index_size: number;
    gemini_configured: boolean;
    using_fallback: boolean;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.overview(),
      analyticsApi.radarData(),
      analyticsApi.recentActivity(8),
      healthApi.check(),
    ]).then(([ov, radar, act, h]) => {
      setOverview(ov);
      setRadarData(radar);
      setActivity(act);
      setHealth(h);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text mb-2">
            AI Email Response System
          </h1>
          <p className="text-zinc-400">
            RAG-powered generation with multi-metric evaluation engine
          </p>
        </div>
        {health && (
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm border ${
            health.gemini_configured
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : "bg-amber-500/10 border-amber-500/30 text-amber-400"
          }`}>
            {health.gemini_configured ? (
              <><CheckCircle className="w-4 h-4" /> Gemini Connected</>
            ) : (
              <><AlertTriangle className="w-4 h-4" /> Using Fallback</>
            )}
          </div>
        )}
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Dataset Emails"
          value={overview?.total_emails.toLocaleString() ?? "—"}
          icon={Database}
          color="bg-blue-500/80 shadow-blue-500/25"
          sub={health ? `${health.faiss_index_size} indexed` : undefined}
        />
        <StatCard
          label="Generated Responses"
          value={overview?.total_generated ?? "—"}
          icon={Zap}
          color="bg-violet-500/80 shadow-violet-500/25"
        />
        <StatCard
          label="Evaluated"
          value={overview?.total_evaluated ?? "—"}
          icon={Brain}
          color="bg-emerald-500/80 shadow-emerald-500/25"
        />
        <StatCard
          label="Avg Score"
          value={overview ? formatScore(overview.average_score) : "—"}
          icon={TrendingUp}
          color="bg-amber-500/80 shadow-amber-500/25"
          sub={overview ? `Safety: ${formatScore(overview.average_safety)}` : undefined}
        />
      </div>

      {/* Charts + Activity */}
      <div className="grid grid-cols-2 gap-6">
        {/* Radar chart */}
        <div className="glass rounded-2xl p-6 border border-white/5">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-violet-400" />
            <h2 className="text-sm font-semibold text-zinc-200">
              Evaluation Metrics Radar
            </h2>
          </div>
          {radarData.length > 0 ? (
            <EvalRadarChart data={radarData} />
          ) : (
            <div className="h-64 flex items-center justify-center text-zinc-600 text-sm">
              No evaluations yet — generate and evaluate an email to see data
            </div>
          )}
        </div>

        {/* Recent activity */}
        <div className="glass rounded-2xl p-6 border border-white/5">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-violet-400" />
            <h2 className="text-sm font-semibold text-zinc-200">
              Recent Activity
            </h2>
          </div>
          <div className="space-y-3">
            {activity.length === 0 ? (
              <p className="text-zinc-600 text-sm text-center py-8">
                No activity yet — try generating a response
              </p>
            ) : (
              activity.map((item) => (
                <div
                  key={item.response_id}
                  className="flex items-center gap-3 p-3 rounded-xl bg-zinc-900/50 border border-white/5 hover:border-white/10 transition-all"
                >
                  <TrafficLight
                    status={item.traffic_light}
                    size="sm"
                    showLabel={false}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-zinc-200 truncate">{item.subject}</p>
                    <p className="text-[10px] text-zinc-500 mt-0.5">
                      {item.model} · {timeAgo(item.generated_at)}
                    </p>
                  </div>
                  {item.overall_score !== null && (
                    <span className={`text-sm font-bold ${
                      item.overall_score >= 0.75 ? "text-emerald-400"
                        : item.overall_score >= 0.50 ? "text-amber-400"
                        : "text-red-400"
                    }`}>
                      {formatScore(item.overall_score)}
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* System info */}
      <div className="glass rounded-2xl p-6 border border-white/5">
        <h2 className="text-sm font-semibold text-zinc-200 mb-4">
          System Architecture
        </h2>
        <div className="grid grid-cols-5 gap-2">
          {[
            { label: "Incoming Email", color: "bg-blue-500/20 border-blue-500/30 text-blue-300" },
            { label: "FAISS Retrieval", color: "bg-violet-500/20 border-violet-500/30 text-violet-300" },
            { label: "Gemini LLM", color: "bg-emerald-500/20 border-emerald-500/30 text-emerald-300" },
            { label: "12-Metric Eval", color: "bg-amber-500/20 border-amber-500/30 text-amber-300" },
            { label: "Scored Response", color: "bg-pink-500/20 border-pink-500/30 text-pink-300" },
          ].map((step, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className={`flex-1 rounded-xl px-3 py-2.5 border text-center text-xs font-medium ${step.color}`}>
                {step.label}
              </div>
              {i < 4 && <span className="text-zinc-600 text-xs">→</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
