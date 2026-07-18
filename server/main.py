"""FastAPI backend for youtube-clipper."""

import os
import re
import tempfile
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from clipper import get_info, make_clip
from jobs import store

app = FastAPI(title="youtube-clipper")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EXT = {"mp4": "mp4", "mp3": "mp3", "gif": "gif"}


class InfoRequest(BaseModel):
    url: str


class ClipRequest(BaseModel):
    url: str
    start: float
    end: float
    format: str = "mp4"
    quality: int = 1080
    title: str | None = None
    duration: float | None = None


def safe_name(title: str | None, ext: str) -> str:
    name = re.sub(r"[^\w\- ]+", "", title or "clip").strip() or "clip"
    return f"{name[:80]}.{ext}"


@app.post("/api/info")
def info(req: InfoRequest):
    try:
        return get_info(req.url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/clip")
def clip(req: ClipRequest):
    if req.format not in EXT:
        raise HTTPException(status_code=400, detail="format must be mp4, mp3 or gif")
    if req.end <= req.start:
        raise HTTPException(status_code=400, detail="end must be after start")

    store.cleanup()
    job = store.create()
    workdir = tempfile.mkdtemp(prefix="clip_")
    threading.Thread(target=_run, args=(job.id, req, workdir), daemon=True).start()
    return {"job_id": job.id}


def _run(job_id: str, req: ClipRequest, workdir: str):
    # Show activity immediately, even before yt-dlp reports its first bytes.
    store.update(job_id, status="downloading")

    def on_progress(status):
        state = status.get("status")
        if state == "downloading":
            total = status.get("total_bytes") or status.get("total_bytes_estimate")
            downloaded = status.get("downloaded_bytes", 0)
            fraction = downloaded / total if total else 0.0
            store.update(
                job_id,
                status="downloading",
                progress=fraction,
                downloaded=downloaded,
                total=total,
            )
        elif state == "finished":
            store.update(job_id, status="processing")

    def on_postprocess(status):
        if status.get("status") == "started":
            store.update(job_id, status="processing")

    try:
        path = make_clip(
            req.url,
            req.start,
            req.end,
            req.format,
            req.quality,
            workdir,
            duration=req.duration,
            hook=on_progress,
            pp_hook=on_postprocess,
        )
        store.update(
            job_id,
            status="done",
            progress=1.0,
            file=path,
            filename=safe_name(req.title, EXT[req.format]),
        )
    except Exception as exc:
        store.update(job_id, status="error", error=str(exc))


@app.get("/api/progress/{job_id}")
def progress(job_id: str):
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="unknown job")
    return {
        "status": job.status,
        "progress": round(job.progress, 3),
        "downloaded": job.downloaded,
        "total": job.total,
        "error": job.error,
        "filename": job.filename,
    }


@app.get("/api/download/{job_id}")
def download(job_id: str):
    job = store.get(job_id)
    if not job or job.status != "done" or not job.file:
        raise HTTPException(status_code=404, detail="clip not ready")
    return FileResponse(job.file, filename=job.filename, media_type="application/octet-stream")
