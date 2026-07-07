"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Brain,
  Database,
  FlaskConical,
  Home,
  Zap,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/dataset", label: "Dataset", icon: Database },
  { href: "/generate", label: "Generate", icon: Zap },
  { href: "/evaluation", label: "Evaluation", icon: FlaskConical },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full w-64 glass border-r border-white/5 z-50">
      {/* Logo */}
      <div className="p-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center shadow-lg shadow-violet-500/25">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-semibold text-sm text-white leading-tight">
              AI Email
            </div>
            <div className="text-xs text-zinc-400">Response System</div>
          </div>
        </div>
      </div>

      {/* Nav links */}
      <nav className="p-4 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? "bg-violet-500/15 text-violet-300 border border-violet-500/20"
                  : "text-zinc-400 hover:text-zinc-100 hover:bg-white/5"
              }`}
            >
              <Icon
                className={`w-4 h-4 transition-colors ${
                  isActive ? "text-violet-400" : "text-zinc-500 group-hover:text-zinc-300"
                }`}
              />
              {label}
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-violet-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/5">
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Powered by Gemini + FAISS</span>
        </div>
      </div>
    </aside>
  );
}
