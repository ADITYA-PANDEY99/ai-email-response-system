"use client";

import { formatScore } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  score: number;
  weight?: number;
  explanation?: string;
  why_lost_points?: string;
  how_to_improve?: string;
  className?: string;
}

export function MetricCard({
  label,
  score,
  weight,
  explanation,
  why_lost_points,
  how_to_improve,
  className = "",
}: MetricCardProps) {
  const getColor = (s: number) => {
    if (s >= 0.75) return { bar: "bg-emerald-400", text: "text-emerald-400", bg: "bg-emerald-400/10" };
    if (s >= 0.50) return { bar: "bg-amber-400", text: "text-amber-400", bg: "bg-amber-400/10" };
    return { bar: "bg-red-400", text: "text-red-400", bg: "bg-red-400/10" };
  };

  const colors = getColor(score);

  return (
    <div
      className={`glass rounded-2xl p-4 border border-white/5 hover:border-white/10 transition-all duration-200 ${className}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-xs text-zinc-400 font-medium uppercase tracking-wider">
            {label}
          </p>
          {weight !== undefined && (
            <p className="text-[10px] text-zinc-600 mt-0.5">
              Weight: {(weight * 100).toFixed(0)}%
            </p>
          )}
        </div>
        <span className={`text-lg font-bold ${colors.text}`}>
          {formatScore(score)}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-3">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${colors.bar}`}
          style={{ width: `${score * 100}%` }}
        />
      </div>

      {/* Explanation */}
      {explanation && (
        <p className="text-[11px] text-zinc-500 leading-relaxed mb-2">
          {explanation}
        </p>
      )}

      {/* Why lost points */}
      {why_lost_points && score < 0.95 && (
        <div className="mt-2 text-[10px] text-red-300 bg-red-950/20 border border-red-900/30 rounded-lg p-2 leading-relaxed">
          <span className="font-semibold">Why lost points:</span> {why_lost_points}
        </div>
      )}

      {/* How to improve */}
      {how_to_improve && score < 0.95 && (
        <div className="mt-1 text-[10px] text-emerald-300 bg-emerald-950/20 border border-emerald-900/30 rounded-lg p-2 leading-relaxed">
          <span className="font-semibold">How to improve:</span> {how_to_improve}
        </div>
      )}
    </div>
  );
}
