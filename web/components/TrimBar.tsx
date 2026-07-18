"use client";

import styles from "./TrimBar.module.css";

interface Props {
  max: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
}

function formatTime(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const mins = Math.floor(total / 60);
  const secs = total % 60;
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

export default function TrimBar({ max, value, onChange }: Props) {
  const [start, end] = value;
  const percent = (t: number) => (max > 0 ? (t / max) * 100 : 0);

  return (
    <div className={styles.wrap}>
      <div className={styles.track}>
        <div
          className={styles.selected}
          style={{ left: `${percent(start)}%`, right: `${100 - percent(end)}%` }}
        />
        <input
          className={styles.range}
          type="range"
          min={0}
          max={max}
          step={1}
          value={start}
          onChange={(e) => onChange([Math.min(Number(e.target.value), end - 1), end])}
        />
        <input
          className={styles.range}
          type="range"
          min={0}
          max={max}
          step={1}
          value={end}
          onChange={(e) => onChange([start, Math.max(Number(e.target.value), start + 1)])}
        />
      </div>
      <div className={styles.labels}>
        <span>{formatTime(start)}</span>
        <span className={styles.duration}>{formatTime(end - start)} selected</span>
        <span>{formatTime(end)}</span>
      </div>
    </div>
  );
}
