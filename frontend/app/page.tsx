"use client";

import { useCallback, useEffect, useState } from "react";
import { api, QueueItem, QueueStatus, QueueType } from "@/lib/api";
import QueueCard from "@/components/QueueCard";
import Link from "next/link";

const STATUS_TABS: { label: string; value: QueueStatus }[] = [
  { label: "Pending", value: "pending" },
  { label: "Approved", value: "approved" },
  { label: "Posted", value: "posted" },
  { label: "Rejected", value: "rejected" },
];

const TYPE_FILTERS: { label: string; value: QueueType | "" }[] = [
  { label: "All", value: "" },
  { label: "Birthdays", value: "birthday" },
  { label: "Replies", value: "reply" },
  { label: "Follows", value: "follow" },
  { label: "Unfollow", value: "unfollow" },
];

export default function DashboardPage() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [status, setStatus] = useState<QueueStatus>("pending");
  const [typeFilter, setTypeFilter] = useState<QueueType | "">("");
  const [platformFilter, setPlatformFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState("");
  const [showFollowModal, setShowFollowModal] = useState(false);
  const [followPlatform, setFollowPlatform] = useState("facebook");
  const [followName, setFollowName] = useState("");
  const [followUrl, setFollowUrl] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getQueue(status, typeFilter || undefined);
      setItems(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [status, typeFilter]);

  useEffect(() => { load(); }, [load]);

  const scanBirthdays = async () => {
    setScanning(true); setScanMsg("");
    try {
      const r = await api.scanBirthdays() as { added: number };
      setScanMsg(`${r.added} birthday item(s) added to queue`);
      load();
    } catch (e) {
      setScanMsg(e instanceof Error ? e.message : "Scan failed");
    } finally { setScanning(false); }
  };

  const scanFeed = async () => {
    setScanning(true); setScanMsg("");
    try {
      const r = await api.scanFeed() as { added: number };
      setScanMsg(`${r.added} reply item(s) added to queue`);
      load();
    } catch (e) {
      setScanMsg(e instanceof Error ? e.message : "Scan failed");
    } finally { setScanning(false); }
  };

  const addFollow = async () => {
    if (!followName || !followUrl) return;
    await api.addFollow(followPlatform, followName, followUrl);
    setShowFollowModal(false);
    setFollowName(""); setFollowUrl("");
    load();
  };

  const byType = (t: QueueType) => items.filter((i) => i.type === t).length;
  const visibleItems = platformFilter ? items.filter((i) => i.platform === platformFilter) : items;

  const PLATFORM_FILTERS = [
    { label: "All", value: "" },
    { label: "FB", value: "facebook" },
    { label: "IG", value: "instagram" },
    { label: "LI", value: "linkedin" },
    { label: "X", value: "twitter" },
  ];

  const PLATFORM_COLORS: Record<string, string> = {
    facebook: "bg-blue-600",
    instagram: "bg-pink-600",
    linkedin: "bg-sky-700",
    twitter: "bg-black",
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <h1 className="font-bold text-gray-900 text-lg">Social Engage</h1>
        <div className="flex gap-4">
          <Link href="/grow" className="text-sm text-gray-500 hover:text-gray-800">Grow</Link>
          <Link href="/settings" className="text-sm text-gray-500 hover:text-gray-800">Settings</Link>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Birthdays", count: byType("birthday"), color: "text-yellow-600" },
            { label: "Replies", count: byType("reply"), color: "text-blue-600" },
            { label: "Follows", count: byType("follow"), color: "text-green-600" },
          ].map(({ label, count, color }) => (
            <div key={label} className="bg-white border border-gray-200 rounded-lg p-4 text-center shadow-sm">
              <div className={`text-2xl font-bold ${color}`}>{count}</div>
              <div className="text-xs text-gray-500 mt-1">{label}</div>
            </div>
          ))}
        </div>

        <div className="flex gap-2 flex-wrap">
          <button onClick={scanBirthdays} disabled={scanning}
            className="text-sm bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 disabled:opacity-50 font-medium">
            Scan Birthdays
          </button>
          <button onClick={scanFeed} disabled={scanning}
            className="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">
            Scan Feed
          </button>
          <button onClick={() => setShowFollowModal(true)}
            className="text-sm bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium">
            + Add Follow
          </button>
        </div>

        {scanMsg && <p className="text-sm text-gray-600 bg-gray-100 px-3 py-2 rounded">{scanMsg}</p>}

        <div className="flex gap-1 border-b border-gray-200">
          {STATUS_TABS.map((t) => (
            <button key={t.value} onClick={() => setStatus(t.value)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                status === t.value
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}>
              {t.label}
            </button>
          ))}
        </div>

        <div className="flex gap-2 flex-wrap items-center">
          <div className="flex gap-1.5 flex-wrap">
            {TYPE_FILTERS.map((f) => (
              <button key={f.value} onClick={() => setTypeFilter(f.value)}
                className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                  typeFilter === f.value
                    ? "bg-gray-800 text-white border-gray-800"
                    : "text-gray-600 border-gray-300 hover:bg-gray-50"
                }`}>
                {f.label}
              </button>
            ))}
          </div>
          <div className="w-px h-4 bg-gray-300" />
          <div className="flex gap-1.5 flex-wrap">
            {PLATFORM_FILTERS.map((f) => (
              <button key={f.value} onClick={() => setPlatformFilter(f.value)}
                className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
                  platformFilter === f.value
                    ? f.value
                      ? `${PLATFORM_COLORS[f.value]} text-white border-transparent`
                      : "bg-gray-800 text-white border-gray-800"
                    : "text-gray-600 border-gray-300 hover:bg-gray-50"
                }`}>
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-gray-400 text-center py-10">Loading...</p>
        ) : visibleItems.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-10">No items in this queue.</p>
        ) : (
          <div className="space-y-3">
            {visibleItems.map((item) => <QueueCard key={item.id} item={item} onUpdate={load} />)}
          </div>
        )}
      </div>

      {showFollowModal && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <h2 className="font-semibold text-gray-900">Add to Follow Queue</h2>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-600 block mb-1">Platform</label>
                <select value={followPlatform} onChange={(e) => setFollowPlatform(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                  <option value="facebook">Facebook</option>
                  <option value="instagram">Instagram</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="twitter">X / Twitter</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-600 block mb-1">Name</label>
                <input type="text" value={followName} onChange={(e) => setFollowName(e.target.value)}
                  placeholder="John Smith"
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-gray-600 block mb-1">Profile URL</label>
                <input type="url" value={followUrl} onChange={(e) => setFollowUrl(e.target.value)}
                  placeholder="https://facebook.com/johnsmith"
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={addFollow}
                className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-green-700">
                Add to Queue
              </button>
              <button onClick={() => setShowFollowModal(false)}
                className="flex-1 border border-gray-300 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
