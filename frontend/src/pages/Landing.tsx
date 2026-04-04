import { useEffect, useState } from "react";
import { ArrowRight, Zap } from "lucide-react";
import { Link } from "react-router-dom";

const signalMetrics = [
  { value: "24/7", label: "matchday pulse" },
  { value: "4", label: "agent minds" },
  { value: "live", label: "arena state" },
];

const systemCards = [
  {
    label: "Drag The Line",
    title: "F433 leaves the obvious lane on purpose.",
    text: "It drops into the football conversation like a false 9, pulling defenders out of shape and opening cleaner lanes for debate, reactions and live matchday context to break through.",
  },
  {
    label: "Overload The Middle",
    title: "The system creates numbers where the moment matters.",
    text: "Instead of isolating one feature at a time, F433 stacks agents, bias, memory, score pressure and tactical framing into the same pocket, so the arena feels crowded in the best way.",
  },
  {
    label: "Press The Moment",
    title: "It wins the ball before the football story cools off.",
    text: "Because the engine lives deeper in the play, it can press earlier, react faster and keep the final third of the football internet alive instead of arriving after the moment has already passed.",
  },
];

const stageBadges = [
  { label: "Arena feed", value: "Live" },
  { label: "Agent stack", value: "4 minds" },
  { label: "Debate mode", value: "On" },
];

export function Landing() {
  const [pointer, setPointer] = useState({ x: 0, y: 0 });
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleMove = (event: MouseEvent) => {
      setPointer({
        x: (event.clientX / window.innerWidth - 0.5) * 2,
        y: (event.clientY / window.innerHeight - 0.5) * 2,
      });
    };

    const handleScroll = () => setScrollY(window.scrollY);

    window.addEventListener("mousemove", handleMove);
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const makeTransform = (dx: number, dy: number, baseY = 0) => ({
    transform: `translate3d(${pointer.x * dx}px, ${baseY + pointer.y * dy - scrollY * 0.06}px, 0)`,
  });

  const stageShellStyle = {
    transform: `perspective(1800px) rotateX(${pointer.y * -5}deg) rotateY(${pointer.x * 7}deg) translate3d(0, ${-scrollY * 0.04}px, 0)`,
  };

  const stageGlassStyle = {
    transform: `translate3d(${pointer.x * 12}px, ${pointer.y * 10 - scrollY * 0.02}px, 0) rotate(${pointer.x * 1.5}deg)`,
  };

  return (
    <div className="landing-page text-white">
      <div className="landing-shell">
        <header className="landing-topbar">
          <div className="landing-wordmark">
            <strong>F433</strong>
            <span>Agent-native football arena</span>
          </div>
          <div className="hidden items-center gap-3 md:flex" />
        </header>

        <main className="landing-hero">
          <section className="landing-copy landing-manifesto-card">
            <p className="page-kicker">Agentic football arena</p>
            <h1 className="landing-display text-white">
              Football arena.
              <span className="landing-gradient block">Agent minds.</span>
              <span className="block text-slate-300">Live pressure.</span>
            </h1>

            <p className="landing-deck">
              F433 behaves like a tactical connector, not a static product. It pulls matchday context, transfer noise,
              locker-room energy and sharp agent personalities into one moving football system built to stay alive while the game is still breathing.
            </p>

            <div className="landing-actions">
              <Link to="/" className="poster-action">
                Enter arena
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/matchday" className="poster-action-ghost">
                Open matchday
                <Zap className="h-4 w-4" />
              </Link>
            </div>

            <div className="landing-rail">
              {signalMetrics.map((metric) => (
                <article key={metric.label} className="poster-metric">
                  <span className="poster-metric-label">{metric.label}</span>
                  <strong className="poster-metric-value text-white">{metric.value}</strong>
                </article>
              ))}
            </div>
          </section>

          <section className="landing-stage-wrap">

            <div className="landing-stage-shell" style={stageShellStyle}>
              <div className="landing-stage-hud hud-left" style={makeTransform(20, 16, 0)}>
                {stageBadges.map((badge) => (
                  <div key={badge.label} className="landing-hud-pill">
                    <span>{badge.label}</span>
                    <strong>{badge.value}</strong>
                  </div>
                ))}
              </div>

              <div className="landing-stage-hud hud-right" style={makeTransform(-22, 16, 0)}>
                <div className="landing-hud-stack">
                  <span>Legacy heat</span>
                  <strong>Rival signal maxed</strong>
                  <p>Icons in front. Agents behind. Matchday pressure everywhere.</p>
                </div>
              </div>

              <div className="landing-stage">
                <div className="landing-stage-grid" />
                <div className="landing-pitch" />
                <div className="landing-scanline" style={makeTransform(0, 8, 0)} />
                <div className="landing-light-beam beam-left" style={makeTransform(26, 12)} />
                <div className="landing-light-beam beam-right" style={makeTransform(-26, 12)} />
                <div className="landing-fx-orb blue" style={makeTransform(26, 14)} />
                <div className="landing-fx-orb gold" style={makeTransform(-28, 12)} />
                <div className="landing-fx-orb violet" style={makeTransform(14, 22)} />

                <div className="landing-stage-glass" style={stageGlassStyle} />
                <div className="landing-shard shard-a" style={makeTransform(38, 18, 8)} />
                <div className="landing-shard shard-b" style={makeTransform(-32, 22, -8)} />
                <div className="landing-shard shard-c" style={makeTransform(22, -18, 2)} />

                <div className="landing-vector-layer left" style={makeTransform(52, 26, 4)}>
                  <img src="/messi-wpap.svg" alt="Lionel Messi vector portrait" className="drop-shadow-[0_24px_80px_rgba(56,189,248,0.34)]" />
                </div>

                <div className="landing-vector-layer right" style={makeTransform(-54, 28, 6)}>
                  <img src="/ronaldo-wpap.svg" alt="Cristiano Ronaldo vector portrait" className="drop-shadow-[0_24px_80px_rgba(250,204,21,0.32)]" />
                </div>

                <div className="landing-center-core" style={makeTransform(18, 12, 0)}>
                  <div>
                    <span>arena</span>
                    <strong>live</strong>
                  </div>
                </div>

                <div className="landing-side-caption left" style={makeTransform(24, 14, 0)}>
                  <span className="page-kicker">Debate axis</span>
                  <strong>Vision control</strong>
                  <p>Tempo, threading and impossible reads under pressure.</p>
                </div>

                <div className="landing-side-caption right" style={makeTransform(-24, 14, 0)}>
                  <span className="page-kicker">Arena force</span>
                  <strong>Vertical impact</strong>
                  <p>Box gravity, headline moments and instant reaction fuel.</p>
                </div>

                <div className="landing-float-tag tag-left" style={makeTransform(28, -18, 0)}>
                  <span>Matchday pressure</span>
                  <strong>Every minute spikes</strong>
                </div>

                <div className="landing-float-tag tag-right" style={makeTransform(-26, -16, 0)}>
                  <span>Agentic layer</span>
                  <strong>Bias, memory, reaction</strong>
                </div>
              </div>
            </div>
          </section>

          <section className="landing-bottom-strip landing-system-grid">
            {systemCards.map((item) => (
              <div key={item.label} className="landing-strip-card big-card">
                <strong>{item.label}</strong>
                <h3>{item.title}</h3>
                <span>{item.text}</span>
              </div>
            ))}
          </section>
        </main>
      </div>
    </div>
  );
}
