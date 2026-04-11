from __future__ import annotations

from pathlib import Path

from owlmlx.cache_truth import (
    CACHE_CLI_FLAGS,
    CACHE_ENV_KEYS,
    HIGH_TURBOQUANT_CACHE_SAFETY_RISK,
    SAFE_TURBOQUANT_ADOPTION_REQUIREMENTS,
    CacheFlags,
    CacheProfile,
    cache_flags_to_dict,
    cache_profile_from_flags,
    cache_profile_snapshot,
    cache_profile_snapshot_to_dict,
    cache_restart_required,
    extract_cache_cli_flags,
    normalize_cache_flags,
    normalize_cache_profile,
    turboquant_cache_safety,
    turboquant_cache_safety_to_dict,
)


def test_cache_env_keys_are_omlx_specific() -> None:
    assert CACHE_ENV_KEYS == {
        "OMLX_CACHE_DIR",
        "OMLX_CACHE_MAX_SIZE",
        "OMLX_HOT_CACHE_SIZE",
    }


def test_cache_cli_flags_are_omlx_specific() -> None:
    assert "--paged-ssd-cache-dir" in CACHE_CLI_FLAGS
    assert "--paged-ssd-cache-max-size" in CACHE_CLI_FLAGS
    assert "--hot-cache-max-size" in CACHE_CLI_FLAGS


def test_normalize_cache_profile_accepts_known_values() -> None:
    assert normalize_cache_profile("baseline") is CacheProfile.baseline
    assert normalize_cache_profile("cache-enabled") is CacheProfile.cache_enabled
    assert normalize_cache_profile(CacheProfile.not_running) is CacheProfile.not_running


def test_normalize_cache_profile_invalid_is_unknown() -> None:
    assert normalize_cache_profile("turbo") is CacheProfile.unknown
    assert normalize_cache_profile(None) is CacheProfile.unknown


def test_normalize_cache_flags_from_platform_shape() -> None:
    flags = normalize_cache_flags(
        {
            "paged_ssd_cache_dir": " /tmp/cache ",
            "paged_ssd_cache_max_size": "",
            "hot_cache_max_size": '"8GB"',
        }
    )
    assert flags == CacheFlags(
        paged_ssd_cache_dir="/tmp/cache",
        paged_ssd_cache_max_size=None,
        hot_cache_max_size="8GB",
    )


def test_normalize_cache_flags_from_env_shape() -> None:
    flags = normalize_cache_flags(
        {
            "OMLX_CACHE_DIR": "/tmp/cache",
            "OMLX_CACHE_MAX_SIZE": "64GB",
            "OMLX_HOT_CACHE_SIZE": "8GB",
        }
    )
    assert flags.paged_ssd_cache_dir == "/tmp/cache"
    assert flags.paged_ssd_cache_max_size == "64GB"
    assert flags.hot_cache_max_size == "8GB"


def test_cache_flags_enabled_property() -> None:
    assert CacheFlags().enabled is False
    assert CacheFlags(hot_cache_max_size="8GB").enabled is True


def test_cache_profile_from_flags_baseline() -> None:
    assert cache_profile_from_flags({}) is CacheProfile.baseline


def test_cache_profile_from_flags_cache_enabled() -> None:
    assert cache_profile_from_flags({"OMLX_CACHE_DIR": "/tmp/cache"}) is CacheProfile.cache_enabled


def test_cache_flags_to_dict_preserves_existing_platform_shape() -> None:
    data = cache_flags_to_dict(CacheFlags(paged_ssd_cache_dir="/tmp/cache", hot_cache_max_size="8GB"))
    assert data == {
        "enabled": True,
        "paged_ssd_cache_dir": "/tmp/cache",
        "paged_ssd_cache_max_size": None,
        "hot_cache_max_size": "8GB",
    }


def test_extract_cache_cli_flags_all_values() -> None:
    cmdline = (
        "python -m omlx.cli serve --port 8001 "
        "--paged-ssd-cache-dir /tmp/cache "
        "--paged-ssd-cache-max-size 64GB "
        "--hot-cache-max-size 8GB"
    )
    flags = extract_cache_cli_flags(cmdline)
    assert flags == CacheFlags(
        paged_ssd_cache_dir="/tmp/cache",
        paged_ssd_cache_max_size="64GB",
        hot_cache_max_size="8GB",
    )


def test_extract_cache_cli_flags_missing_values() -> None:
    assert extract_cache_cli_flags("python -m omlx.cli serve") == CacheFlags()


def test_cache_restart_required_when_runtime_differs() -> None:
    assert cache_restart_required("cache-enabled", "baseline") is True


def test_cache_restart_not_required_when_runtime_matches() -> None:
    assert cache_restart_required("cache-enabled", "cache-enabled") is False


def test_cache_restart_not_required_when_runtime_not_running() -> None:
    assert cache_restart_required("cache-enabled", "not_running") is False


def test_cache_restart_not_required_when_runtime_unknown() -> None:
    assert cache_restart_required("cache-enabled", "unknown") is False


def test_cache_profile_snapshot_derives_all_fields() -> None:
    snapshot = cache_profile_snapshot(
        configured_flags={"OMLX_HOT_CACHE_SIZE": "8GB"},
        runtime_profile="baseline",
        runtime_flags={"hot_cache_max_size": None},
    )
    assert snapshot.configured_profile is CacheProfile.cache_enabled
    assert snapshot.runtime_profile is CacheProfile.baseline
    assert snapshot.restart_required is True
    assert snapshot.configured_flags.hot_cache_max_size == "8GB"
    assert snapshot.runtime_flags == CacheFlags()


def test_cache_profile_snapshot_to_dict() -> None:
    snapshot = cache_profile_snapshot(
        configured_flags={},
        runtime_profile="baseline",
    )
    assert cache_profile_snapshot_to_dict(snapshot) == {
        "configured_profile": "baseline",
        "runtime_profile": "baseline",
        "restart_required": False,
        "active_flags": {
            "enabled": False,
            "paged_ssd_cache_dir": None,
            "paged_ssd_cache_max_size": None,
            "hot_cache_max_size": None,
        },
        "runtime_flags": None,
    }


def test_turboquant_default_is_not_safe_to_activate() -> None:
    safety = turboquant_cache_safety()
    assert safety.can_activate is False
    assert safety.cache_safety_risk == HIGH_TURBOQUANT_CACHE_SAFETY_RISK
    assert safety.safe_adoption_requires == SAFE_TURBOQUANT_ADOPTION_REQUIREMENTS


def test_turboquant_can_activate_only_when_runtime_verified_and_cache_safe() -> None:
    unsafe = turboquant_cache_safety(
        bits_in_cache_key=True,
        invalidates_on_config_toggle=True,
        runtime_verified=False,
    )
    safe = turboquant_cache_safety(
        bits_in_cache_key=True,
        invalidates_on_config_toggle=True,
        runtime_verified=True,
    )
    assert unsafe.can_activate is False
    assert safe.can_activate is True
    assert safe.cache_safety_risk == "LOW"
    assert safe.safe_adoption_requires == ()


def test_turboquant_cache_safety_to_dict() -> None:
    data = turboquant_cache_safety_to_dict(turboquant_cache_safety())
    assert data["can_activate"] is False
    assert data["cache_safety_risk"] == HIGH_TURBOQUANT_CACHE_SAFETY_RISK
    assert data["safe_adoption_requires"] == list(SAFE_TURBOQUANT_ADOPTION_REQUIREMENTS)


def test_module_has_no_platform_dependency() -> None:
    source = Path(__file__).parents[1].joinpath("owlmlx", "cache_truth.py").read_text()
    forbidden = [
        "subprocess",
        "httpx",
        "requests",
        "llm_router",
        "ops_dashboard",
        "scripts/",
        "Path(",
        "open(",
    ]
    for pattern in forbidden:
        assert pattern not in source
