"""In-memory registry of clip jobs. Fine for a single-process dev server."""

import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Job:
    id: str
    status: str = "queued"  # queued, downloading, processing, done, error
    progress: float = 0.0
    downloaded: int = 0
    total: int | None = None
    file: str | None = None
    filename: str | None = None
    error: str | None = None
    created: float = field(default_factory=time.time)


class JobStore:
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self) -> Job:
        job = Job(id=uuid.uuid4().hex[:12])
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for key, value in fields.items():
                setattr(job, key, value)

    def cleanup(self, max_age: int = 3600):
        """Drop finished jobs and their temp files once they're old enough."""
        now = time.time()
        with self._lock:
            stale = [j for j in self._jobs.values() if now - j.created > max_age]
        for job in stale:
            if job.file and os.path.exists(job.file):
                shutil.rmtree(os.path.dirname(job.file), ignore_errors=True)
            with self._lock:
                self._jobs.pop(job.id, None)


store = JobStore()
