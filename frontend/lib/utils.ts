/**
 * Utility functions shared across the frontend.
 */

export function scoreToColor(score: number): string {
  if (score >= 0.75) return "text-emerald-400";
  if (score >= 0.50) return "text-amber-400";
  return "text-red-400";
}

export function scoreToGradient(score: number): string {
  if (score >= 0.75) return "from-emerald-500 to-green-400";
  if (score >= 0.50) return "from-amber-500 to-yellow-400";
  return "from-red-500 to-rose-400";
}

export function scoreToBg(score: number): string {
  if (score >= 0.75) return "bg-emerald-500/10 border-emerald-500/30";
  if (score >= 0.50) return "bg-amber-500/10 border-amber-500/30";
  return "bg-red-500/10 border-red-500/30";
}

export function trafficLightColor(light: "green" | "amber" | "red" | null): string {
  if (light === "green") return "bg-emerald-400";
  if (light === "amber") return "bg-amber-400";
  if (light === "red") return "bg-red-400";
  return "bg-zinc-500";
}

export function gradeColor(grade: string): string {
  const map: Record<string, string> = {
    A: "text-emerald-400",
    B: "text-green-400",
    C: "text-amber-400",
    D: "text-orange-400",
    F: "text-red-400",
  };
  return map[grade] ?? "text-zinc-400";
}

export function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}

export function formatMs(ms: number): string {
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function priorityColor(priority: string): string {
  const map: Record<string, string> = {
    critical: "text-red-400 bg-red-400/10 border-red-400/30",
    high: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    medium: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    low: "text-blue-400 bg-blue-400/10 border-blue-400/30",
  };
  return map[priority.toLowerCase()] ?? "text-zinc-400 bg-zinc-400/10 border-zinc-400/30";
}

export function categoryIcon(category: string): string {
  const map: Record<string, string> = {
    Refund: "💰",
    Shipping: "📦",
    Billing: "🧾",
    "Technical Support": "🔧",
    "Password Reset": "🔑",
    Cancellation: "❌",
    Sales: "🤝",
    Enterprise: "🏢",
    Pricing: "💲",
    "Bug Report": "🐛",
    "Feature Request": "✨",
    Subscription: "🔄",
    "Account Access": "🔐",
    "Customer Complaint": "😤",
    "Positive Feedback": "⭐",
  };
  return map[category] ?? "📧";
}

export function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.substring(0, maxLen).trimEnd() + "…";
}

export function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}
