"use client";

import { formatScore } from "@/lib/utils";

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export function ScoreRing({
  score,
  size = 120,
  strokeWidth = 8,
  label = "Score",
}: ScoreRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score);

  const getColor = (s: number) => {
    if (s >= 0.75) return "#34d399"; // emerald
    if (s >= 0.50) return "#fbbf24"; // amber
    return "#f87171"; // red
  };

  const color = getColor(score);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="-rotate-90"
          viewBox={`0 0 ${size} ${size}`}
        >
          {/* Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              transition: "stroke-dashoffset 1s ease-in-out",
              filter: `drop-shadow(0 0 6px ${color}80)`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white">
            {(score * 100).toFixed(0)}
          </span>
          <span className="text-[10px] text-zinc-500 uppercase tracking-wider">%</span>
        </div>
      </div>
      <span className="text-xs text-zinc-400">{label}</span>
    </div>
  );
}
