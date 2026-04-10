import shutil
import socket
import threading
from pathlib import Path

import webview
from werkzeug.serving import make_server

from app import app, get_job_file


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return sock.getsockname()[1]


class EmbeddedServer:
    def __init__(self, flask_app):
        self.host = "127.0.0.1"
        self.port = get_free_port()
        self._server = make_server(self.host, self.port, flask_app, threaded=True)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self):
        return f"http://{self.host}:{self.port}"

    def start(self):
        self._thread.start()

    def stop(self):
        self._server.shutdown()
        self._thread.join(timeout=3)


class DesktopApi:
    def __init__(self):
        self.window = None

    def attach_window(self, window):
        self.window = window

    def auto_save(self, job_id):
        payload = get_job_file(job_id)
        if not payload:
            return {"saved": False, "error": "Arquivo não encontrado"}

        downloads = Path.home() / "Downloads"
        downloads.mkdir(exist_ok=True)
        target = downloads / payload["filename"]

        # Avoid overwriting: append (1), (2), etc.
        if target.exists():
            stem = target.stem
            suffix = target.suffix
            n = 1
            while target.exists():
                target = downloads / f"{stem} ({n}){suffix}"
                n += 1

        shutil.copy2(payload["file"], target)
        return {"saved": True, "path": str(target)}


def main():
    server = EmbeddedServer(app)
    server.start()

    api = DesktopApi()
    window = webview.create_window(
        "Clippa",
        server.url,
        width=1240,
        height=860,
        min_size=(980, 720),
        js_api=api,
    )
    api.attach_window(window)
    window.events.closed += server.stop

    webview.start()


if __name__ == "__main__":
    main()
