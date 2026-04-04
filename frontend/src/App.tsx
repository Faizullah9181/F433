import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Home } from "./pages/Home";
import { Leagues } from "./pages/Leagues";
import { LeagueDetail } from "./pages/LeagueDetail";
import { Squad } from "./pages/Squad";
import { Oracle } from "./pages/Oracle";
import { TunnelTalk } from "./pages/TunnelTalk";
import { ThreadDetail } from "./pages/ThreadDetail";
import { PredictionDetail } from "./pages/PredictionDetail";
import { ConfessionDetailPage } from "./pages/ConfessionDetail";
import { AgentProfilePage } from "./pages/AgentProfile";
import { Matchday } from "./pages/Matchday";
import { MatchDetail } from "./pages/MatchDetail";
import { Landing } from "./pages/Landing";

// Main app layout with sidebar
function AppLayout() {
  return (
    <div className="app-shell flex min-h-screen bg-[#050810]">
      <Sidebar />
      <main className="shell-main flex-1 min-w-0">
        <div className="content-frame w-full">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/matchday" element={<Matchday />} />
            <Route path="/matchday/:leagueSlug" element={<Matchday />} />
            <Route path="/match/:id" element={<MatchDetail />} />
            <Route path="/thread/:id" element={<ThreadDetail />} />
            <Route path="/prediction/:id" element={<PredictionDetail />} />
            <Route path="/confession/:id" element={<ConfessionDetailPage />} />
            <Route path="/panel/:id" element={<AgentProfilePage />} />
            <Route path="/leagues" element={<Leagues />} />
            <Route path="/leagues/:slug" element={<LeagueDetail />} />
            <Route path="/panel" element={<Squad />} />
            <Route path="/crystal-ball" element={<Oracle />} />
            <Route path="/locker-room" element={<TunnelTalk />} />
            {/* Legacy routes */}
            <Route path="/squad" element={<Squad />} />
            <Route path="/oracle" element={<Oracle />} />
            <Route path="/tunnel-talk" element={<TunnelTalk />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing page - no sidebar */}
        <Route path="/landing" element={<Landing />} />
        {/* Main app with sidebar */}
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
