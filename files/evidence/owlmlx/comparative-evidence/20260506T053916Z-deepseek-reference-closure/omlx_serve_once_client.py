#!/usr/bin/env python3
"""Start oMLX for one OpenAI-compatible streaming request, then stop it."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _wait_ready(base_url: str, *, timeout_s: float, server: subprocess.Popen) -> None:
    deadline = time.monotonic() + timeout_s
    last_error = ""
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"oMLX server exited before ready: {server.returncode}")
        try:
            with urllib.request.urlopen(base_url.rstrip("/") + "/v1/models", timeout=2) as response:
                response.read()
            return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = repr(exc)
            time.sleep(1)
    raise TimeoutError(f"oMLX server readiness timeout: {last_error}")


def _terminate(server: subprocess.Popen) -> None:
    if server.poll() is not None:
        return
    try:
        server.send_signal(signal.SIGTERM)
        server.wait(timeout=30)
    except Exception:
        try:
            server.kill()
            server.wait(timeout=10)
        except Exception:
            pass


def main() -> int:
    if len(sys.argv) != 8:
        print(
            "usage: omlx_serve_once_client.py MODEL_DIR MODEL_ID PORT PROMPT MAX_TOKENS TEMPERATURE LOG_PATH",
            file=sys.stderr,
        )
        return 2
    model_dir, model_id, port, prompt, max_tokens, temperature, log_path = sys.argv[1:]
    omlx_command = os.environ.get("OMLX_COMMAND", "omlx")
    log = Path(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)
    base_url = f"http://127.0.0.1:{port}"
    stream_client = Path(__file__).with_name("openai_stream_client.py")
    cmd = [
        omlx_command,
        "serve",
        "--model-dir",
        model_dir,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
        "--paged-ssd-cache-dir",
        "/Users/yeemio/AI/Agent/.omlx-cache",
        "--hot-cache-max-size",
        "8GB",
    ]
    with log.open("ab") as stream:
        stream.write(("COMMAND " + " ".join(cmd) + "\n").encode("utf-8"))
        stream.flush()
        server = subprocess.Popen(cmd, stdout=stream, stderr=stream)
        try:
            _wait_ready(base_url, timeout_s=900, server=server)
            client = subprocess.run(
                [
                    sys.executable,
                    str(stream_client),
                    base_url,
                    model_id,
                    prompt,
                    str(max_tokens),
                    str(temperature),
                ],
                cwd="/Users/yeemio/AI/gitrep/owlmlx",
                text=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
                timeout=900,
            )
            return int(client.returncode)
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        finally:
            _terminate(server)


if __name__ == "__main__":
    raise SystemExit(main())
