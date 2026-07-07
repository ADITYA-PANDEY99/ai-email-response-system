"use client";

interface TrafficLightProps {
  status: "green" | "amber" | "red" | null;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

const colorMap = {
  green: { active: "bg-emerald-400 shadow-emerald-400/60", inactive: "bg-zinc-700" },
  amber: { active: "bg-amber-400 shadow-amber-400/60", inactive: "bg-zinc-700" },
  red: { active: "bg-red-400 shadow-red-400/60", inactive: "bg-zinc-700" },
};

const labelMap = {
  green: "Excellent",
  amber: "Needs Review",
  red: "Poor Quality",
};

const sizeMap = {
  sm: "w-3 h-3",
  md: "w-4 h-4",
  lg: "w-5 h-5",
};

export function TrafficLight({
  status,
  size = "md",
  showLabel = true,
}: TrafficLightProps) {
  const dotSize = sizeMap[size];

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5 bg-zinc-900 p-2 rounded-full border border-white/10">
        {(["green", "amber", "red"] as const).map((color) => (
          <div
            key={color}
            className={`${dotSize} rounded-full transition-all duration-300 ${
              status === color
                ? `${colorMap[color].active} shadow-lg traffic-pulse`
                : colorMap[color].inactive
            }`}
          />
        ))}
      </div>
      {showLabel && status && (
        <span
          className={`text-sm font-medium ${
            status === "green"
              ? "text-emerald-400"
              : status === "amber"
              ? "text-amber-400"
              : "text-red-400"
          }`}
        >
          {labelMap[status]}
        </span>
      )}
    </div>
  );
}
