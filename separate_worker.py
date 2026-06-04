"""Run one stem separation in a throwaway process.

The torch/onnxruntime stack aborts (SIGABRT) when its tensor destructors run
during interpreter teardown, which would take the desktop window down with it.
Isolating each separation in its own process means that abort can only kill a
disposable worker. We also skip the teardown entirely with os._exit() right
after the result is written, so the abort never even fires.
"""

import os
import sys


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 4:
        sys.stderr.write(
            "usage: separate_worker AUDIO TARGET OUTPUT_DIR MODEL_DIR [FFMPEG_DIR]\n"
        )
        return 2

    audio_path, target, output_dir, model_dir = argv[:4]
    ffmpeg_dir = argv[4] if len(argv) > 4 and argv[4] else None

    import separation

    try:
        stem_path = separation.separate(
            audio_path, target, output_dir, model_dir, ffmpeg_dir=ffmpeg_dir
        )
    except Exception as exc:
        sys.stderr.write(f"{type(exc).__name__}: {exc}\n")
        sys.stderr.flush()
        os._exit(1)

    sys.stdout.write(f"{separation.WORKER_RESULT_PREFIX}{os.path.abspath(stem_path)}\n")
    sys.stdout.flush()
    # Skip normal interpreter teardown: that is where the torch destructors abort.
    os._exit(0)


if __name__ == "__main__":
    sys.exit(main())
