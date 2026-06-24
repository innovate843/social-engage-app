const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8096";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export type QueueStatus = "pending" | "approved" | "posted" | "rejected";
export type QueueType = "birthday" | "reply" | "follow";

export interface QueueItem {
  id: number;
  type: QueueType;
  platform: string;
  target_name: string | null;
  target_profile_url: string | null;
  post_url: string | null;
  post_content: string | null;
  draft_message: string | null;
  status: QueueStatus;
  created_at: string;
  posted_at: string | null;
}

export interface Platform {
  id: string;
  display_name: string;
  logged_in: number;
  last_checked: string | null;
}

export const api = {
  // Queue
  getQueue: (status?: QueueStatus, type?: QueueType) => {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (type) params.set("type", type);
    return req<QueueItem[]>(`/queue?${params}`);
  },
  updateDraft: (id: number, draft_message: string) =>
    req(`/queue/${id}`, { method: "PATCH", body: JSON.stringify({ draft_message }) }),
  approve: (id: number) => req(`/queue/${id}/approve`, { method: "POST" }),
  reject: (id: number) => req(`/queue/${id}/reject`, { method: "POST" }),
  post: (id: number) => req(`/queue/${id}/post`, { method: "POST" }),

  // Platforms
  getPlatforms: () => req<Platform[]>("/platforms"),
  importCookies: (platform: string, cookies: object[]) =>
    req(`/platforms/${platform}/cookies`, {
      method: "POST",
      body: JSON.stringify({ cookies }),
    }),
  clearSession: (platform: string) =>
    req(`/platforms/${platform}/session`, { method: "DELETE" }),

  // Scans
  scanBirthdays: () => req("/scan/birthdays", { method: "POST" }),
  scanFeed: (platforms?: string[]) =>
    req("/scan/feed", { method: "POST", body: JSON.stringify({ platforms }) }),

  // Manual adds
  addFollow: (platform: string, name: string, profile_url: string) =>
    req("/follow", { method: "POST", body: JSON.stringify({ platform, name, profile_url }) }),
  addBirthday: (data: {
    name: string;
    platform: string;
    profile_url: string;
    birthday_month: number;
    birthday_day: number;
  }) => req("/birthday", { method: "POST", body: JSON.stringify(data) }),
};
