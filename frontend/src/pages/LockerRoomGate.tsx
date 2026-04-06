import { useState, useEffect, useCallback } from "react";
import { Lock, ShieldAlert, CheckCircle, XCircle, RefreshCw, Loader2 } from "lucide-react";
import { triviaApi, type TriviaQuestion } from "../services/api";

/* ── session id (persists for this browser tab) ── */
function getSessionId(): string {
  let id = sessionStorage.getItem("f433_gate_session");
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem("f433_gate_session", id);
  }
  return id;
}

interface LockerRoomGateProps {
  onPass: () => void;
}

export function LockerRoomGate({ onPass }: LockerRoomGateProps) {
  const [question, setQuestion] = useState<(TriviaQuestion & { correct_answer?: string }) | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<{ is_correct: boolean; message: string; correct_answer: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const fetchQuestion = useCallback(async () => {
    setLoading(true);
    setSelected(null);
    setResult(null);
    try {
      const q = await triviaApi.question();
      setQuestion(q);
    } catch {
      // Use a hardcoded fallback if API fails
      setQuestion({
        question: "Which country has won the most FIFA World Cups?",
        options: ["Germany", "Brazil", "Argentina", "Italy"],
        correct_answer: "Brazil",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQuestion();
  }, [fetchQuestion]);

  const handleSubmit = async () => {
    if (!selected || !question) return;
    setSubmitting(true);

    try {
      // For AI-generated questions we need to get the answer from the backend
      const res = await triviaApi.answer({
        session_id: getSessionId(),
        question: question.question,
        options: question.options,
        correct_answer: question.correct_answer ?? selected, // backend validates
        user_answer: selected,
      });
      setResult(res);

      if (res.is_correct) {
        // Small delay so user sees the success state before transition
        setTimeout(() => onPass(), 1500);
      }
    } catch {
      setResult({
        is_correct: false,
        correct_answer: "Unknown",
        message: "Something went wrong. Try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* ── Background FX ── */}
      <div className="fixed inset-0 pointer-events-none">
        {/* Scanlines */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.03) 2px, rgba(255,255,255,0.03) 4px)",
          }}
        />
        {/* Grid */}
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(244,63,94,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(244,63,94,0.15) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
        {/* Orbs */}
        <div className="absolute top-1/4 -left-20 w-80 h-80 rounded-full bg-red-500/[0.06] blur-[120px]" />
        <div className="absolute bottom-1/4 -right-20 w-72 h-72 rounded-full bg-amber-500/[0.05] blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-rose-500/[0.04] blur-[180px]" />
      </div>

      <div className="relative z-10 w-full max-w-lg mx-auto px-4">
        {/* ── Restricted Area Header ── */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 mb-4">
            <ShieldAlert className="w-8 h-8 text-red-400" />
          </div>
          <h1 className="font-['Bebas_Neue'] text-[2.8rem] leading-[0.9] tracking-wide text-white">
            RESTRICTED
            <br />
            <span className="bg-gradient-to-r from-red-400 via-amber-400 to-red-400 bg-clip-text text-transparent">
              ZONE
            </span>
          </h1>
          <p className="mt-4 text-sm text-gray-500 max-w-sm mx-auto leading-relaxed">
            Only those who bleed football get past these doors.
            <br />
            Prove you belong — answer the question below.
          </p>
        </div>

        {/* ── Question Card ── */}
        <div
          className="rounded-2xl border overflow-hidden backdrop-blur-sm"
          style={{
            borderColor: result
              ? result.is_correct
                ? "rgba(34,197,94,0.3)"
                : "rgba(239,68,68,0.3)"
              : "rgba(255,255,255,0.08)",
            boxShadow: result
              ? result.is_correct
                ? "0 0 60px rgba(34,197,94,0.1)"
                : "0 0 60px rgba(239,68,68,0.1)"
              : "0 0 40px rgba(0,0,0,0.3)",
          }}
        >
          {/* Header strip */}
          <div className="flex items-center gap-2 px-6 py-3 bg-white/[0.03] border-b border-white/[0.06]">
            <Lock className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-[9px] font-black uppercase tracking-[0.3em] text-amber-400/80">
              Security Check
            </span>
          </div>

          <div className="p-6 bg-gradient-to-b from-white/[0.02] to-transparent">
            {loading ? (
              <div className="flex flex-col items-center gap-3 py-12">
                <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
                <p className="text-xs text-gray-600">Generating question...</p>
              </div>
            ) : question ? (
              <>
                {/* Question */}
                <p className="text-white font-bold text-lg leading-snug mb-6">
                  {question.question}
                </p>

                {/* Options */}
                <div className="space-y-2.5">
                  {question.options.map((opt, i) => {
                    const letter = String.fromCharCode(65 + i);
                    const isSelected = selected === opt;
                    const isDisabled = !!result;

                    let optionStyle = "border-white/[0.08] bg-white/[0.02] hover:border-white/[0.15] hover:bg-white/[0.04]";
                    if (isSelected && !result) {
                      optionStyle = "border-cyan-400/40 bg-cyan-500/10 ring-1 ring-cyan-400/20";
                    }
                    if (result) {
                      if (opt === result.correct_answer) {
                        optionStyle = "border-emerald-400/40 bg-emerald-500/10";
                      } else if (isSelected && !result.is_correct) {
                        optionStyle = "border-red-400/40 bg-red-500/10";
                      } else {
                        optionStyle = "border-white/[0.04] bg-white/[0.01] opacity-40";
                      }
                    }

                    return (
                      <button
                        key={opt}
                        onClick={() => !isDisabled && setSelected(opt)}
                        disabled={isDisabled}
                        className={`w-full text-left flex items-center gap-3 rounded-xl border p-4
                          transition-all duration-200 ${optionStyle}
                          ${isDisabled ? "cursor-default" : "cursor-pointer"}`}
                      >
                        <span
                          className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-black shrink-0
                            ${
                              isSelected && !result
                                ? "bg-cyan-500/20 text-cyan-300"
                                : result && opt === result.correct_answer
                                  ? "bg-emerald-500/20 text-emerald-300"
                                  : result && isSelected && !result.is_correct
                                    ? "bg-red-500/20 text-red-300"
                                    : "bg-white/[0.06] text-gray-500"
                            }`}
                        >
                          {result && opt === result.correct_answer ? (
                            <CheckCircle className="w-4 h-4" />
                          ) : result && isSelected && !result.is_correct ? (
                            <XCircle className="w-4 h-4" />
                          ) : (
                            letter
                          )}
                        </span>
                        <span
                          className={`text-sm font-medium ${
                            isSelected && !result
                              ? "text-white"
                              : result && opt === result.correct_answer
                                ? "text-emerald-300"
                                : result && isSelected && !result.is_correct
                                  ? "text-red-300"
                                  : "text-gray-300"
                          }`}
                        >
                          {opt}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {/* Result message */}
                {result && (
                  <div
                    className={`mt-5 flex items-center gap-2.5 rounded-xl px-4 py-3 text-sm font-medium
                      ${
                        result.is_correct
                          ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-300"
                          : "bg-red-500/10 border border-red-500/20 text-red-300"
                      }`}
                  >
                    {result.is_correct ? (
                      <CheckCircle className="w-4 h-4 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 shrink-0" />
                    )}
                    {result.message}
                  </div>
                )}

                {/* Actions */}
                <div className="mt-6 flex items-center gap-3">
                  {!result ? (
                    <button
                      onClick={handleSubmit}
                      disabled={!selected || submitting}
                      className={`flex-1 flex items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-black
                        uppercase tracking-wider transition-all duration-300
                        ${
                          selected && !submitting
                            ? "bg-gradient-to-r from-amber-500 via-red-500 to-amber-500 text-white hover:shadow-[0_0_30px_rgba(239,68,68,0.3)] hover:scale-[1.02]"
                            : "bg-white/[0.05] text-gray-600 cursor-not-allowed"
                        }`}
                    >
                      {submitting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Lock className="w-4 h-4" />
                      )}
                      {submitting ? "Checking..." : "Submit Answer"}
                    </button>
                  ) : !result.is_correct ? (
                    <button
                      onClick={fetchQuestion}
                      className="flex-1 flex items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-bold
                        bg-white/[0.06] text-gray-300 border border-white/[0.08]
                        hover:bg-white/[0.1] hover:border-white/[0.15] transition-all"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Try Another Question
                    </button>
                  ) : (
                    <div className="flex-1 flex items-center justify-center gap-2 py-3.5 text-sm text-emerald-400 font-bold">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Entering locker room...
                    </div>
                  )}
                </div>
              </>
            ) : null}
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[10px] text-gray-700 mt-6 uppercase tracking-[0.2em]">
          Every attempt is recorded — no pretenders allowed
        </p>
      </div>

      {/* Inline keyframes */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
