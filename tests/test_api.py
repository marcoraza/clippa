import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
from app import app, jobs, jobs_lock, is_valid_url, cleanup_expired_jobs


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    jobs.clear()


class TestURLValidation:
    def test_valid_https(self):
        assert is_valid_url("https://www.youtube.com/watch?v=abc")

    def test_valid_http(self):
        assert is_valid_url("http://example.com/video")

    def test_rejects_ftp(self):
        assert not is_valid_url("ftp://example.com/file")

    def test_rejects_javascript(self):
        assert not is_valid_url("javascript:alert(1)")

    def test_rejects_empty(self):
        assert not is_valid_url("")

    def test_rejects_no_host(self):
        assert not is_valid_url("http://")

    def test_rejects_plain_text(self):
        assert not is_valid_url("not a url")

    def test_rejects_file_scheme(self):
        assert not is_valid_url("file:///etc/passwd")


class TestJobCleanup:
    def test_cleans_expired_jobs(self):
        jobs["old"] = {"status": "done", "created": time.time() - 7200}
        jobs["new"] = {"status": "done", "created": time.time()}
        cleanup_expired_jobs()
        assert "old" not in jobs
        assert "new" in jobs
        jobs.clear()

    def test_removes_file_on_cleanup(self, tmp_path):
        f = tmp_path / "test.mp4"
        f.write_text("data")
        jobs["expired"] = {"status": "done", "created": time.time() - 7200, "file": str(f)}
        cleanup_expired_jobs()
        assert not f.exists()
        jobs.clear()

    def test_keeps_fresh_jobs(self):
        jobs["fresh"] = {"status": "downloading", "created": time.time()}
        cleanup_expired_jobs()
        assert "fresh" in jobs
        jobs.clear()


class TestIndexRoute:
    def test_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Clippa" in resp.data


class TestInfoEndpoint:
    def test_missing_url(self, client):
        resp = client.post("/api/info", json={})
        assert resp.status_code == 400

    def test_empty_url(self, client):
        resp = client.post("/api/info", json={"url": ""})
        assert resp.status_code == 400

    def test_invalid_url_scheme(self, client):
        resp = client.post("/api/info", json={"url": "ftp://evil.com"})
        assert resp.status_code == 400
        assert resp.json["error"] == "Invalid URL"

    def test_javascript_url(self, client):
        resp = client.post("/api/info", json={"url": "javascript:alert(1)"})
        assert resp.status_code == 400


class TestDownloadEndpoint:
    def test_missing_url(self, client):
        resp = client.post("/api/download", json={})
        assert resp.status_code == 400

    def test_empty_url(self, client):
        resp = client.post("/api/download", json={"url": ""})
        assert resp.status_code == 400

    def test_invalid_url(self, client):
        resp = client.post("/api/download", json={"url": "not-a-url"})
        assert resp.status_code == 400

    def test_invalid_format_id_injection(self, client):
        resp = client.post("/api/download", json={
            "url": "https://example.com/video",
            "format_id": "evil; rm -rf /",
        })
        assert resp.status_code == 400
        assert resp.json["error"] == "Invalid format ID"

    def test_invalid_format_id_spaces(self, client):
        resp = client.post("/api/download", json={
            "url": "https://example.com/video",
            "format_id": "has spaces",
        })
        assert resp.status_code == 400

    def test_valid_format_id(self, client):
        resp = client.post("/api/download", json={
            "url": "https://www.youtube.com/watch?v=test",
            "format": "video",
            "format_id": "137",
        })
        assert resp.status_code == 200
        assert "job_id" in resp.json

    def test_returns_job_id(self, client):
        resp = client.post("/api/download", json={
            "url": "https://www.youtube.com/watch?v=test",
            "format": "video",
        })
        assert resp.status_code == 200
        assert "job_id" in resp.json
        assert len(resp.json["job_id"]) == 10


class TestStatusEndpoint:
    def test_unknown_job(self, client):
        resp = client.get("/api/status/nonexistent")
        assert resp.status_code == 404

    def test_existing_job(self, client):
        jobs["testjob"] = {"status": "downloading", "created": time.time()}
        resp = client.get("/api/status/testjob")
        assert resp.status_code == 200
        assert resp.json["status"] == "downloading"
        assert "progress" in resp.json

    def test_done_job_has_filename(self, client):
        jobs["donejob"] = {
            "status": "done",
            "created": time.time(),
            "filename": "video.mp4",
            "file": "/tmp/video.mp4",
        }
        resp = client.get("/api/status/donejob")
        assert resp.status_code == 200
        assert resp.json["filename"] == "video.mp4"


class TestFileEndpoint:
    def test_unknown_job(self, client):
        resp = client.get("/api/file/nonexistent")
        assert resp.status_code == 404

    def test_not_done_job(self, client):
        jobs["pending"] = {"status": "downloading", "created": time.time()}
        resp = client.get("/api/file/pending")
        assert resp.status_code == 404


class TestCancelEndpoint:
    def test_cancel_unknown_job(self, client):
        resp = client.post("/api/cancel/nonexistent")
        assert resp.status_code == 404

    def test_cancel_non_downloading_job(self, client):
        jobs["done"] = {"status": "done", "created": time.time()}
        resp = client.post("/api/cancel/done")
        assert resp.status_code == 400

    def test_cancel_downloading_job(self, client):
        cancel_event = threading.Event()
        jobs["active"] = {"status": "downloading", "created": time.time(), "cancel": cancel_event}
        resp = client.post("/api/cancel/active")
        assert resp.status_code == 200
        assert resp.json["cancelled"] is True
        assert cancel_event.is_set()


class TestStatusPhase:
    def test_status_includes_phase(self, client):
        jobs["pjob"] = {"status": "downloading", "created": time.time(), "progress_phase": "processing"}
        resp = client.get("/api/status/pjob")
        assert resp.json["phase"] == "processing"

    def test_status_default_phase(self, client):
        jobs["djob"] = {"status": "downloading", "created": time.time()}
        resp = client.get("/api/status/djob")
        assert resp.json["phase"] == "downloading"


class TestSecurityHeaders:
    def test_nosniff(self, client):
        resp = client.get("/")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_frame_deny(self, client):
        resp = client.get("/")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_csp_present(self, client):
        resp = client.get("/")
        assert "Content-Security-Policy" in resp.headers
