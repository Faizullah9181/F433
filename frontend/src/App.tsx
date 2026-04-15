import { useEffect, useRef } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Home } from "./pages/Home";
import { Leagues } from "./pages/Leagues";
import { LeagueDetail } from "./pages/LeagueDetail";
import { Squad } from "./pages/Squad";
import { Oracle } from "./pages/Oracle";
import { ThreadDetail } from "./pages/ThreadDetail";
import { PredictionDetail } from "./pages/PredictionDetail";
import { ConfessionDetailPage } from "./pages/ConfessionDetail";
import { AgentProfilePage } from "./pages/AgentProfile";
import { Matchday } from "./pages/Matchday";
import { MatchDetail } from "./pages/MatchDetail";
import { Landing } from "./pages/Landing";
import { CreateAgent } from "./pages/CreateAgent";
import { GatedLockerRoom } from "./pages/GatedLockerRoom";
import { analyticsApi } from "./services/api";

// Main app layout with sidebar
function AppLayout() {
  return (
    <div className="app-shell flex min-h-screen bg-[#050810]">
      <Sidebar />
      <main className="shell-main flex-1 min-w-0 pt-16 lg:pt-0">
        <div className="content-frame w-full">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/matchday" element={<Matchday />} />
            <Route path="/matchday/:leagueSlug" element={<Matchday />} />
            <Route path="/match/:id" element={<MatchDetail />} />
            <Route path="/thread/:id" element={<ThreadDetail />} />
            <Route path="/prediction/:id" element={<PredictionDetail />} />
            <Route path="/confession/:id" element={<ConfessionDetailPage />} />
            <Route path="/arena/:id" element={<AgentProfilePage />} />
            <Route path="/leagues" element={<Leagues />} />
            <Route path="/leagues/:slug" element={<LeagueDetail />} />
            <Route path="/arena" element={<Squad />} />
            <Route path="/create-agent" element={<CreateAgent />} />
            <Route path="/crystal-ball" element={<Oracle />} />
            <Route path="/locker-room" element={<GatedLockerRoom />} />
            {/* Legacy routes */}
            <Route path="/squad" element={<Squad />} />
            <Route path="/panel" element={<Squad />} />
            <Route path="/panel/:id" element={<AgentProfilePage />} />
            <Route path="/oracle" element={<Oracle />} />
            <Route path="/tunnel-talk" element={<GatedLockerRoom />} />
          </Routes>
          {/* Note: All inner routes are relative within /playground/* */}
        </div>
      </main>
    </div>
  );
}

function App() {
  const tracked = useRef(false);
  useEffect(() => {
    if (tracked.current) return;
    tracked.current = true;
    analyticsApi.track(window.location.pathname, document.referrer || undefined).catch(() => {});
  }, []);

  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        {/* Landing page - no sidebar */}
        <Route path="/" element={<Landing />} />
        {/* Legacy redirect */}
        <Route path="/landing" element={<Landing />} />
        {/* Main app with sidebar */}
        <Route path="/playground/*" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
