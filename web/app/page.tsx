"use client";

import { useEffect, useRef, useState } from "react";
import TrimBar from "@/components/TrimBar";
import {
  ClipOptions,
  Progress,
  VideoInfo,
  downloadUrl,
  fetchInfo,
  getProgress,
  startClip,
} from "@/lib/api";
import styles from "./page.module.css";

type Format = ClipOptions["format"];

export default function Home() {
  const [url, setUrl] = useState("");
  const [info, setInfo] = useState<VideoInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [range, setRange] = useState<[number, number]>([0, 0]);
  const [format, setFormat] = useState<Format>("mp4");
  const [quality, setQuality] = useState(1080);

  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<Progress | null>(null);
  const poller = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (poller.current) clearInterval(poller.current);
    };
  }, []);

  async function loadVideo() {
    const trimmed = url.trim();
    if (!trimmed) return;
    setError(null);
    setInfo(null);
    setJob(null);
    setJobId(null);
    setLoading(true);
    try {
      const data = await fetchInfo(trimmed);
      setInfo(data);
      setRange([0, Math.min(30, data.duration || 0)]);
      setQuality(data.resolutions[0] ?? 1080);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load that video");
    } finally {
      setLoading(false);
    }
  }

  async function createClip() {
    if (!info) return;
    setError(null);
    setJob({ status: "queued", progress: 0, error: null, filename: null });
    try {
      const { job_id } = await startClip({
        url: url.trim(),
        start: range[0],
        end: range[1],
        format,
        quality,
        title: info.title,
      });
      setJobId(job_id);
      if (poller.current) clearInterval(poller.current);
      poller.current = setInterval(() => checkProgress(job_id), 800);
    } catch (e) {
      setJob(null);
      setError(e instanceof Error ? e.message : "Could not start the clip");
    }
  }

  async function checkProgress(id: string) {
    try {
      const p = await getProgress(id);
      setJob(p);
      if (p.status === "done" || p.status === "error") {
        if (poller.current) clearInterval(poller.current);
        if (p.status === "error") setError(p.error ?? "Something went wrong");
      }
    } catch {
      // transient error, keep polling
    }
  }

  const busy = job !== null && job.status !== "done" && job.status !== "error";
  const percent = Math.round((job?.progress ?? 0) * 100);

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1>youtube-clipper</h1>
        <p>Trim a section of a video and save it as MP4, MP3 or GIF.</p>
      </header>

      <div className={styles.searchRow}>
        <input
          className={styles.input}
          type="text"
          placeholder="Paste a YouTube link"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && loadVideo()}
        />
        <button className={styles.button} onClick={loadVideo} disabled={loading}>
          {loading ? "Loading…" : "Load"}
        </button>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {info && (
        <section className={styles.card}>
          <div className={styles.meta}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img className={styles.thumb} src={info.thumbnail} alt="" />
            <div>
              <h2 className={styles.title}>{info.title}</h2>
              <p className={styles.uploader}>{info.uploader}</p>
            </div>
          </div>

          <TrimBar max={info.duration || 0} value={range} onChange={setRange} />

          <div className={styles.controls}>
            <label className={styles.field}>
              <span>Format</span>
              <select value={format} onChange={(e) => setFormat(e.target.value as Format)}>
                <option value="mp4">MP4 video</option>
                <option value="mp3">MP3 audio</option>
                <option value="gif">GIF</option>
              </select>
            </label>

            {format !== "mp3" && (
              <label className={styles.field}>
                <span>Quality</span>
                <select value={quality} onChange={(e) => setQuality(Number(e.target.value))}>
                  {info.resolutions.map((r) => (
                    <option key={r} value={r}>
                      {r}p
                    </option>
                  ))}
                </select>
              </label>
            )}

            <button className={styles.primary} onClick={createClip} disabled={busy}>
              {busy ? "Working…" : "Create clip"}
            </button>
          </div>

          {job && (
            <div className={styles.progress}>
              {job.status !== "done" ? (
                <>
                  <div className={styles.bar}>
                    <div className={styles.fill} style={{ width: `${percent}%` }} />
                  </div>
                  <span className={styles.status}>
                    {job.status === "downloading"
                      ? `Downloading ${percent}%`
                      : job.status === "processing"
                        ? "Converting…"
                        : "Starting…"}
                  </span>
                </>
              ) : (
                jobId && (
                  <a className={styles.download} href={downloadUrl(jobId)}>
                    Download {job.filename}
                  </a>
                )
              )}
            </div>
          )}
        </section>
      )}

      <footer className={styles.footer}>
        For content you own or have permission to use.
      </footer>
    </main>
  );
}
