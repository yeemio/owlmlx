"""Cache profile and cache-safety truth for MLX serving runtimes.

This module owns cache-related runtime semantics that are independent of a
specific platform shell:

- cache profile labels
- cache flag schema
- configured/runtime profile derivation
- restart-required derivation
- TurboQuant cache-safety rules

It intentionally does not read env files, inspect processes, mutate cache
settings, clear caches, or manage a specific model line. Those are platform
or runtime-host responsibilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Mapping


CACHE_ENV_KEYS = frozenset(
    {
        "OMLX_CACHE_DIR",
        "OMLX_CACHE_MAX_SIZE",
        "OMLX_HOT_CACHE_SIZE",
    }
)

CACHE_CLI_FLAGS = frozenset(
    {
        "--paged-ssd-cache-dir",
        "--paged-ssd-cache-max-size",
        "--hot-cache-max-size",
    }
)

SAFE_TURBOQUANT_ADOPTION_REQUIREMENTS = (
    "Clear SSD + hot cache before any TurboQuant config change",
    "Unload + reload model after settings change",
    "Never mix bit-widths on same model without full cache clear",
)

HIGH_TURBOQUANT_CACHE_SAFETY_RISK = (
    "HIGH — no bits-in-cache-key, no invalidation on config toggle"
)


class CacheProfile(str, Enum):
    """Runtime cache profile label."""

    baseline = "baseline"
    cache_enabled = "cache-enabled"
    not_running = "not_running"
    unknown = "unknown"


@dataclass(frozen=True, slots=True)
class CacheFlags:
    """Normalized oMLX cache flag snapshot."""

    paged_ssd_cache_dir: str | None = None
    paged_ssd_cache_max_size: str | None = None
    hot_cache_max_size: str | None = None

    @property
    def enabled(self) -> bool:
        """Whether any cache flag is configured."""

        return bool(
            self.paged_ssd_cache_dir
            or self.paged_ssd_cache_max_size
            or self.hot_cache_max_size
        )


@dataclass(frozen=True, slots=True)
class CacheProfileSnapshot:
    """Pure cache profile status derived from configured and runtime flags."""

    configured_profile: CacheProfile
    runtime_profile: CacheProfile
    restart_required: bool
    configured_flags: CacheFlags
    runtime_flags: CacheFlags | None = None


@dataclass(frozen=True, slots=True)
class TurboQuantCacheSafety:
    """Cache-safety decision for runtime KV quantization adoption."""

    can_activate: bool
    cache_safety_risk: str
    safe_adoption_requires: tuple[str, ...]


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().strip('"').strip("'")
    return text or None


def normalize_cache_profile(value: CacheProfile | str | None) -> CacheProfile:
    """Normalize raw cache profile labels.

    Invalid or missing profile values become ``unknown``.  This keeps callers
    fail-safe without raising from status-building paths.
    """

    if isinstance(value, CacheProfile):
        return value
    if value is None:
        return CacheProfile.unknown
    try:
        return CacheProfile(str(value))
    except ValueError:
        return CacheProfile.unknown


def normalize_cache_flags(raw: CacheFlags | Mapping[str, Any] | None) -> CacheFlags:
    """Normalize cache flags from platform env or status dictionaries."""

    if isinstance(raw, CacheFlags):
        return raw
    if raw is None:
        return CacheFlags()
    return CacheFlags(
        paged_ssd_cache_dir=_clean(
            raw.get("paged_ssd_cache_dir")
            or raw.get("OMLX_CACHE_DIR")
            or raw.get("cache_dir")
        ),
        paged_ssd_cache_max_size=_clean(
            raw.get("paged_ssd_cache_max_size")
            or raw.get("OMLX_CACHE_MAX_SIZE")
            or raw.get("cache_max_size")
        ),
        hot_cache_max_size=_clean(
            raw.get("hot_cache_max_size")
            or raw.get("OMLX_HOT_CACHE_SIZE")
            or raw.get("hot_cache_size")
        ),
    )


def cache_flags_to_dict(flags: CacheFlags | Mapping[str, Any] | None) -> dict[str, Any]:
    """Return the platform-facing cache flag shape."""

    normalized = normalize_cache_flags(flags)
    return {
        "enabled": normalized.enabled,
        "paged_ssd_cache_dir": normalized.paged_ssd_cache_dir,
        "paged_ssd_cache_max_size": normalized.paged_ssd_cache_max_size,
        "hot_cache_max_size": normalized.hot_cache_max_size,
    }


def cache_profile_from_flags(flags: CacheFlags | Mapping[str, Any] | None) -> CacheProfile:
    """Derive configured cache profile from cache flags."""

    return (
        CacheProfile.cache_enabled
        if normalize_cache_flags(flags).enabled
        else CacheProfile.baseline
    )


def extract_cache_cli_flags(cmdline: str) -> CacheFlags:
    """Extract cache flags from an oMLX command line string."""

    def flag_value(flag: str) -> str | None:
        match = re.search(rf"{re.escape(flag)}\s+(\S+)", cmdline)
        return match.group(1) if match else None

    return CacheFlags(
        paged_ssd_cache_dir=flag_value("--paged-ssd-cache-dir"),
        paged_ssd_cache_max_size=flag_value("--paged-ssd-cache-max-size"),
        hot_cache_max_size=flag_value("--hot-cache-max-size"),
    )


def cache_restart_required(
    configured_profile: CacheProfile | str | None,
    runtime_profile: CacheProfile | str | None,
) -> bool:
    """Whether oMLX must restart for configured cache profile to take effect."""

    configured = normalize_cache_profile(configured_profile)
    runtime = normalize_cache_profile(runtime_profile)
    return runtime not in (CacheProfile.not_running, CacheProfile.unknown) and runtime != configured


def cache_profile_snapshot(
    *,
    configured_flags: CacheFlags | Mapping[str, Any] | None,
    runtime_profile: CacheProfile | str | None,
    runtime_flags: CacheFlags | Mapping[str, Any] | None = None,
) -> CacheProfileSnapshot:
    """Build a pure cache profile snapshot."""

    configured = normalize_cache_flags(configured_flags)
    runtime = normalize_cache_profile(runtime_profile)
    return CacheProfileSnapshot(
        configured_profile=cache_profile_from_flags(configured),
        runtime_profile=runtime,
        restart_required=cache_restart_required(cache_profile_from_flags(configured), runtime),
        configured_flags=configured,
        runtime_flags=normalize_cache_flags(runtime_flags) if runtime_flags is not None else None,
    )


def cache_profile_snapshot_to_dict(snapshot: CacheProfileSnapshot) -> dict[str, Any]:
    """Return a JSON-ready cache profile snapshot."""

    return {
        "configured_profile": snapshot.configured_profile.value,
        "runtime_profile": snapshot.runtime_profile.value,
        "restart_required": snapshot.restart_required,
        "active_flags": cache_flags_to_dict(snapshot.configured_flags),
        "runtime_flags": (
            cache_flags_to_dict(snapshot.runtime_flags)
            if snapshot.runtime_flags is not None
            else None
        ),
    }


def turboquant_cache_safety(
    *,
    bits_in_cache_key: bool = False,
    invalidates_on_config_toggle: bool = False,
    runtime_verified: bool = False,
) -> TurboQuantCacheSafety:
    """Derive safe-adoption requirements for runtime KV quantization.

    Runtime KV quantization may only auto-activate when the runtime both
    isolates bit-width in cache keys and invalidates cache on config toggles.
    The current local oMLX observation does neither, so the default is a
    hard "do not activate" posture.
    """

    can_activate = bool(
        bits_in_cache_key and invalidates_on_config_toggle and runtime_verified
    )
    if can_activate:
        return TurboQuantCacheSafety(
            can_activate=True,
            cache_safety_risk="LOW",
            safe_adoption_requires=(),
        )
    return TurboQuantCacheSafety(
        can_activate=False,
        cache_safety_risk=HIGH_TURBOQUANT_CACHE_SAFETY_RISK,
        safe_adoption_requires=SAFE_TURBOQUANT_ADOPTION_REQUIREMENTS,
    )


def turboquant_cache_safety_to_dict(safety: TurboQuantCacheSafety) -> dict[str, Any]:
    """Return a JSON-ready TurboQuant cache-safety decision."""

    return {
        "can_activate": safety.can_activate,
        "cache_safety_risk": safety.cache_safety_risk,
        "safe_adoption_requires": list(safety.safe_adoption_requires),
    }
