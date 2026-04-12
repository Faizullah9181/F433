import { useState, useEffect, useMemo } from "react";

// ── Types ──────────────────────────────────────────────────────

interface PitchDeploymentProps {
  agentName: string;
  agentEmoji: string;
  isBenching?: boolean;
  onComplete: () => void;
}

// ── Confetti Particle Positions ────────────────────────────────

function generateParticles(count: number) {
  const colors = [
    "rgba(16,185,129,0.8)",
    "rgba(6,182,212,0.8)",
    "rgba(255,255,255,0.6)",
    "rgba(132,204,22,0.7)",
    "rgba(245,158,11,0.7)",
  ];
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    left: `${10 + Math.random() * 80}%`,
    bottom: `${30 + Math.random() * 30}%`,
    color: colors[i % colors.length],
    delay: `${1.6 + Math.random() * 1.2}s`,
    size: 3 + Math.random() * 4,
  }));
}

// ── Component ──────────────────────────────────────────────────

export function PitchDeployment({
  agentName,
  agentEmoji,
  isBenching = false,
  onComplete,
}: PitchDeploymentProps) {
  const [closing, setClosing] = useState(false);
  const particles = useMemo(() => generateParticles(18), []);

  useEffect(() => {
    const timer = setTimeout(() => setClosing(true), isBenching ? 2000 : 3200);
    const done = setTimeout(onComplete, isBenching ? 2500 : 3800);
    return () => {
      clearTimeout(timer);
      clearTimeout(done);
    };
  }, [onComplete, isBenching]);

  return (
    <div
      className={`pitch-overlay ${closing ? "closing" : ""}`}
      role="dialog"
      aria-label={isBenching ? "Benching agent" : "Deploying agent"}
    >
      <div className="pitch-backdrop" />

      <div className="pitch-field">
        {/* Pitch markings */}
        <div className="pitch-center-line" />
        <div className="pitch-center-circle" />
        <div className="pitch-center-dot" />
        <div className="pitch-box-left" />
        <div className="pitch-box-right" />
        <div className="pitch-goal-left" />
        <div className="pitch-goal-right" />
        <div className="pitch-corner-tl" />
        <div className="pitch-corner-tr" />
        <div className="pitch-corner-bl" />
        <div className="pitch-corner-br" />

        {/* Spotlight sweep */}
        <div className="pitch-spotlight" />

        {/* Status text */}
        <div className="pitch-status">
          <div className="pitch-status-text">
            {isBenching ? "Substitution" : "Coming On"}
          </div>
          <div className="pitch-status-sub">
            {isBenching ? "Player heading to the bench" : "Entering the pitch"}
          </div>
        </div>

        {/* Player running on */}
        <div
          className={isBenching ? "pitch-player-bench" : "pitch-player"}
        >
          <div className="pitch-player-name">{agentName.toUpperCase()}</div>
          <div className="pitch-player-avatar">{agentEmoji}</div>
          <div className="pitch-player-shadow" />
        </div>

        {/* Celebration particles (deploy only) */}
        {!isBenching && (
          <div className="pitch-particles">
            {particles.map((p) => (
              <div
                key={p.id}
                className="pitch-particle"
                style={{
                  left: p.left,
                  bottom: p.bottom,
                  background: p.color,
                  animationDelay: p.delay,
                  width: p.size,
                  height: p.size,
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
