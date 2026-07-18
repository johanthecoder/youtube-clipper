import os
import time

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_rejects_unknown_format():
    r = client.post("/api/clip", json={"url": "x", "start": 0, "end": 5, "format": "avi"})
    assert r.status_code == 400


def test_rejects_bad_range():
    r = client.post("/api/clip", json={"url": "x", "start": 5, "end": 5, "format": "mp4"})
    assert r.status_code == 400


def test_progress_unknown_job():
    assert client.get("/api/progress/nope").status_code == 404


def test_download_unknown_job():
    assert client.get("/api/download/nope").status_code == 404


def test_clip_flow(monkeypatch):
    """Full request -> job -> download, with the heavy clip step stubbed out."""

    def fake_make_clip(url, start, end, fmt, quality, out_dir, duration=None, hook=None, pp_hook=None):
        path = os.path.join(out_dir, f"clip.{fmt}")
        with open(path, "wb") as fh:
            fh.write(b"data")
        return path

    monkeypatch.setattr(main, "make_clip", fake_make_clip)

    started = client.post(
        "/api/clip",
        json={"url": "x", "start": 0, "end": 5, "format": "mp4", "title": "My Clip"},
    )
    assert started.status_code == 200
    job_id = started.json()["job_id"]

    result = {}
    for _ in range(100):
        result = client.get(f"/api/progress/{job_id}").json()
        if result["status"] in ("done", "error"):
            break
        time.sleep(0.05)

    assert result["status"] == "done"
    assert result["filename"] == "My Clip.mp4"

    downloaded = client.get(f"/api/download/{job_id}")
    assert downloaded.status_code == 200
    assert downloaded.content == b"data"
