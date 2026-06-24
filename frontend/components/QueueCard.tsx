"use client";

import { useState } from "react";
import { api, QueueItem } from "@/lib/api";

const PLATFORM_COLORS: Record<string, string> = {
  facebook: "bg-blue-600",
  instagram: "bg-pink-600",
  linkedin: "bg-sky-700",
  twitter: "bg-black",
};

const PLATFORM_LABELS: Record<string, string> = {
  facebook: "FB",
  instagram: "IG",
  linkedin: "LI",
  twitter: "X",
};

const TYPE_LABELS: Record<string, string> = {
  birthday: "Birthday",
  reply: "Reply",
  follow: "Follow",
};

interface Props {
  item: QueueItem;
  onUpdate: () => void;
}

export default function QueueCard({ item, onUpdate }: Props) {
  const [draft, setDraft] = useState(item.draft_message ?? "");
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const run = async (fn: () => Promise<unknown>) => {
    setLoading(true);
    setError("");
    try {
      await fn();
      onUpdate();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const saveDraft = () => run(() => api.updateDraft(item.id, draft));
  const approve = () => run(() => api.approve(item.id));
  const reject = () => run(() => api.reject(item.id));
  const postNow = () => run(() => api.post(item.id));

  const platformColor = PLATFORM_COLORS[item.platform] ?? "bg-gray-600";
  const platformLabel = PLATFORM_LABELS[item.platform] ?? item.platform;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`${platformColor} text-white text-xs font-bold px-2 py-0.5 rounded`}>
            {platformLabel}
          </span>
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
            {TYPE_LABELS[item.type] ?? item.type}
          </span>
          {item.target_name && (
            <span className="font-semibold text-gray-900 text-sm">{item.target_name}</span>
          )}
        </div>
        <span className="text-xs text-gray-400 whitespace-nowrap">
          {new Date(item.created_at).toLocaleDateString()}
        </span>
      </div>

      {/* Original post (reply type) */}
      {item.post_content && (
        <div className="text-xs text-gray-500 bg-gray-50 border-l-2 border-gray-300 pl-3 py-1 italic line-clamp-3">
          {item.post_content}
        </div>
      )}

      {/* Draft message */}
      {item.type !== "follow" && (
        <div>
          {editing ? (
            <div className="space-y-2">
              <textarea
                className="w-full text-sm border border-gray-300 rounded p-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
                rows={3}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
              />
              <div className="flex gap-2">
                <button
                  onClick={() => { saveDraft(); setEditing(false); }}
                  disabled={loading}
                  className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  Save
                </button>
                <button
                  onClick={() => { setDraft(item.draft_message ?? ""); setEditing(false); }}
                  className="text-xs text-gray-500 px-3 py-1 rounded border hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div
              className="text-sm text-gray-800 bg-blue-50 border border-blue-100 rounded p-3 cursor-pointer hover:bg-blue-100 transition-colors"
              onClick={() => setEditing(true)}
              title="Click to edit"
            >
              {draft || <span className="text-gray-400 italic">No draft yet</span>}
            </div>
          )}
        </div>
      )}

      {/* Profile URL (follow type) */}
      {item.type === "follow" && item.target_profile_url && (
        <div className="text-xs text-gray-600 break-all">
          <a href={item.target_profile_url} target="_blank" rel="noopener noreferrer"
            className="text-blue-600 hover:underline">
            {item.target_profile_url}
          </a>
        </div>
      )}

      {error && <p className="text-xs text-red-600">{error}</p>}

      {/* Actions */}
      {item.status === "pending" && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={approve}
            disabled={loading}
            className="text-xs bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700 disabled:opacity-50 font-medium"
          >
            Approve
          </button>
          <button
            onClick={postNow}
            disabled={loading}
            className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded hover:bg-indigo-700 disabled:opacity-50 font-medium"
          >
            Post Now
          </button>
          {!editing && (
            <button
              onClick={() => setEditing(true)}
              className="text-xs text-gray-600 px-3 py-1.5 rounded border hover:bg-gray-50"
            >
              Edit
            </button>
          )}
          <button
            onClick={reject}
            disabled={loading}
            className="text-xs text-red-600 px-3 py-1.5 rounded border border-red-200 hover:bg-red-50"
          >
            Reject
          </button>
        </div>
      )}
      {item.status === "approved" && (
        <div className="flex gap-2 items-center">
          <span className="text-xs text-green-700 bg-green-100 px-2 py-1 rounded font-medium">Approved</span>
          <button
            onClick={postNow}
            disabled={loading}
            className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded hover:bg-indigo-700 disabled:opacity-50"
          >
            Post Now
          </button>
        </div>
      )}
      {item.status === "posted" && (
        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
          Posted {item.posted_at ? new Date(item.posted_at).toLocaleDateString() : ""}
        </span>
      )}
      {item.status === "rejected" && (
        <span className="text-xs text-red-500 bg-red-50 px-2 py-1 rounded">Rejected</span>
      )}
    </div>
  );
}
