"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import Link from "next/link";

const PLATFORMS = [
  { value: "twitter", label: "X / Twitter" },
  { value: "instagram", label: "Instagram" },
  { value: "linkedin", label: "LinkedIn" },
];

function ResultBanner({ msg }: { msg: string }) {
  if (!msg) return null;
  const isErr = msg.toLowerCase().startsWith("error");
  return (
    <p className={`text-xs px-3 py-2 rounded ${isErr ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"}`}>
      {msg}
    </p>
  );
}

export default function GrowPage() {
  // Hashtag discovery
  const [hashPlatform, setHashPlatform] = useState("twitter");
  const [hashtag, setHashtag] = useState("");
  const [hashMax, setHashMax] = useState(20);
  const [hashLoading, setHashLoading] = useState(false);
  const [hashMsg, setHashMsg] = useState("");

  // Competitor audience
  const [audPlatform, setAudPlatform] = useState("twitter");
  const [audUrl, setAudUrl] = useState("");
  const [audSource, setAudSource] = useState("followers");
  const [audMax, setAudMax] = useState(30);
  const [audLoading, setAudLoading] = useState(false);
  const [audMsg, setAudMsg] = useState("");

  // Follow-back
  const [fbPlatforms, setFbPlatforms] = useState<string[]>(["twitter", "instagram"]);
  const [fbLoading, setFbLoading] = useState(false);
  const [fbMsg, setFbMsg] = useState("");

  // Unfollow queue
  const [unfollowDays, setUnfollowDays] = useState(30);
  const [unfollowLoading, setUnfollowLoading] = useState(false);
  const [unfollowMsg, setUnfollowMsg] = useState("");

  const toggleFbPlatform = (p: string) =>
    setFbPlatforms((prev) => prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]);

  const run = async (
    fn: () => Promise<{ added: number }>,
    setLoading: (v: boolean) => void,
    setMsg: (v: string) => void,
    label: string
  ) => {
    setLoading(true);
    setMsg("");
    try {
      const r = await fn();
      setMsg(`${r.added} ${label} added to queue`);
    } catch (e) {
      setMsg(`Error: ${e instanceof Error ? e.message : "Request failed"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-4">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-800">← Queue</Link>
        <h1 className="font-bold text-gray-900 text-lg">Grow</h1>
      </nav>

      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">

        {/* ── Hashtag Discovery ─────────────────────────────────────── */}
        <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
          <div>
            <h2 className="font-semibold text-gray-900">Hashtag Discovery</h2>
            <p className="text-xs text-gray-500 mt-0.5">Find people posting with a hashtag and add them to your follow queue.</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-600 block mb-1">Platform</label>
              <select value={hashPlatform} onChange={(e) => setHashPlatform(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                {PLATFORMS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-600 block mb-1">Max results</label>
              <input type="number" value={hashMax} min={5} max={50}
                onChange={(e) => setHashMax(Number(e.target.value))}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-600 block mb-1">Hashtag or keyword</label>
            <input
              type="text"
              placeholder="#realestate"
              value={hashtag}
              onChange={(e) => setHashtag(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
          <ResultBanner msg={hashMsg} />
          <button
            disabled={hashLoading || !hashtag.trim()}
            onClick={() => run(() => api.discoverHashtag(hashPlatform, hashtag, hashMax), setHashLoading, setHashMsg, "profiles")}
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {hashLoading ? "Scanning…" : "Find People"}
          </button>
        </section>

        {/* ── Competitor Audience ───────────────────────────────────── */}
        <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
          <div>
            <h2 className="font-semibold text-gray-900">Competitor Audience</h2>
            <p className="text-xs text-gray-500 mt-0.5">Pull the followers or following list of any public profile.</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-600 block mb-1">Platform</label>
              <select value={audPlatform} onChange={(e) => setAudPlatform(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                {PLATFORMS.filter((p) => p.value !== "linkedin").map((p) =>
                  <option key={p.value} value={p.value}>{p.label}</option>
                )}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-600 block mb-1">Source</label>
              <select value={audSource} onChange={(e) => setAudSource(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                <option value="followers">Followers</option>
                <option value="following">Following</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-600 block mb-1">Profile URL</label>
              <input
                type="url"
                placeholder="https://x.com/username"
                value={audUrl}
                onChange={(e) => setAudUrl(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-600 block mb-1">Max results</label>
              <input type="number" value={audMax} min={5} max={100}
                onChange={(e) => setAudMax(Number(e.target.value))}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>
          </div>
          <ResultBanner msg={audMsg} />
          <button
            disabled={audLoading || !audUrl.trim()}
            onClick={() => run(() => api.discoverAudience(audPlatform, audUrl, audSource, audMax), setAudLoading, setAudMsg, "profiles")}
            className="bg-purple-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 font-medium"
          >
            {audLoading ? "Scanning…" : "Pull Audience"}
          </button>
        </section>

        {/* ── Follow-Back Suggestions ───────────────────────────────── */}
        <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
          <div>
            <h2 className="font-semibold text-gray-900">Follow-Back Suggestions</h2>
            <p className="text-xs text-gray-500 mt-0.5">Find people who recently followed you and add them to your follow queue.</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            {PLATFORMS.filter((p) => p.value !== "linkedin").map((p) => (
              <button key={p.value} onClick={() => toggleFbPlatform(p.value)}
                className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                  fbPlatforms.includes(p.value)
                    ? "bg-gray-800 text-white border-gray-800"
                    : "text-gray-600 border-gray-300 hover:bg-gray-50"
                }`}>
                {p.label}
              </button>
            ))}
          </div>
          <ResultBanner msg={fbMsg} />
          <button
            disabled={fbLoading || fbPlatforms.length === 0}
            onClick={() => run(() => api.discoverFollowback(fbPlatforms), setFbLoading, setFbMsg, "follow-backs")}
            className="bg-green-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
          >
            {fbLoading ? "Scanning…" : "Find Follow-Backs"}
          </button>
        </section>

        {/* ── Unfollow Queue ────────────────────────────────────────── */}
        <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
          <div>
            <h2 className="font-semibold text-gray-900">Unfollow Queue</h2>
            <p className="text-xs text-gray-500 mt-0.5">Find people you followed through this app more than N days ago — add them to queue for review and unfollow.</p>
          </div>
          <div className="w-40">
            <label className="text-xs text-gray-600 block mb-1">Days since followed</label>
            <input type="number" value={unfollowDays} min={1} max={365}
              onChange={(e) => setUnfollowDays(Number(e.target.value))}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>
          <ResultBanner msg={unfollowMsg} />
          <button
            disabled={unfollowLoading}
            onClick={() => run(() => api.discoverUnfollow(unfollowDays), setUnfollowLoading, setUnfollowMsg, "unfollow candidates")}
            className="bg-red-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 font-medium"
          >
            {unfollowLoading ? "Finding…" : "Find Unfollow Candidates"}
          </button>
        </section>

      </div>
    </div>
  );
}
