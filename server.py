import os
import sys
import json
import uuid
import glob
import mimetypes
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Ensure yt_dlp is importable from bundled binary
bin_path = os.path.join(os.path.dirname(__file__), "bin", "yt-dlp")
if os.path.exists(bin_path):
    sys.path.insert(0, bin_path)

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

jobs = {}


def format_bytes(b):
    if not b or b <= 0:
        return None
    if b < 1024 * 1024:
        return f"{round(b / 1024)} KB"
    if b < 1024 * 1024 * 1024:
        mb = b / (1024 * 1024)
        return f"{round(mb)} MB" if mb >= 100 else f"{mb:.1f} MB"
    gb = b / (1024 * 1024 * 1024)
    return f"{gb:.1f} GB"


def run_download_thread(job_id, url, format_choice, format_id):
    job = jobs.get(job_id)
    if not job:
        return

    out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")

    def progress_hook(d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            if total > 0:
                pct = min(99.0, max(0.0, round((downloaded / total) * 100, 1)))
                job["percent"] = pct
            else:
                job["percent"] = 0
            job["status"] = "downloading"
            job["speed"] = d.get("speed")
            job["eta"] = d.get("eta")
        elif status == "finished":
            job["percent"] = 100
            job["status"] = "processing"

    ydl_opts = {
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
    }

    if format_choice == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif format_id:
        ydl_opts["format"] = f"{format_id}+bestaudio/best"
        ydl_opts["merge_output_format"] = "mp4"
    else:
        ydl_opts["format"] = "bestvideo+bestaudio/best"
        ydl_opts["merge_output_format"] = "mp4"

    try:
        if yt_dlp is None:
            raise RuntimeError("yt_dlp module could not be loaded")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

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
        job["percent"] = 100
        job["file"] = chosen
        ext = os.path.splitext(chosen)[1]
        title = (job.get("title") or "").strip()
        if title:
            safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()[:100].strip()
            job["filename"] = f"{safe_title}{ext}" if safe_title else os.path.basename(chosen)
        else:
            job["filename"] = os.path.basename(chosen)
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)


class ReClipHandler(BaseHTTPRequestHandler):
    def send_json_response(self, data, status_code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            file_path = os.path.join(BASE_DIR, "templates", "index.html")
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "index.html not found")
            return

        if path == "/robots.txt":
            host = self.headers.get("Host", "localhost:3000")
            proto = "https" if "https" in self.headers.get("X-Forwarded-Proto", "") else "http"
            robots_txt = (
                "User-agent: *\n"
                "Allow: /\n"
                "Disallow: /api/\n"
                "Disallow: /downloads/\n\n"
                f"Sitemap: {proto}://{host}/sitemap.xml\n"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(robots_txt)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(robots_txt)
            return

        if path == "/sitemap.xml":
            host = self.headers.get("Host", "localhost:3000")
            proto = "https" if "https" in self.headers.get("X-Forwarded-Proto", "") else "http"
            sitemap_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                '  <url>\n'
                f'    <loc>{proto}://{host}/</loc>\n'
                '    <lastmod>2026-10-09</lastmod>\n'
                '    <changefreq>daily</changefreq>\n'
                '    <priority>1.0</priority>\n'
                '  </url>\n'
                '</urlset>\n'
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.send_header("Content-Length", str(len(sitemap_xml)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(sitemap_xml)
            return

        if path.startswith("/static/") or path.startswith("/assets/"):
            rel_path = path.lstrip("/")
            file_path = os.path.join(BASE_DIR, rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "File not found")
            return

        if path.startswith("/api/status/"):
            job_id = path.split("/api/status/")[1]
            job = jobs.get(job_id)
            if not job:
                self.send_json_response({"error": "Job not found"}, 404)
                return
            self.send_json_response({
                "status": job["status"],
                "percent": job.get("percent", 0),
                "speed": job.get("speed"),
                "eta": job.get("eta"),
                "error": job.get("error"),
                "filename": job.get("filename"),
            })
            return

        if path.startswith("/api/file/"):
            job_id = path.split("/api/file/")[1]
            job = jobs.get(job_id)
            if not job or job.get("status") != "done" or not job.get("file"):
                self.send_json_response({"error": "File not ready"}, 404)
                return

            file_path = job["file"]
            if not os.path.exists(file_path):
                self.send_json_response({"error": "File not found on server"}, 404)
                return

            filename = job.get("filename") or os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()

            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
            return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        if path == "/api/info":
            url = (body.get("url") or "").strip()
            if not url:
                self.send_json_response({"error": "No URL provided"}, 400)
                return

            try:
                if yt_dlp is None:
                    raise RuntimeError("yt_dlp is not available")

                ydl_opts = {
                    "skip_download": True,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                duration = info.get("duration") or 0

                # Determine best audio size
                best_audio_size = 0
                best_audio_bitrate = 0
                for f in info.get("formats", []):
                    if f.get("vcodec") == "none" and f.get("acodec") != "none":
                        abr = f.get("abr") or f.get("tbr") or 0
                        if abr > best_audio_bitrate:
                            best_audio_bitrate = abr
                            a_size = f.get("filesize") or f.get("filesize_approx")
                            if a_size:
                                best_audio_size = a_size
                            elif duration and abr:
                                best_audio_size = round((abr * 1000 / 8) * duration)

                if not best_audio_size and duration:
                    best_audio_size = round((128 * 1000 / 8) * duration)

                audio_filesize = best_audio_size or (round((192 * 1000 / 8) * duration) if duration else None)

                best_by_height = {}
                for f in info.get("formats", []):
                    height = f.get("height")
                    if height and f.get("vcodec") != "none":
                        tbr = f.get("tbr") or 0
                        if height not in best_by_height or tbr > (best_by_height[height].get("tbr") or 0):
                            best_by_height[height] = f

                formats = []
                for height, f in best_by_height.items():
                    size = f.get("filesize") or f.get("filesize_approx")
                    is_video_only = not f.get("acodec") or f.get("acodec") == "none"

                    if not size and duration and (f.get("tbr") or f.get("vbr")):
                        br = f.get("tbr") or f.get("vbr")
                        size = round((br * 1000 / 8) * duration)

                    if size and is_video_only and best_audio_size:
                        size += best_audio_size

                    formats.append({
                        "id": f.get("format_id"),
                        "label": f"{height}p",
                        "height": height,
                        "filesize": size,
                        "filesize_formatted": format_bytes(size),
                    })

                formats.sort(key=lambda x: x["height"], reverse=True)

                self.send_json_response({
                    "title": info.get("title", ""),
                    "thumbnail": info.get("thumbnail", ""),
                    "duration": duration,
                    "uploader": info.get("uploader", ""),
                    "formats": formats,
                    "audio_filesize": audio_filesize,
                    "audio_filesize_formatted": format_bytes(audio_filesize),
                })
            except Exception as e:
                self.send_json_response({"error": str(e)}, 400)
            return

        if path == "/api/playlist":
            url = (body.get("url") or "").strip()
            if not url:
                self.send_json_response({"error": "No URL provided"}, 400)
                return

            try:
                if yt_dlp is None:
                    raise RuntimeError("yt_dlp is not available")

                ydl_opts = {
                    "extract_flat": True,
                    "quiet": True,
                    "no_warnings": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                entries = info.get("entries", [])
                urls = [entry.get("url") for entry in entries if entry.get("url")]
                self.send_json_response({"urls": urls})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 400)
            return

        if path == "/api/download":
            url = (body.get("url") or "").strip()
            format_choice = body.get("format", "video")
            format_id = body.get("format_id")
            title = body.get("title", "")

            if not url:
                self.send_json_response({"error": "No URL provided"}, 400)
                return

            job_id = uuid.uuid4().hex[:10]
            jobs[job_id] = {"status": "downloading", "percent": 0, "url": url, "title": title}

            thread = threading.Thread(
                target=run_download_thread,
                args=(job_id, url, format_choice, format_id)
            )
            thread.daemon = True
            thread.start()

            self.send_json_response({"job_id": job_id})
            return

        self.send_error(404, "Endpoint not found")

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 33073))
    host = "0.0.0.0"
    server = ThreadingHTTPServer((host, port), ReClipHandler)
    print(f"ReClip Python server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
