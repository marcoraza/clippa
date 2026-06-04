"""Vocal/instrumental stem separation behind a swappable interface.

Today the only backend is local UVR (MDX-Net ONNX models via audio-separator).
The public surface is `is_available()` and `separate()`, so a future cloud or
VPS backend can be plugged in without touching the rest of the app.
"""

import os
import re
import sys
import time
import tempfile
import subprocess
from pathlib import Path

# Sentinel the worker prints on stdout with the absolute path of the finished stem.
WORKER_RESULT_PREFIX = "CLIPPA_RESULT:"
# Hard cap so a wedged worker can never hang a job forever (a song is ~2-3 min).
WORKER_TIMEOUT = 1800


class SeparationCancelled(Exception):
    pass


# tqdm prints "  43%|..." progress to the worker's stderr log. We tail that log
# while the worker runs and surface the last percentage so the UI can show a real
# bar instead of a featureless spinner on a 3-4 minute job.
_PROGRESS_RE = re.compile(r"(\d{1,3})%")

# Each target uses the UVR model specialized for that stem.
# Roformer models are avoided on purpose: they crash on Python 3.14 (beartype).
STEM_MODELS = {
    "vocals": "Kim_Vocal_2.onnx",
    "instrumental": "UVR-MDX-NET-Inst_HQ_3.onnx",
}

# audio-separator names its output after this stem key.
STEM_OUTPUT_NAME = {
    "vocals": "Vocals",
    "instrumental": "Instrumental",
}


def _accelerated_providers():
    """Best ONNX Runtime providers available, hardware accel first, CPU fallback.

    audio-separator only enables CoreML when platform.uname().processor == "arm",
    which comes back empty inside the PyInstaller-frozen .app, so it silently runs
    on CPU (~8x slower). We pick the provider ourselves from what ONNX Runtime
    actually exposes and keep CPU as a fallback so a CoreML session failure can
    never break separation outright.
    """
    try:
        import onnxruntime as ort
        available = ort.get_available_providers()
    except Exception:
        return None
    for accel in ("CUDAExecutionProvider", "CoreMLExecutionProvider"):
        if accel in available:
            return [accel, "CPUExecutionProvider"]
    return None


def is_available():
    try:
        import audio_separator.separator  # noqa: F401
        return True
    except Exception:
        return False


def get_model_dir(base_dir):
    model_dir = Path(base_dir) / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    return str(model_dir)


def separate(audio_path, target, output_dir, model_dir, ffmpeg_dir=None):
    """Separate `audio_path` and return the absolute path to the chosen stem.

    target: "vocals" or "instrumental".
    Models auto-download into `model_dir` on first use and are cached there.
    """
    if target not in STEM_MODELS:
        raise ValueError(f"Unknown stem target: {target}")

    if ffmpeg_dir and os.path.isdir(ffmpeg_dir):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

    from audio_separator.separator import Separator

    separator = Separator(
        output_dir=output_dir,
        output_format="mp3",
        output_single_stem=STEM_OUTPUT_NAME[target],
        model_file_dir=model_dir,
        log_level=30,
    )
    providers = _accelerated_providers()
    if providers:
        separator.onnx_execution_provider = providers
    separator.load_model(model_filename=STEM_MODELS[target])
    outputs = separator.separate(audio_path)

    if not outputs:
        raise RuntimeError("Separation produced no output")

    return os.path.join(output_dir, outputs[0])


def _worker_command(audio_path, target, output_dir, model_dir, ffmpeg_dir):
    args = [audio_path, target, output_dir, model_dir, ffmpeg_dir or ""]
    if getattr(sys, "frozen", False):
        return [sys.executable, "--clippa-separate", *args], dict(os.environ)
    worker = os.path.join(os.path.dirname(os.path.abspath(__file__)), "separate_worker.py")
    return [sys.executable, worker, *args], dict(os.environ)


def separate_subprocess(audio_path, target, output_dir, model_dir, ffmpeg_dir=None, cancel_check=None, progress_cb=None):
    """Run `separate()` in a worker process and return the stem path.

    Same contract as separate(), but the torch work happens in a disposable
    process. A native abort in the worker can no longer kill the host (the GUI);
    the job just fails. cancel_check is polled so a user cancel stops the worker.
    progress_cb, if given, is called with an int 0-100 as the worker advances.
    """
    if target not in STEM_MODELS:
        raise ValueError(f"Unknown stem target: {target}")

    cmd, env = _worker_command(audio_path, target, output_dir, model_dir, ffmpeg_dir)
    err_log = tempfile.NamedTemporaryFile(mode="w+", suffix=".log", delete=False)
    try:
        proc = subprocess.Popen(
            cmd, env=env, stdout=subprocess.PIPE, stderr=err_log, text=True
        )
        start = time.time()
        last_pct = -1
        while proc.poll() is None:
            if cancel_check and cancel_check():
                _terminate(proc)
                raise SeparationCancelled()
            if time.time() - start > WORKER_TIMEOUT:
                _terminate(proc)
                raise RuntimeError("Separation timed out")
            if progress_cb:
                pct = _read_progress(err_log.name)
                if pct is not None:
                    # MDX runs two tqdm passes (a long main one, then a short
                    # reconstruction); clamp so the bar never moves backwards.
                    pct = max(pct, last_pct)
                    if pct != last_pct:
                        last_pct = pct
                        progress_cb(pct)
            time.sleep(0.3)

        out = proc.stdout.read() if proc.stdout else ""
        result_path = None
        for line in out.splitlines():
            if line.startswith(WORKER_RESULT_PREFIX):
                result_path = line[len(WORKER_RESULT_PREFIX):].strip()

        if result_path and os.path.exists(result_path):
            return result_path

        err_log.seek(0)
        tail = [ln for ln in err_log.read().splitlines() if ln.strip()][-5:]
        detail = " | ".join(tail) if tail else f"worker exit {proc.returncode}"
        raise RuntimeError(f"Separation failed: {detail}")
    finally:
        err_log.close()
        try:
            os.remove(err_log.name)
        except OSError:
            pass


def _read_progress(path):
    """Return the latest tqdm percentage in the worker log, or None if not started."""
    try:
        with open(path, "r", errors="ignore") as f:
            text = f.read()
    except OSError:
        return None
    matches = _PROGRESS_RE.findall(text)
    if not matches:
        return None
    return min(int(matches[-1]), 100)


def _terminate(proc):
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
