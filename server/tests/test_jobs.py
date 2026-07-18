import time

from jobs import JobStore


def test_create_and_get():
    store = JobStore()
    job = store.create()
    assert job.status == "queued"
    assert store.get(job.id) is job


def test_get_unknown_returns_none():
    assert JobStore().get("missing") is None


def test_update_sets_fields():
    store = JobStore()
    job = store.create()
    store.update(job.id, status="done", progress=1.0)
    assert store.get(job.id).status == "done"
    assert store.get(job.id).progress == 1.0


def test_update_unknown_is_noop():
    JobStore().update("missing", status="done")  # should not raise


def test_cleanup_removes_old_jobs_and_files(tmp_path):
    store = JobStore()
    job = store.create()
    clip = tmp_path / "clip" / "clip.mp4"
    clip.parent.mkdir()
    clip.write_bytes(b"x")
    store.update(job.id, file=str(clip))
    store.get(job.id).created = time.time() - 4000

    store.cleanup(max_age=3600)

    assert store.get(job.id) is None
    assert not clip.exists()


def test_cleanup_keeps_recent_jobs():
    store = JobStore()
    job = store.create()
    store.cleanup(max_age=3600)
    assert store.get(job.id) is not None
