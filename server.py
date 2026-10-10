import os
import re
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_file, send_from_directory

try:
    import yt_dlp
except ImportError:  # pragma: no cover
    yt_dlp = None

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "templates" / "index.html"
if not INDEX_FILE.is_file():
    INDEX_FILE = BASE_DIR / "index(2).html"
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()


def error_response(message: str, status: int = 400):
    return jsonify({"error": message}), status


def require_ytdlp():
    if yt_dlp is None:
        raise RuntimeError("yt-dlp is not installed. Run: pip install -r requirements.txt")


def validate_url(value: Any) -> str:
    url = str(value or "").strip()
    if not re.match(r"^https?://", url, re.I) or len(url) > 4096:
        raise ValueError("Please provide a valid http(s) URL")
    return url


def format_size(size: int | float | None) -> str | None:
    if not size:
        return None
    size = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return None


def format_duration(seconds: Any) -> int | None:
    try:
        return int(float(seconds)) if seconds is not None else None
    except (TypeError, ValueError):
        return None


def human_error(exc: Exception) -> str:
    message = str(exc).strip().replace("\n", " ")
    return message[-1000:] if message else "Unable to process this URL"


def extract_info(url: str, flat: bool = False) -> dict[str, Any]:
    require_ytdlp()
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "socket_timeout": 20,
    }
    if flat:
        options.update({"extract_flat": "in_playlist", "noplaylist": False})
    with yt_dlp.YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False)


def get_video_formats(info: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a small, useful quality list for the UI, highest quality first."""
    candidates = []
    seen_heights: set[int] = set()
    for item in info.get("formats") or []:
        height = item.get("height")
        if not height or not item.get("vcodec") or item.get("vcodec") == "none":
            continue
        if height < 144 or height in seen_heights:
            continue
        seen_heights.add(height)
        size = item.get("filesize") or item.get("filesize_approx")
        candidates.append({
            "id": str(item.get("format_id")),
            "label": f"{height}p",
            "height": height,
            "ext": item.get("ext"),
            "filesize": size,
            "filesize_formatted": format_size(size),
        })
    candidates.sort(key=lambda x: x["height"], reverse=True)
    return candidates[:12]


def progress_hook(job_id: str):
    def hook(data: dict[str, Any]):
        status = data.get("status")
        with jobs_lock:
            job = jobs.get(job_id)
            if not job:
                return
            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                downloaded = data.get("downloaded_bytes", 0)
                job["status"] = "downloading"
                job["percent"] = round(downloaded * 100 / total, 1) if total else job.get("percent", 0)
            elif status == "finished":
                job["status"] = "processing"
                job["percent"] = 99
    return hook


def run_download(job_id: str, url: str, media_format: str, format_id: str | None):
    try:
        require_ytdlp()
        output_template = str(DOWNLOAD_DIR / f"{job_id}.%(ext)s")
        options: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "outtmpl": output_template,
            "progress_hooks": [progress_hook(job_id)],
            "socket_timeout": 30,
            "retries": 2,
            "overwrites": True,
        }
        if media_format == "audio":
            options.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            # The selected format is a video stream; yt-dlp merges the best audio.
            options.update({
                "format": f"{format_id}+bestaudio/best" if format_id else "bestvideo*+bestaudio/best",
                "merge_output_format": "mp4",
            })

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        files = [p for p in DOWNLOAD_DIR.glob(f"{job_id}.*") if p.is_file()]
        if not files:
            raise RuntimeError("Download completed but no output file was found")
        output = max(files, key=lambda p: p.stat().st_mtime)
        with jobs_lock:
            jobs[job_id].update({
                "status": "done",
                "percent": 100,
                "path": str(output),
                "filename": output.name,
            })
    except Exception as exc:
        with jobs_lock:
            if job_id in jobs:
                jobs[job_id].update({"status": "error", "error": human_error(exc)})


def cleanup_old_jobs():
    cutoff = time.time() - 6 * 3600
    with jobs_lock:
        old_ids = [job_id for job_id, job in jobs.items() if job.get("created", 0) < cutoff]
        old_jobs = [jobs.pop(job_id) for job_id in old_ids]
    for job in old_jobs:
        path = job.get("path")
        if path:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/info", methods=["POST"])
def api_info():
    try:
        url = validate_url((request.get_json(silent=True) or {}).get("url"))
        info = extract_info(url)
        formats = get_video_formats(info)
        return jsonify({
            "title": info.get("title") or "Untitled",
            "thumbnail": info.get("thumbnail") or "",
            "duration": format_duration(info.get("duration")),
            "uploader": info.get("uploader") or info.get("channel") or "",
            "formats": formats,
            "audio_filesize": next((f.get("filesize") for f in info.get("formats", [])[::-1]
                                    if f.get("acodec") not in (None, "none") and f.get("filesize")), None),
            "audio_filesize_formatted": None,
        })
    except Exception as exc:
        return error_response(human_error(exc), 422)


@app.route("/api/playlist", methods=["POST"])
def api_playlist():
    try:
        url = validate_url((request.get_json(silent=True) or {}).get("url"))
        info = extract_info(url, flat=True)
        urls = []
        for entry in info.get("entries") or []:
            if not entry:
                continue
            entry_url = entry.get("webpage_url") or entry.get("url")
            if entry_url and entry_url.startswith("http"):
                urls.append(entry_url)
        return jsonify({"urls": urls[:200]})
    except Exception as exc:
        return error_response(human_error(exc), 422)


@app.route("/api/download", methods=["POST"])
def api_download():
    try:
        payload = request.get_json(silent=True) or {}
        url = validate_url(payload.get("url"))
        media_format = payload.get("format", "video")
        if media_format not in {"video", "audio"}:
            raise ValueError("format must be video or audio")
        format_id = str(payload.get("format_id")) if payload.get("format_id") else None
        job_id = uuid.uuid4().hex
        with jobs_lock:
            jobs[job_id] = {"status": "queued", "percent": 0, "created": time.time()}
        threading.Thread(target=run_download, args=(job_id, url, media_format, format_id), daemon=True).start()
        cleanup_old_jobs()
        return jsonify({"job_id": job_id})
    except Exception as exc:
        return error_response(human_error(exc), 422)


@app.route("/api/status/<job_id>", methods=["GET"])
def api_status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return error_response("Job not found", 404)
        return jsonify({k: v for k, v in job.items() if k not in {"path", "created"}})


@app.route("/api/file/<job_id>", methods=["GET"])
def api_file(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job or job.get("status") != "done":
            return error_response("File is not ready", 404)
        path = Path(job["path"])
        filename = job.get("filename", path.name)
    if not path.is_file() or path.parent != DOWNLOAD_DIR:
        return error_response("File not found", 404)
    return send_file(path, as_attachment=True, download_name=filename)


@app.route("/", methods=["GET"])
def index():
    return send_file(INDEX_FILE)


@app.route("/<path:filename>", methods=["GET"])
def static_files(filename: str):
    return send_from_directory(BASE_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
