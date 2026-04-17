import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard" },
  { key: "events", label: "Events" },
  { key: "members", label: "Members" },
  { key: "settings", label: "System Settings" },
];

const SETTINGS_BOOLEAN_FIELDS = [
  ["motion_enabled", "Motion Detection"],
  ["person_enabled", "Person Detection"],
  ["face_enabled", "Face Recognition"],
  ["snapshot_enabled", "Snapshot Capture"],
  ["clip_enabled", "Clip Recording"],
];

const SETTINGS_NUMBER_FIELDS = [
  ["motion_min_area", "Motion Min Area", 1],
  ["person_confidence", "Person Confidence", 0.1],
  ["face_confidence", "Face Confidence", 0.1],
  ["retention_days", "Retention Days", 1],
];

function getRouteFromHash() {
  const hash = window.location.hash.replace("#", "").trim();
  return NAV_ITEMS.some((item) => item.key === hash) ? hash : "dashboard";
}

async function fetchJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed for ${url}: ${response.status}`);
  }
  return response.json();
}

function Sidebar({ route, onNavigate }) {
  return (
    <aside className="w-64 bg-slate-900 p-6 border-r border-slate-800 hidden md:block">
      <h2 className="text-xl font-bold flex items-center gap-2 mb-8">
        <span className="text-blue-500">📷</span> Camera AI
      </h2>
      <nav className="space-y-3">
        {NAV_ITEMS.map((item) => {
          const isActive = route === item.key;
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => onNavigate(item.key)}
              className={`w-full text-left p-2 rounded-lg transition ${
                isActive
                  ? "text-blue-300 bg-blue-500/15 border border-blue-500/20"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}

function DashboardView({ events, members, stats, onConfirm }) {
  return (
    <>
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold">Smart Arrival Dashboard</h1>
          <p className="text-slate-400 text-sm">System Status: Optimal</p>
        </div>
        <span className="bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full text-xs font-bold border border-emerald-500/20 animate-pulse">
          ● LIVE
        </span>
      </header>

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

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
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

        <section className="bg-slate-900 rounded-2xl border border-slate-800 flex flex-col h-[600px] shadow-xl">
          <div className="p-4 border-b border-slate-800">
            <h3 className="font-bold text-slate-200">Recent Activity</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {events.length === 0 && <p className="text-slate-500 text-center py-10">No recent events</p>}
            {events.map((event) => (
              <EventCard key={event.id} event={event} members={members} onConfirm={onConfirm} />
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

function EventCard({ event, members, onConfirm }) {
  return (
    <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 hover:bg-slate-800 transition group">
      <div className="flex gap-4">
        {event.snapshot_path ? (
          <img src={`/${event.snapshot_path}`} className="w-20 h-20 object-cover rounded-md border border-slate-600 shadow-sm" alt="Event snapshot" />
        ) : (
          <div className="w-20 h-20 bg-slate-700 rounded-md flex items-center justify-center text-xs text-slate-500">No Image</div>
        )}
        <div className="flex-1">
          <div className="flex justify-between items-start gap-2">
            <span className="text-[10px] font-bold text-blue-400 uppercase tracking-tighter">
              #{event.id} {event.detection_type}
            </span>
            <span className="text-[10px] text-slate-500">{new Date(event.timestamp).toLocaleString()}</span>
          </div>
          <div className="mt-1">
            {event.metadata?.recognized_names?.length > 0 ? (
              <span className="bg-blue-500/20 text-blue-300 text-[11px] px-2 py-0.5 rounded border border-blue-500/30 font-bold">
                IDENTIFIED: {event.metadata.recognized_names[0]}
              </span>
            ) : (
              <span className="text-slate-300 text-sm font-medium">Unidentified Person</span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 mt-2">Status: {event.status}</p>

          {event.status !== "confirmed" && (
            <button
              className="mt-2 w-full bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold py-1.5 rounded transition opacity-0 group-hover:opacity-100 disabled:opacity-50"
              onClick={() => onConfirm(event)}
              disabled={!members[0]}
            >
              CONFIRM IDENTITY
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function EventsView({ events, members, unresolvedOnly, onUnresolvedToggle, onConfirm }) {
  return (
    <section>
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold">Events</h1>
          <p className="text-sm text-slate-400">Review recent detections and manually confirm unresolved identities.</p>
        </div>
        <label className="inline-flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
          <input type="checkbox" checked={unresolvedOnly} onChange={(e) => onUnresolvedToggle(e.target.checked)} />
          Show unresolved only
        </label>
      </header>

      <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
        <div className="max-h-[70vh] overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-800/80 sticky top-0">
              <tr className="text-left text-slate-300">
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Identity</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id} className="border-t border-slate-800">
                  <td className="px-4 py-3 font-mono text-blue-300">#{event.id}</td>
                  <td className="px-4 py-3 text-slate-300">{new Date(event.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-3 uppercase text-xs text-slate-400">{event.detection_type}</td>
                  <td className="px-4 py-3 text-slate-200">
                    {event.metadata?.recognized_names?.[0] || event.member_display_name || "Unknown"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        event.status === "confirmed"
                          ? "bg-emerald-500/20 text-emerald-300"
                          : "bg-amber-500/20 text-amber-300"
                      }`}
                    >
                      {event.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {event.status !== "confirmed" ? (
                      <button
                        className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-2 py-1 rounded disabled:opacity-50"
                        onClick={() => onConfirm(event)}
                        disabled={!members[0]}
                      >
                        Confirm
                      </button>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {events.length === 0 && (
                <tr>
                  <td className="px-4 py-10 text-center text-slate-500" colSpan={6}>
                    No events available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function MembersView({ members }) {
  const activeCount = useMemo(() => members.filter((member) => member.active).length, [members]);

  return (
    <section>
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Members</h1>
        <p className="text-sm text-slate-400">Active directory used for confirmations and QR/PIN matching.</p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6 mb-6">
        <div className="bg-slate-900 p-5 rounded-xl border border-slate-800">
          <p className="text-slate-400 text-sm">Total Members</p>
          <p className="text-3xl font-bold">{members.length}</p>
        </div>
        <div className="bg-slate-900 p-5 rounded-xl border border-slate-800">
          <p className="text-slate-400 text-sm">Active Members</p>
          <p className="text-3xl font-bold text-emerald-400">{activeCount}</p>
        </div>
      </div>

      <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/70">
            <tr className="text-left text-slate-300">
              <th className="px-4 py-3">Display Name</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Updated</th>
            </tr>
          </thead>
          <tbody>
            {members.map((member) => (
              <tr key={member.id} className="border-t border-slate-800">
                <td className="px-4 py-3">
                  <div className="font-semibold text-slate-100">{member.display_name || member.name}</div>
                  <div className="text-xs text-slate-400">@{member.name}</div>
                </td>
                <td className="px-4 py-3 text-slate-300">{member.role || "—"}</td>
                <td className="px-4 py-3">
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      member.active ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-700 text-slate-300"
                    }`}
                  >
                    {member.active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-400">{member.updated_at || member.created_at || "—"}</td>
              </tr>
            ))}
            {members.length === 0 && (
              <tr>
                <td className="px-4 py-10 text-center text-slate-500" colSpan={4}>
                  No members found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SettingsView({ settings, settingsSaving, onSettingsChange, onSave }) {
  return (
    <section>
      <header className="mb-6">
        <h1 className="text-2xl font-bold">System Settings</h1>
        <p className="text-sm text-slate-400">These values are loaded from and saved directly to the existing settings API.</p>
      </header>

      <div className="max-w-3xl bg-slate-900 p-6 rounded-2xl border border-slate-800 space-y-6">
        <div>
          <label className="block text-sm text-slate-300 mb-2">Profile</label>
          <input
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm"
            value={settings.profile || ""}
            onChange={(event) => onSettingsChange("profile", event.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {SETTINGS_BOOLEAN_FIELDS.map(([key, label]) => (
            <label key={key} className="flex items-center justify-between bg-slate-800/70 px-3 py-2 rounded-lg border border-slate-700">
              <span className="text-sm text-slate-200">{label}</span>
              <input
                type="checkbox"
                checked={Boolean(settings[key])}
                onChange={(event) => onSettingsChange(key, event.target.checked)}
              />
            </label>
          ))}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {SETTINGS_NUMBER_FIELDS.map(([key, label, step]) => (
            <label key={key} className="block">
              <span className="text-sm text-slate-300">{label}</span>
              <input
                type="number"
                step={step}
                className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm"
                value={settings[key] ?? ""}
                onChange={(event) => onSettingsChange(key, Number(event.target.value))}
              />
            </label>
          ))}
        </div>

        <button
          type="button"
          onClick={onSave}
          disabled={settingsSaving}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-semibold"
        >
          {settingsSaving ? "Saving..." : "Save Settings"}
        </button>
      </div>
    </section>
  );
}

function App() {
  const [route, setRoute] = useState(getRouteFromHash);
  const [events, setEvents] = useState([]);
  const [members, setMembers] = useState([]);
  const [stats, setStats] = useState({});
  const [settings, setSettings] = useState({});
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [unresolvedOnly, setUnresolvedOnly] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const navigate = (nextRoute) => {
    window.location.hash = nextRoute;
  };

  const loadDashboard = async () => {
    const [eventsResponse, membersResponse, statsResponse] = await Promise.all([
      fetchJSON("/api/events?limit=10"),
      fetchJSON("/api/members"),
      fetchJSON("/api/stats"),
    ]);
    setEvents(eventsResponse.events || []);
    setMembers(membersResponse.members || []);
    setStats(statsResponse || {});
  };

  const loadEvents = async (showUnresolvedOnly) => {
    const query = showUnresolvedOnly ? "?limit=100&unresolved=1" : "?limit=100";
    const [eventsResponse, membersResponse] = await Promise.all([
      fetchJSON(`/api/events${query}`),
      fetchJSON("/api/members"),
    ]);
    setEvents(eventsResponse.events || []);
    setMembers(membersResponse.members || []);
  };

  const loadMembers = async () => {
    const membersResponse = await fetchJSON("/api/members");
    setMembers(membersResponse.members || []);
  };

  const loadSettings = async () => {
    const settingsResponse = await fetchJSON("/api/settings");
    setSettings(settingsResponse || {});
  };

  const refreshForRoute = async () => {
    setStatusMessage("");
    try {
      if (route === "dashboard") {
        await loadDashboard();
      } else if (route === "events") {
        await loadEvents(unresolvedOnly);
      } else if (route === "members") {
        await loadMembers();
      } else if (route === "settings") {
        await loadSettings();
      }
    } catch (error) {
      console.error(`Failed to load ${route}`, error);
      setStatusMessage("Unable to load API data. Verify backend status and try again.");
    }
  };

  const confirmEvent = async (event) => {
    if (!members[0]) {
      setStatusMessage("No members available for confirmation.");
      return;
    }

    try {
      await fetchJSON(`/api/events/${event.id}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          method: "manual",
          member_id: members[0].id,
          notes: "Admin confirm",
        }),
      });
      await refreshForRoute();
    } catch (error) {
      console.error("Failed to confirm event", error);
      setStatusMessage("Failed to confirm event.");
    }
  };

  useEffect(() => {
    const onHashChange = () => setRoute(getRouteFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    refreshForRoute();

    const intervalMs = route === "settings" ? 15000 : 4000;
    const timer = setInterval(refreshForRoute, intervalMs);
    return () => clearInterval(timer);
  }, [route, unresolvedOnly]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans">
      <Sidebar route={route} onNavigate={navigate} />

      <main className="flex-1 overflow-y-auto p-8">
        <div className="md:hidden mb-6 flex flex-wrap gap-2">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => navigate(item.key)}
              className={`px-3 py-1.5 text-sm rounded ${route === item.key ? "bg-blue-600" : "bg-slate-800"}`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {statusMessage && <div className="mb-4 bg-amber-500/20 border border-amber-500/30 text-amber-200 p-3 rounded">{statusMessage}</div>}

        {route === "dashboard" && <DashboardView events={events} members={members} stats={stats} onConfirm={confirmEvent} />}

        {route === "events" && (
          <EventsView
            events={events}
            members={members}
            unresolvedOnly={unresolvedOnly}
            onUnresolvedToggle={setUnresolvedOnly}
            onConfirm={confirmEvent}
          />
        )}

        {route === "members" && <MembersView members={members} />}

        {route === "settings" && (
          <SettingsView
            settings={settings}
            settingsSaving={settingsSaving}
            onSettingsChange={(key, value) => setSettings((prev) => ({ ...prev, [key]: value }))}
            onSave={async () => {
              try {
                setSettingsSaving(true);
                const updated = await fetchJSON("/api/settings", {
                  method: "PUT",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(settings),
                });
                setSettings(updated || {});
                setStatusMessage("Settings saved successfully.");
              } catch (error) {
                console.error("Failed to save settings", error);
                setStatusMessage("Failed to save settings.");
              } finally {
                setSettingsSaving(false);
              }
            }}
          />
        )}
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
