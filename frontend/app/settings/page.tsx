"use client";

import { useEffect, useState } from "react";
import { api, Platform } from "@/lib/api";
import Link from "next/link";

const INSTRUCTIONS: Record<string, { steps: string[]; domains: string[] }> = {
  facebook: {
    domains: ["facebook.com", ".facebook.com"],
    steps: [
      "Open Facebook in Chrome and make sure you're logged in.",
      "Press F12 to open DevTools.",
      "Go to Application > Storage > Cookies > https://www.facebook.com",
      "Right-click any cookie row and choose 'Copy All'.",
      "Paste the JSON below.",
    ],
  },
  instagram: {
    domains: ["instagram.com", ".instagram.com"],
    steps: [
      "Open Instagram in Chrome and make sure you're logged in.",
      "Press F12 > Application > Cookies > https://www.instagram.com",
      "Right-click > 'Copy All', then paste below.",
    ],
  },
  linkedin: {
    domains: ["linkedin.com", ".linkedin.com"],
    steps: [
      "Open LinkedIn in Chrome and make sure you're logged in.",
      "Press F12 > Application > Cookies > https://www.linkedin.com",
      "Right-click > 'Copy All', then paste below.",
    ],
  },
  twitter: {
    domains: ["x.com", ".x.com", "twitter.com", ".twitter.com"],
    steps: [
      "Open X (Twitter) in Chrome and make sure you're logged in.",
      "Press F12 > Application > Cookies > https://x.com",
      "Right-click > 'Copy All', then paste below.",
    ],
  },
};

const PLATFORM_COLORS: Record<string, string> = {
  facebook: "bg-blue-600",
  instagram: "bg-pink-600",
  linkedin: "bg-sky-700",
  twitter: "bg-black",
};

export default function SettingsPage() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [modal, setModal] = useState<string | null>(null);
  const [cookieText, setCookieText] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const load = async () => {
    try {
      const p = await api.getPlatforms();
      setPlatforms(p);
    } catch {
      // ignore
    }
  };

  useEffect(() => { load(); }, []);

  const openModal = (platform: string) => {
    setModal(platform);
    setCookieText("");
    setMsg("");
  };

  const saveSession = async () => {
    if (!modal || !cookieText.trim()) return;
    setSaving(true); setMsg("");
    try {
      const parsed = JSON.parse(cookieText);
      const cookies = Array.isArray(parsed) ? parsed : Object.values(parsed);
      await api.importCookies(modal, cookies as object[]);
      setMsg("Connected successfully!");
      load();
    } catch (e) {
      setMsg(e instanceof Error ? `Error: ${e.message}` : "Invalid JSON — paste the full cookie export");
    } finally {
      setSaving(false);
    }
  };

  const disconnect = async (platform: string) => {
    await api.clearSession(platform);
    load();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-4">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-800">
          ← Queue
        </Link>
        <h1 className="font-bold text-gray-900 text-lg">Settings</h1>
      </nav>

      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-1">Platform Connections</h2>
          <p className="text-xs text-gray-500">
            Connect each platform by importing your browser session cookies. Nothing is stored
            except your session — no passwords.
          </p>
        </div>

        <div className="space-y-3">
          {platforms.map((p) => {
            const color = PLATFORM_COLORS[p.id] ?? "bg-gray-600";
            const connected = p.logged_in === 1;
            return (
              <div key={p.id} className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between gap-4 shadow-sm">
                <div className="flex items-center gap-3">
                  <span className={`${color} text-white text-xs font-bold w-9 h-9 rounded-lg flex items-center justify-center`}>
                    {p.id === "facebook" ? "FB" : p.id === "instagram" ? "IG" : p.id === "linkedin" ? "LI" : "X"}
                  </span>
                  <div>
                    <div className="font-medium text-sm text-gray-900">{p.display_name}</div>
                    <div className={`text-xs ${connected ? "text-green-600" : "text-gray-400"}`}>
                      {connected ? "Connected" : "Not connected"}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => openModal(p.id)}
                    className="text-xs bg-gray-800 text-white px-3 py-1.5 rounded hover:bg-gray-700"
                  >
                    {connected ? "Reconnect" : "Connect"}
                  </button>
                  {connected && (
                    <button
                      onClick={() => disconnect(p.id)}
                      className="text-xs text-red-500 border border-red-200 px-3 py-1.5 rounded hover:bg-red-50"
                    >
                      Disconnect
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-xs text-blue-800 space-y-1">
          <p className="font-semibold">Backend URL</p>
          <p>
            Set <code className="bg-blue-100 px-1 rounded">NEXT_PUBLIC_API_URL</code> in your Vercel
            environment variables to point to your Lightsail server, e.g.{" "}
            <code className="bg-blue-100 px-1 rounded">http://107.21.111.216:8096</code>
          </p>
        </div>
      </div>

      {/* Cookie import modal */}
      {modal && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 space-y-4">
            <h2 className="font-semibold text-gray-900">
              Connect {platforms.find((p) => p.id === modal)?.display_name}
            </h2>

            <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside bg-gray-50 rounded p-3">
              {(INSTRUCTIONS[modal]?.steps ?? []).map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ol>

            <div>
              <label className="text-xs text-gray-600 block mb-1">Paste cookies JSON here</label>
              <textarea
                rows={6}
                value={cookieText}
                onChange={(e) => setCookieText(e.target.value)}
                placeholder='[{"name":"c_user","value":"...","domain":".facebook.com",...}]'
                className="w-full border border-gray-300 rounded p-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>

            {msg && (
              <p className={`text-xs ${msg.startsWith("Error") ? "text-red-600" : "text-green-600"}`}>
                {msg}
              </p>
            )}

            <div className="flex gap-2">
              <button
                onClick={saveSession}
                disabled={saving || !cookieText.trim()}
                className="flex-1 bg-gray-900 text-white py-2 rounded-lg text-sm font-medium hover:bg-gray-700 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Session"}
              </button>
              <button
                onClick={() => setModal(null)}
                className="flex-1 border border-gray-300 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
