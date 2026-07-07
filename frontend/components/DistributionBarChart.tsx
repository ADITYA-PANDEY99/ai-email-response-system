"use client";

import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface DistributionBarChartProps {
  data: Array<{ range: string; count: number }>;
}

const COLORS = [
  "#f87171", "#f87171", "#fbbf24", "#fbbf24",
  "#fbbf24", "#34d399", "#34d399", "#34d399",
  "#22c55e", "#10b981",
];

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-xl px-3 py-2 border border-white/10 text-sm">
        <p className="text-zinc-300">{label}</p>
        <p className="text-violet-300 font-medium">{payload[0].value} responses</p>
      </div>
    );
  }
  return null;
};

export function DistributionBarChart({ data }: DistributionBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
        <XAxis
          dataKey="range"
          tick={{ fill: "#71717a", fontSize: 9 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "#71717a", fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index] ?? "#8b5cf6"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
