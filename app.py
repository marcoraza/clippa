import os
import re
import sys
import time
import uuid
import glob
import shutil
import threading
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask, request, jsonify, send_file, render_template
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


def get_resource_dir():
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))

    return Path(__file__).resolve().parent


def get_download_dir():
    if getattr(sys, "frozen", False):
        return Path.home() / "Downloads" / "Clippa"

    return get_resource_dir() / "downloads"


def ensure_runtime_path():
    runtime_bin = get_resource_dir() / "bin"
    extra_paths = [str(runtime_bin), "/opt/homebrew/bin", "/usr/local/bin"]
    current_path = os.environ.get("PATH", "")
    current_parts = [part for part in current_path.split(os.pathsep) if part]

    for path in reversed(extra_paths):
        if os.path.isdir(path) and path not in current_parts:
            current_parts.insert(0, path)

    os.environ["PATH"] = os.pathsep.join(current_parts)


ensure_runtime_path()


RESOURCE_DIR = get_resource_dir()
DOWNLOAD_DIR = str(get_download_dir())
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
FFMPEG_LOCATION = str(RESOURCE_DIR / "bin") if (RESOURCE_DIR / "bin").is_dir() else None

app = Flask(
    __name__,
    template_folder=str(RESOURCE_DIR / "templates"),
    static_folder=str(RESOURCE_DIR / "static"),
)

jobs = {}
jobs_lock = threading.Lock()
JOB_TTL = 3600


def cleanup_expired_jobs():
    now = time.time()
    with jobs_lock:
        expired = [jid for jid, j in jobs.items() if now - j.get("created", 0) > JOB_TTL]
        for jid in expired:
            job = jobs.pop(jid, None)
            if job and job.get("file"):
                try:
                    os.remove(job["file"])
                except OSError:
                    pass


def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname)
    except Exception:
        return False


def make_progress_hook(job):
    def hook(d):
        if job.get("cancel") and job["cancel"].is_set():
            raise CancelledError("Download cancelado")
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                job["progress"] = round(downloaded / total * 100)
        elif d["status"] == "finished":
            job["progress_phase"] = "processing"
    return hook


class CancelledError(Exception):
    pass


class YtdlpLogger:
    def __init__(self):
        self.errors = []

    def debug(self, msg):
        return None

    def warning(self, msg):
        return None

    def error(self, msg):
        self.errors.append(msg)

    @property
    def last_error(self):
        return self.errors[-1] if self.errors else ""


def build_ydl_options(timeout_seconds=None):
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    if timeout_seconds is not None:
        options["socket_timeout"] = timeout_seconds

    if FFMPEG_LOCATION:
        options["ffmpeg_location"] = FFMPEG_LOCATION

    return options


def copy_to_downloads(src, filename):
    downloads = Path.home() / "Downloads"
    target = downloads / filename
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        n = 1
        while target.exists():
            target = downloads / f"{stem} ({n}){suffix}"
            n += 1
    try:
        shutil.copy2(src, target)
        return str(target)
    except OSError:
        return None


def run_download(job_id, url, format_choice, format_id):
    job = jobs[job_id]
    out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")
    logger = YtdlpLogger()
    ydl_options = build_ydl_options(timeout_seconds=300)
    ydl_options.update({
        "logger": logger,
        "outtmpl": out_template,
        "progress_hooks": [make_progress_hook(job)],
    })

    if format_choice == "audio":
        ydl_options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }],
        })
    elif format_id:
        ydl_options.update({
            "format": f"{format_id}+bestaudio/best",
            "merge_output_format": "mp4",
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }],
        })
    else:
        ydl_options.update({
            "format": "bestvideo[vcodec^=avc1]+bestaudio/bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }],
        })

    try:
        with YoutubeDL(ydl_options) as ydl:
            ydl.download([url])

        if job.get("cancel") and job["cancel"].is_set():
            raise CancelledError("Download cancelado")

        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*"))
        if not files:
            job["status"] = "error"
            job["error"] = "Download completed but no file was found"
            return

        if format_choice == "audio":
            target = [f for f in files if f.endswith(".mp3")]
            chosen = target[0] if target else files[0]
        else:
            target = [f for f in files if f.endswith(".mp4")]
            chosen = target[0] if target else files[0]

        for f in files:
            if f != chosen:
                try:
                    os.remove(f)
                except OSError:
                    pass

        job["status"] = "done"
        job["file"] = chosen
        ext = os.path.splitext(chosen)[1]
        title = job.get("title", "").strip()
        if title:
            safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()
            if len(safe_title) > 80:
                safe_title = safe_title[:80].rsplit(" ", 1)[0].strip()
            job["filename"] = f"{safe_title}{ext}" if safe_title else os.path.basename(chosen)
        else:
            job["filename"] = os.path.basename(chosen)

        saved = copy_to_downloads(chosen, job["filename"])
        if saved:
            job["saved_path"] = saved
    except CancelledError:
        job["status"] = "cancelled"
        job["error"] = "Download cancelado"
        for f in glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*")):
            try:
                os.remove(f)
            except OSError:
                pass
    except DownloadError as e:
        job["status"] = "error"
        job["error"] = logger.last_error or str(e)
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if not is_valid_url(url):
        return jsonify({"error": "Invalid URL"}), 400

    logger = YtdlpLogger()
    ydl_options = build_ydl_options(timeout_seconds=60)
    ydl_options["logger"] = logger

    try:
        with YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(url, download=False)

        # Build quality options — prefer h264 per resolution (QuickTime-compatible)
        best_by_height = {}
        for f in info.get("formats", []):
            height = f.get("height")
            vcodec = f.get("vcodec", "none")
            if height and vcodec != "none":
                existing = best_by_height.get(height)
                is_h264 = vcodec.startswith("avc")
                existing_h264 = existing and existing.get("vcodec", "").startswith("avc")
                # Prefer h264 over other codecs; within same codec family, prefer higher bitrate
                if not existing or (is_h264 and not existing_h264) or \
                   (is_h264 == existing_h264 and (f.get("tbr") or 0) > (existing.get("tbr") or 0)):
                    best_by_height[height] = f

        formats = []
        for height, f in best_by_height.items():
            formats.append({
                "id": f["format_id"],
                "label": f"{height}p",
                "height": height,
            })
        formats.sort(key=lambda x: x["height"], reverse=True)

        return jsonify({
            "title": info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration"),
            "uploader": info.get("uploader", ""),
            "formats": formats,
        })
    except DownloadError as e:
        return jsonify({"error": logger.last_error or str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download", methods=["POST"])
def start_download():
    cleanup_expired_jobs()
    data = request.json
    url = data.get("url", "").strip()
    format_choice = data.get("format", "video")
    format_id = data.get("format_id")
    title = data.get("title", "")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if not is_valid_url(url):
        return jsonify({"error": "Invalid URL"}), 400

    if format_id and not re.match(r"^[\w\-]+$", format_id):
        return jsonify({"error": "Invalid format ID"}), 400

    job_id = uuid.uuid4().hex[:10]
    cancel_event = threading.Event()
    with jobs_lock:
        jobs[job_id] = {
            "status": "downloading",
            "url": url,
            "title": title,
            "created": time.time(),
            "cancel": cancel_event,
        }

    thread = threading.Thread(target=run_download, args=(job_id, url, format_choice, format_id))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/cancel/<job_id>", methods=["POST"])
def cancel_download(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job["status"] != "downloading":
        return jsonify({"error": "Job is not downloading"}), 400
    cancel_event = job.get("cancel")
    if cancel_event:
        cancel_event.set()
    return jsonify({"cancelled": True})


@app.route("/api/status/<job_id>")
def check_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "status": job["status"],
        "error": job.get("error"),
        "filename": job.get("filename"),
        "progress": job.get("progress", 0),
        "phase": job.get("progress_phase", "downloading"),
        "saved_path": job.get("saved_path"),
    })


@app.route("/api/file/<job_id>")
def download_file(job_id):
    payload = get_job_file(job_id)
    if not payload:
        return jsonify({"error": "File not ready"}), 404

    return send_file(payload["file"], as_attachment=True, download_name=payload["filename"])


def get_job_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return None

    return {"file": job["file"], "filename": job["filename"]}


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src * data:; "
        "connect-src 'self'"
    )
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8899))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port)
