import sys
import multiprocessing

# torch pulls in multiprocessing; in a frozen app its helper processes re-exec
# this binary. freeze_support() lets those children run their own logic and exit
# here, before they ever reach the GUI or the worker dispatch below.
multiprocessing.freeze_support()

# Worker mode: run one separation and exit before importing any GUI. We key off an
# explicit argv flag (not an env var) so multiprocessing's own re-execs, which
# inherit the environment but not this flag, can never be mistaken for a job.
if len(sys.argv) > 1 and sys.argv[1] == "--clippa-separate":
    import separate_worker

    sys.exit(separate_worker.main(sys.argv[2:]))

import socket
import threading

import webview
from werkzeug.serving import make_server

from app import app


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


def main():
    server = EmbeddedServer(app)
    server.start()

    window = webview.create_window(
        "Clippa",
        server.url,
        width=1240,
        height=860,
        min_size=(980, 720),
    )
    window.events.closed += server.stop

    webview.start()


if __name__ == "__main__":
    main()
