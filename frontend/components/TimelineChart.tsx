"use client";

import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface TimelineChartProps {
  data: Array<{ date: string; score: number }>;
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: any[];
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass rounded-xl px-3 py-2 border border-white/10 text-xs">
        <p className="text-zinc-500">Date: {new Date(payload[0].name || "").toLocaleDateString()}</p>
        <p className="text-emerald-400 font-bold">Score: {(payload[0].value * 100).toFixed(0)}%</p>
      </div>
    );
  }
  return null;
};

export function TimelineChart({ data }: TimelineChartProps) {
  // Map data to preserve name for tooltips
  const chartData = data.map((item) => ({
    name: item.date,
    score: item.score,
    dateStr: new Date(item.date).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    }),
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="scoreColor" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="dateStr"
          tick={{ fill: "#71717a", fontSize: 9 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 1]}
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          tick={{ fill: "#71717a", fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="score"
          stroke="#10b981"
          strokeWidth={2}
          fillOpacity={1}
          fill="url(#scoreColor)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
