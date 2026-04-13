import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

function App() {
  const [events, setEvents] = useState([]);
  const [members, setMembers] = useState([]);
  const [stats, setStats] = useState({});

  const load = async () => {
    try {
      const [ev, mb, st] = await Promise.all([
        fetch("/api/events?limit=10").then((r) => r.json()),
        fetch("/api/members").then((r) => r.json()),
        fetch("/api/stats").then((r) => r.json()),
      ]);

      setEvents(ev.events || []);
      setMembers(mb.members || []);
      setStats(st || {});
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 2000); // 2-second refresh for tighter feel
    return () => clearInterval(t);
  }, []);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 p-6 border-r border-slate-800 hidden md:block">
        <h2 className="text-xl font-bold flex items-center gap-2 mb-8">
          <span className="text-blue-500">📷</span> Camera AI
        </h2>
        <nav className="space-y-4">
          <div className="text-blue-400 bg-blue-500/10 p-2 rounded-lg cursor-pointer">Dashboard</div>
          <div className="text-slate-400 hover:text-white p-2 transition cursor-pointer">Events</div>
          <div className="text-slate-400 hover:text-white p-2 transition cursor-pointer">Members</div>
          <div className="text-slate-400 hover:text-white p-2 transition cursor-pointer">System Settings</div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        {/* Top Header */}
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold">Smart Arrival Dashboard</h1>
            <p className="text-slate-400 text-sm">System Status: Optimal</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full text-xs font-bold border border-emerald-500/20 animate-pulse">
              ● LIVE
            </span>
          </div>
        </header>

        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
            <p className="text-slate-400 text-sm mb-1">Total Events</p>
            <p className="text-3xl font-mono font-bold">{stats.total_events || 0}</p>
          </div>
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
            <p className="text-slate-400 text-sm mb-1">Pending Review</p>
            <p className="text-3xl font-mono font-bold text-orange-400">{stats.pending_events || 0}</p>
          </div>
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
            <p className="text-slate-400 text-sm mb-1">Authenticated</p>
            <p className="text-3xl font-mono font-bold text-emerald-400">{stats.confirmed_events || 0}</p>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Live Feed Column */}
          <div className="xl:col-span-2 space-y-6">
            <section className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl">
              <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                <h3 className="font-bold">Primary Camera View</h3>
                <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Pi5 Ribbon Cam</span>
              </div>
              <div className="relative aspect-video bg-black">
                <img src="/api/stream" className="w-full h-full object-cover" alt="Stream" />
              </div>
            </section>
          </div>

          {/* Activity Sidebar */}
          <section className="bg-slate-900 rounded-2xl border border-slate-800 flex flex-col h-[600px] shadow-xl">
            <div className="p-4 border-b border-slate-800">
              <h3 className="font-bold text-slate-200">Recent Activity</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {events.length === 0 && <p className="text-slate-500 text-center py-10">No recent events</p>}
              {events.map((e) => (
                <div key={e.id} className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 hover:bg-slate-800 transition group">
                  <div className="flex gap-4">
                    {e.snapshot_path ? (
                      <img src={`/${e.snapshot_path}`} className="w-20 h-20 object-cover rounded-md border border-slate-600 shadow-sm" />
                    ) : (
                      <div className="w-20 h-20 bg-slate-700 rounded-md flex items-center justify-center text-xs text-slate-500">No Image</div>
                    )}
                    <div className="flex-1">
                      <div className="flex justify-between items-start">
                        <span className="text-[10px] font-bold text-blue-400 uppercase tracking-tighter">#{e.id} {e.detection_type}</span>
                        <span className="text-[10px] text-slate-500">{new Date(e.timestamp).toLocaleTimeString()}</span>
                      </div>
                      
                      {/* Show the Biometric Identity if it exists in metadata */}
                      <div className="mt-1">
                        {e.metadata?.recognized_names?.length > 0 ? (
                          <span className="bg-blue-500/20 text-blue-300 text-[11px] px-2 py-0.5 rounded border border-blue-500/30 font-bold">
                            IDENTIFIED: {e.metadata.recognized_names[0]}
                          </span>
                        ) : (
                          <span className="text-slate-300 text-sm font-medium">Unidentified Person</span>
                        )}
                      </div>

                      {e.status !== "confirmed" && (
                        <button
                          className="mt-2 w-full bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold py-1.5 rounded transition opacity-0 group-hover:opacity-100"
                          onClick={async () => {
                            if (!members[0]) return;
                            await fetch(`/api/events/${e.id}/confirm`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                method: "manual",
                                member_id: members[0].id,
                                notes: "Admin confirm",
                              }),
                            });
                            load();
                          }}
                        >
                          CONFIRM IDENTITY
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
