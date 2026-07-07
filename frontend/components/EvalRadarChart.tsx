"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { RadarDataPoint } from "@/types";

interface EvalRadarChartProps {
  data: RadarDataPoint[];
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { value: number }[] }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-xl px-3 py-2 border border-white/10 text-sm">
        <span className="text-violet-300 font-medium">
          {(payload[0].value * 100).toFixed(1)}%
        </span>
      </div>
    );
  }
  return null;
};

export function EvalRadarChart({ data }: EvalRadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
        <PolarGrid stroke="rgba(255,255,255,0.08)" />
        <PolarAngleAxis
          dataKey="metric"
          tick={{ fill: "#71717a", fontSize: 10, fontFamily: "var(--font-inter)" }}
        />
        <Radar
          name="Score"
          dataKey="score"
          stroke="#8b5cf6"
          fill="#8b5cf6"
          fillOpacity={0.2}
          strokeWidth={2}
          dot={{ fill: "#8b5cf6", strokeWidth: 0, r: 4 }}
        />
        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
