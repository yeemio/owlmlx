#!/usr/bin/env python3
"""Run the owlmlx native-backend technical-preview server."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn

from owlmlx.runtime.native_preview import DEFAULT_TECHNICAL_PREVIEW_PORT


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Start owlmlx technical-preview serving with the native MLX backend. "
            "This is the opt-in path for native session KV cache validation."
        )
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_TECHNICAL_PREVIEW_PORT)
    parser.add_argument(
        "--models-root",
        default=os.environ.get("OWLMLX_MODELS_ROOT", "/Users/yeemio/AI/Agent/models"),
        help="Local model root used for model visibility and model-id resolution.",
    )
    parser.add_argument(
        "--enable-session-cache",
        action="store_true",
        help="Set OWLMLX_SESSION_CACHE_ENABLED=1 before constructing the backend.",
    )
    parser.add_argument(
        "--enable-auto-prefix",
        action="store_true",
        help=(
            "Set OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED=1 before constructing "
            "the backend. Requires --enable-session-cache for reuse."
        ),
    )
    parser.add_argument(
        "--session-cache-max-resident-bytes",
        default=os.environ.get("OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES", ""),
        help="Optional resident-cache byte cap for the experimental session cache.",
    )
    parser.add_argument(
        "--runtime-monitor-trend-ledger-path",
        default=os.environ.get("OWLMLX_RUNTIME_MONITOR_TREND_LEDGER_PATH", ""),
        help="Optional rolling JSONL ledger path for Runtime Monitor trend history.",
    )
    parser.add_argument(
        "--runtime-monitor-sample-interval-s",
        type=float,
        default=float(os.environ.get("OWLMLX_RUNTIME_MONITOR_SAMPLE_INTERVAL_S", "0")),
        help="Background Runtime Monitor sampling interval in seconds; 0 disables it.",
    )
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    os.environ["OWLMLX_MODELS_ROOT"] = str(Path(args.models_root).expanduser())
    os.environ["OWLMLX_RUNTIME_URL"] = f"http://{args.host}:{args.port}"
    if args.enable_session_cache:
        os.environ["OWLMLX_SESSION_CACHE_ENABLED"] = "1"
    if args.enable_auto_prefix:
        os.environ["OWLMLX_SESSION_CACHE_AUTO_PREFIX_ENABLED"] = "1"
    if args.session_cache_max_resident_bytes:
        os.environ["OWLMLX_SESSION_CACHE_MAX_RESIDENT_BYTES"] = str(
            args.session_cache_max_resident_bytes
        )
    if args.runtime_monitor_trend_ledger_path:
        os.environ["OWLMLX_RUNTIME_MONITOR_TREND_LEDGER_PATH"] = str(
            Path(args.runtime_monitor_trend_ledger_path).expanduser()
        )
    if args.runtime_monitor_sample_interval_s > 0:
        os.environ["OWLMLX_RUNTIME_MONITOR_SAMPLE_INTERVAL_S"] = str(
            args.runtime_monitor_sample_interval_s
        )

    uvicorn.run(
        "owlmlx.runtime.native_preview:create_native_preview_app",
        factory=True,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
