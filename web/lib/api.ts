const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface VideoInfo {
  id: string;
  title: string;
  uploader: string;
  duration: number;
  thumbnail: string;
  resolutions: number[];
}

export interface ClipOptions {
  url: string;
  start: number;
  end: number;
  format: "mp4" | "mp3" | "gif";
  quality: number;
  title?: string;
}

export interface Progress {
  status: "queued" | "downloading" | "processing" | "done" | "error";
  progress: number;
  error: string | null;
  filename: string | null;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export function fetchInfo(url: string) {
  return postJson<VideoInfo>("/api/info", { url });
}

export function startClip(opts: ClipOptions) {
  return postJson<{ job_id: string }>("/api/clip", opts);
}

export async function getProgress(jobId: string): Promise<Progress> {
  const res = await fetch(`${API}/api/progress/${jobId}`);
  if (!res.ok) throw new Error("Could not check progress");
  return res.json();
}

export function downloadUrl(jobId: string) {
  return `${API}/api/download/${jobId}`;
}
