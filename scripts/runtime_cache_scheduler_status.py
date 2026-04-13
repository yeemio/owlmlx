#!/usr/bin/env python3
"""Emit the runtime-owned cache/scheduler depth status for owlmlx."""

from __future__ import annotations

import argparse
import json

from owlmlx import build_cache_scheduler_status, cache_scheduler_status_to_dict


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit the current owlmlx cache/scheduler depth status."
    )
    parser.add_argument("--configured-cache-dir", default=None)
    parser.add_argument("--configured-cache-max-size", default=None)
    parser.add_argument("--configured-hot-cache-size", default=None)
    parser.add_argument(
        "--runtime-profile",
        choices=("baseline", "cache-enabled", "not_running", "unknown"),
        default=None,
    )
    parser.add_argument("--runtime-cache-dir", default=None)
    parser.add_argument("--runtime-cache-max-size", default=None)
    parser.add_argument("--runtime-hot-cache-size", default=None)
    parser.add_argument("--bits-in-cache-key", action="store_true")
    parser.add_argument("--invalidates-on-config-toggle", action="store_true")
    parser.add_argument("--runtime-verified", action="store_true")
    args = parser.parse_args()

    configured_flags = {
        "paged_ssd_cache_dir": args.configured_cache_dir,
        "paged_ssd_cache_max_size": args.configured_cache_max_size,
        "hot_cache_max_size": args.configured_hot_cache_size,
    }
    runtime_flags = {
        "paged_ssd_cache_dir": args.runtime_cache_dir,
        "paged_ssd_cache_max_size": args.runtime_cache_max_size,
        "hot_cache_max_size": args.runtime_hot_cache_size,
    }

    status = build_cache_scheduler_status(
        configured_flags=configured_flags,
        runtime_profile=args.runtime_profile,
        runtime_flags=runtime_flags if any(runtime_flags.values()) else None,
        bits_in_cache_key=args.bits_in_cache_key,
        invalidates_on_config_toggle=args.invalidates_on_config_toggle,
        runtime_verified=args.runtime_verified,
    )
    print(json.dumps(cache_scheduler_status_to_dict(status), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
