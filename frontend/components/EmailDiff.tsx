"use client";

interface EmailDiffProps {
  generated: string;
  reference: string;
  missingActions?: string[];
  hallucinatedStatements?: string[];
}

export function EmailDiff({
  generated,
  reference,
  missingActions = [],
  hallucinatedStatements = [],
}: EmailDiffProps) {
  // Simple sentence splitter
  const getSentences = (text: string) =>
    text
      ? text
          .split(/(?<=[.!?])\s+/)
          .map((s) => s.trim())
          .filter(Boolean)
      : [];

  const genSentences = getSentences(generated);
  const refSentences = getSentences(reference);

  // Classify sentences
  const matched: string[] = [];
  const extra: string[] = [];

  genSentences.forEach((sent) => {
    // If exact or close substring in reference
    const isMatched = refSentences.some(
      (refSent) =>
        refSent.toLowerCase().includes(sent.toLowerCase()) ||
        sent.toLowerCase().includes(refSent.toLowerCase())
    );

    if (isMatched) {
      matched.push(sent);
    } else {
      extra.push(sent);
    }
  });

  const missing = refSentences.filter(
    (refSent) =>
      !genSentences.some(
        (sent) =>
          sent.toLowerCase().includes(refSent.toLowerCase()) ||
          refSent.toLowerCase().includes(sent.toLowerCase())
      )
  );

  return (
    <div className="glass rounded-2xl p-5 border border-white/5 space-y-4">
      <h3 className="text-sm font-semibold text-zinc-200">📊 Interactive Semantic Email Diff</h3>
      <p className="text-[11px] text-zinc-500">
        Compares sentence-level semantic variations and highlights potential gaps, extra claims, and matched text.
      </p>

      <div className="grid grid-cols-2 gap-4 text-xs">
        {/* Left Panel: Ground Truth Reference */}
        <div className="bg-zinc-950/60 rounded-xl p-4 border border-white/5 space-y-3">
          <p className="font-semibold text-zinc-400 border-b border-white/5 pb-2">
            Reference Ideal Reply (Ground Truth)
          </p>
          <div className="space-y-1.5 leading-relaxed overflow-y-auto max-h-64 pr-2">
            {refSentences.length === 0 ? (
              <p className="text-zinc-600 italic">No reference reply provided for diff.</p>
            ) : (
              refSentences.map((sent, idx) => {
                const isMissing = missing.includes(sent);
                return (
                  <span
                    key={idx}
                    className={`inline-block mr-1 p-0.5 rounded transition-all duration-200 ${
                      isMissing
                        ? "bg-red-500/10 text-red-400 border border-red-500/20"
                        : "text-zinc-400"
                    }`}
                    title={isMissing ? "This sentence or concern is missing from the reply." : "Fully covered"}
                  >
                    {sent}{" "}
                  </span>
                );
              })
            )}
          </div>
          {missingActions.length > 0 && (
            <div className="pt-2 border-t border-white/5">
              <span className="text-[10px] font-bold text-red-400 uppercase tracking-wider block mb-1">
                ⚠️ Missing Next-Step Actions:
              </span>
              <div className="flex flex-wrap gap-1">
                {missingActions.map((act) => (
                  <span
                    key={act}
                    className="text-[9px] bg-red-950/40 text-red-400 border border-red-900/30 px-2 py-0.5 rounded-full"
                  >
                    {act}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Panel: Generated Reply Evaluation */}
        <div className="bg-zinc-950/60 rounded-xl p-4 border border-white/5 space-y-3">
          <p className="font-semibold text-zinc-400 border-b border-white/5 pb-2">
            Generated Response (Evaluation Mode)
          </p>
          <div className="space-y-1.5 leading-relaxed overflow-y-auto max-h-64 pr-2">
            {genSentences.map((sent, idx) => {
              const isExtra = extra.includes(sent);
              const isHallucinated =
                isExtra ||
                hallucinatedStatements.some(
                  (hall) =>
                    sent.toLowerCase().includes(hall.toLowerCase()) ||
                    hall.toLowerCase().includes(sent.toLowerCase())
                );

              return (
                <span
                  key={idx}
                  className={`inline-block mr-1 p-0.5 rounded transition-all duration-200 ${
                    isHallucinated
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                  }`}
                  title={
                    isHallucinated
                      ? "This statement is not grounded in context or references."
                      : "Grounded sentence"
                  }
                >
                  {sent}{" "}
                </span>
              );
            })}
          </div>
          <div className="pt-2 border-t border-white/5 flex gap-4 text-[9px] text-zinc-500">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded bg-emerald-500/10 border border-emerald-500/20" />
              <span>Grounded / Matches reference</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded bg-amber-500/10 border border-amber-500/20" />
              <span>Ungrounded / Potential hallucination</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded bg-red-500/10 border border-red-500/20" />
              <span>Missing from generated reply</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
