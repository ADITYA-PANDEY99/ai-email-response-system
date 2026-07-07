"use client";

import { useEffect, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Database,
  Loader2,
  RefreshCw,
  Search,
} from "lucide-react";
import { emailsApi, datasetApi } from "@/lib/api";
import type { Email, EmailListResponse, CategoryStat } from "@/types";
import { categoryIcon, priorityColor, truncate } from "@/lib/utils";

const CATEGORIES = [
  "All", "Refund", "Shipping", "Billing", "Technical Support",
  "Password Reset", "Cancellation", "Sales", "Enterprise",
  "Pricing", "Bug Report", "Feature Request", "Subscription",
  "Account Access", "Customer Complaint", "Positive Feedback",
];

export default function DatasetPage() {
  const [data, setData] = useState<EmailListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [selected, setSelected] = useState<Email | null>(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [stats, setStats] = useState<CategoryStat[]>([]);
  const [dbStatus, setDbStatus] = useState<{ email_count: number; faiss_index_size: number } | null>(null);

  const PAGE_SIZE = 15;

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const result = await emailsApi.list({
        page,
        page_size: PAGE_SIZE,
        category: category === "All" ? undefined : category,
        search: search || undefined,
      });
      setData(result);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, category]);

  useEffect(() => {
    setPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, category]);

  useEffect(() => {
    datasetApi.status().then(setDbStatus).catch(() => {});
    emailsApi.categoryStats().then(setStats).catch(() => {});
  }, []);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await datasetApi.seed();
      await fetchEmails();
      const s = await datasetApi.status();
      setDbStatus(s);
    } finally {
      setSeeding(false);
    }
  };

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Database className="w-6 h-6 text-blue-400" />
            Email Dataset
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            {dbStatus?.email_count ?? "—"} emails · {dbStatus?.faiss_index_size ?? "—"} indexed in FAISS
          </p>
        </div>
        <button
          onClick={handleSeed}
          disabled={seeding}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-xl text-sm hover:bg-blue-500/20 transition-all disabled:opacity-50"
        >
          {seeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {seeding ? "Seeding..." : "Seed Dataset"}
        </button>
      </div>

      {/* Category stats */}
      <div className="flex gap-2 flex-wrap">
        {CATEGORIES.map((cat) => {
          const count = cat === "All"
            ? stats.reduce((a, b) => a + b.count, 0)
            : stats.find((s) => s.category === cat)?.count ?? 0;
          return (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                category === cat
                  ? "bg-violet-500/20 border-violet-500/40 text-violet-300"
                  : "bg-zinc-900/50 border-white/5 text-zinc-400 hover:border-white/15"
              }`}
            >
              {cat === "All" ? "📧" : categoryIcon(cat)} {cat}
              {count > 0 && (
                <span className="ml-1.5 text-zinc-600">{count}</span>
              )}
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Email list */}
        <div className="col-span-2 glass rounded-2xl border border-white/5 overflow-hidden">
          {/* Search */}
          <div className="p-4 border-b border-white/5">
            <div className="flex items-center gap-2 bg-zinc-900/60 rounded-xl px-3 py-2 border border-white/5">
              <Search className="w-4 h-4 text-zinc-500" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchEmails()}
                placeholder="Search emails..."
                className="flex-1 bg-transparent text-sm text-zinc-200 placeholder-zinc-600 outline-none"
              />
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
            </div>
          ) : data?.items.length === 0 ? (
            <div className="text-center py-16 text-zinc-600">
              No emails found. Try seeding the dataset.
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              {data?.items.map((email) => (
                <div
                  key={email.id}
                  onClick={() => setSelected(email)}
                  className={`p-4 cursor-pointer transition-all hover:bg-white/3 ${
                    selected?.id === email.id ? "bg-violet-500/5 border-l-2 border-violet-500" : ""
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <p className="text-sm font-medium text-zinc-200 truncate">
                      {categoryIcon(email.category)} {email.subject}
                    </p>
                    <span className={`shrink-0 text-[10px] px-2 py-0.5 rounded-full border font-medium ${priorityColor(email.priority)}`}>
                      {email.priority}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 truncate">{truncate(email.body, 100)}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-[10px] bg-zinc-800 px-2 py-0.5 rounded-full text-zinc-400">
                      {email.category}
                    </span>
                    <span className="text-[10px] text-zinc-600">{email.intent}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {data && data.total > PAGE_SIZE && (
            <div className="flex items-center justify-between p-4 border-t border-white/5">
              <span className="text-xs text-zinc-500">
                Page {page} of {totalPages} · {data.total} total
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded-lg bg-zinc-900 border border-white/5 text-zinc-400 disabled:opacity-30 hover:border-white/15 transition-all"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-1.5 rounded-lg bg-zinc-900 border border-white/5 text-zinc-400 disabled:opacity-30 hover:border-white/15 transition-all"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Detail panel */}
        <div className="glass rounded-2xl border border-white/5 p-5 overflow-y-auto max-h-[700px]">
          {selected ? (
            <div className="space-y-4 animate-fade-in">
              <div>
                <h3 className="text-sm font-semibold text-zinc-200 mb-1">
                  {selected.subject}
                </h3>
                <div className="flex gap-1.5 flex-wrap">
                  {selected.tags.map((tag) => (
                    <span key={tag} className="text-[10px] bg-zinc-800 px-2 py-0.5 rounded-full text-zinc-400">
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-[10px] uppercase text-zinc-600 mb-1">Customer Email</p>
                <div className="bg-zinc-900/60 rounded-xl p-3 text-xs text-zinc-300 leading-relaxed border border-white/5 whitespace-pre-wrap">
                  {selected.body}
                </div>
              </div>

              <div>
                <p className="text-[10px] uppercase text-zinc-600 mb-1">Ideal Reply</p>
                <div className="bg-emerald-500/5 rounded-xl p-3 text-xs text-zinc-300 leading-relaxed border border-emerald-500/10 whitespace-pre-wrap">
                  {selected.ideal_reply}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-zinc-900/60 rounded-xl p-3 border border-white/5">
                  <p className="text-zinc-600 mb-1">Intent</p>
                  <p className="text-zinc-200">{selected.intent}</p>
                </div>
                <div className="bg-zinc-900/60 rounded-xl p-3 border border-white/5">
                  <p className="text-zinc-600 mb-1">Tone</p>
                  <p className="text-zinc-200">{selected.tone}</p>
                </div>
              </div>

              {selected.expected_actions.length > 0 && (
                <div>
                  <p className="text-[10px] uppercase text-zinc-600 mb-1">Expected Actions</p>
                  <div className="space-y-1">
                    {selected.expected_actions.map((action) => (
                      <div key={action} className="text-xs text-zinc-400 flex items-center gap-1.5">
                        <div className="w-1 h-1 bg-violet-400 rounded-full" />
                        {action}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full py-16 text-zinc-600">
              <Database className="w-8 h-8 mb-2 opacity-30" />
              <p className="text-sm">Select an email to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
