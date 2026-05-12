"""Tests for owlmlx.quantization_metadata — Stage 3.1 c4 migration target.

Closes the `owned but still shell-hosted` row for `Quantization metadata
truth` in contract-mapping.md §3.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from owlmlx import (
    QUANTIZATION_METADATA_SURFACE,
    QUANTIZATION_METADATA_VERSION,
    QuantizationMetadata,
    SUPPORTED_QUANT_METHODS,
    build_quantization_metadata,
    quantization_metadata_to_dict,
)
from owlmlx.memory_budget import MachineMemoryProfile
from owlmlx.model_lineage import ModelLineage, normalize_model_lineage
from owlmlx.runtime import FakeBackend, RuntimeKernel
from owlmlx.runtime.server import create_app


def _profile() -> MachineMemoryProfile:
    return MachineMemoryProfile(
        system_memory_gb=8.0,
        system_reserve_gb=2.0,
        serving_budget_gb=6.0,
        warning_threshold_gb=5.0,
    )


def _lineage(**overrides: str) -> ModelLineage:
    raw: dict = dict(
        base_model="qwen3.5-27b",
        quantizer="mlx",
        quant_method="mlx_4bit",
        served_format="mlx-safetensors",
    )
    raw.update(overrides)
    return normalize_model_lineage(raw)


class TestBitWidthParsing:
    """Verify the best-effort bit-width parse over realistic quant_method strings."""

    @pytest.mark.parametrize(
        "quant_method, expected_bits",
        [
            ("mlx_4bit", 4),
            ("mlx_8bit", 8),
            ("4-bit", 4),
            ("8 bit", 8),
            ("Q4", 4),
            ("Q8", 8),
            ("MXFP4", 4),
            ("fp16", 16),
            ("bf16", 16),
            ("fp32", 32),
            ("awq_4bit", 4),
            ("gptq_4bit", 4),
        ],
    )
    def test_recognized_patterns(self, quant_method: str, expected_bits: int) -> None:
        meta = build_quantization_metadata(lineage=_lineage(quant_method=quant_method))
        assert meta.bits == expected_bits, f"{quant_method!r} → {meta.bits} (expected {expected_bits})"

    def test_unparseable_returns_none(self) -> None:
        meta = build_quantization_metadata(
            lineage=_lineage(quant_method="proprietary_zilch")
        )
        assert meta.bits is None

    def test_empty_quant_method_returns_none(self) -> None:
        meta = build_quantization_metadata(lineage=_lineage(quant_method=""))
        assert meta.bits is None


class TestRuntimeSupport:
    def test_known_method_marked_supported(self) -> None:
        meta = build_quantization_metadata(lineage=_lineage(quant_method="mlx_4bit"))
        assert meta.runtime_supported is True
        assert meta.reason_code == "supported_static_quantization"
        assert "4-bit" in meta.reason_message

    def test_unknown_method_marked_unsupported(self) -> None:
        meta = build_quantization_metadata(lineage=_lineage(quant_method="hypotheticalq3"))
        assert meta.runtime_supported is False
        assert meta.reason_code == "unsupported_quantization"

    def test_unquantized_recognized(self) -> None:
        meta = build_quantization_metadata(lineage=_lineage(quant_method=""))
        assert meta.is_static is False
        assert meta.runtime_supported is False
        assert meta.reason_code == "no_quantization"


class TestLineageMissing:
    """When no lineage is available, the contract must return an explicit
    empty signal — not silently report 'no quant'."""

    def test_none_lineage_returns_explicit_signal(self) -> None:
        meta = build_quantization_metadata(lineage=None)
        assert meta.bits is None
        assert meta.is_static is False
        assert meta.runtime_supported is False
        assert meta.reason_code == "lineage_missing"
        assert meta.cache_safety is not None

    def test_none_lineage_does_not_confuse_with_no_quant(self) -> None:
        empty = build_quantization_metadata(lineage=None)
        unquantized = build_quantization_metadata(lineage=_lineage(quant_method=""))
        assert empty.reason_code != unquantized.reason_code


class TestCacheSafetyIntegration:
    def test_cache_safety_defaults_unsafe(self) -> None:
        """Defaults for the three cache-safety inputs are unsafe, so callers
        who forget to wire runtime evidence don't get a permissive verdict."""
        meta = build_quantization_metadata(lineage=_lineage())
        assert meta.cache_safety.can_activate is False
        assert len(meta.cache_safety.safe_adoption_requires) > 0

    def test_all_three_safety_signals_yields_safe(self) -> None:
        meta = build_quantization_metadata(
            lineage=_lineage(),
            bits_in_cache_key=True,
            invalidates_on_config_toggle=True,
            runtime_verified=True,
        )
        assert meta.cache_safety.can_activate is True
        assert meta.cache_safety.safe_adoption_requires == ()


class TestSerialization:
    def test_to_dict_includes_all_stable_sections(self) -> None:
        meta = build_quantization_metadata(lineage=_lineage())
        payload = quantization_metadata_to_dict(meta)
        assert payload["contract"]["surface"] == QUANTIZATION_METADATA_SURFACE
        assert payload["contract"]["version"] == QUANTIZATION_METADATA_VERSION
        for section in ("lineage", "structure", "cache_safety", "reason"):
            assert section in payload, f"missing section: {section}"

    def test_to_dict_exposes_supported_methods(self) -> None:
        meta = build_quantization_metadata(lineage=_lineage())
        payload = quantization_metadata_to_dict(meta)
        assert set(payload["structure"]["supported_methods"]) == SUPPORTED_QUANT_METHODS


class TestRuntimeRoute:
    """Verify the runtime/ consumer chain satisfies the AGENTS rule:
    server.py imports the module, reads its fields via to_dict, and exposes
    them at a stable URL."""

    def test_runtime_quantization_metadata_route_returns_lineage_missing_when_no_model_id(
        self,
    ) -> None:
        client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
        response = client.get("/v1/runtime/quantization-metadata")
        assert response.status_code == 200
        payload = response.json()
        assert payload["contract"]["surface"] == QUANTIZATION_METADATA_SURFACE
        assert payload["reason"]["code"] == "lineage_missing"
        assert payload["structure"]["bits"] is None

    def test_runtime_quantization_metadata_route_resolves_loadability_lineage_records(
        self,
    ) -> None:
        client = TestClient(
            create_app(
                RuntimeKernel(FakeBackend(), profile=_profile()),
                loadability_lineage_records={
                    "qwen3.5-27b-mlx-4bit": {
                        "base_model": "qwen3.5-27b",
                        "quantizer": "mlx",
                        "quant_method": "mlx_4bit",
                        "served_format": "mlx-safetensors",
                    },
                },
            )
        )
        response = client.get(
            "/v1/runtime/quantization-metadata?model_id=qwen3.5-27b-mlx-4bit"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["lineage"]["base_model"] == "qwen3.5-27b"
        assert payload["lineage"]["quant_method"] == "mlx_4bit"
        assert payload["structure"]["bits"] == 4
        assert payload["structure"]["is_static"] is True
        assert payload["structure"]["runtime_supported"] is True
        assert payload["reason"]["code"] == "supported_static_quantization"

    def test_runtime_quantization_metadata_route_unknown_model_id_returns_lineage_missing(
        self,
    ) -> None:
        client = TestClient(create_app(RuntimeKernel(FakeBackend(), profile=_profile())))
        response = client.get("/v1/runtime/quantization-metadata?model_id=not-registered")
        assert response.status_code == 200
        assert response.json()["reason"]["code"] == "lineage_missing"


class TestAGENTSRule:
    """Stage 1 anti-regression rule (AGENTS.md): a new module must have a
    real runtime consumer reading its fields. Verify the three checks
    explicitly so future contributors see the test as the rule's gate."""

    def test_module_is_imported_by_runtime(self) -> None:
        import pathlib
        server_text = pathlib.Path("owlmlx/runtime/server.py").read_text()
        assert "from owlmlx.quantization_metadata import" in server_text

    def test_module_has_real_function_bodies(self) -> None:
        """The module must do work, not just declare a frozen dataclass.
        build_quantization_metadata has real parsing + classification logic."""
        meta_a = build_quantization_metadata(lineage=_lineage(quant_method="mlx_4bit"))
        meta_b = build_quantization_metadata(lineage=_lineage(quant_method="unknown"))
        # Different inputs produce different decisions — this is real
        # behavior, not literal-string returns.
        assert meta_a.runtime_supported != meta_b.runtime_supported
        assert meta_a.reason_code != meta_b.reason_code

    def test_dataclass_fields_are_read_by_runtime(self) -> None:
        """quantization_metadata_to_dict reads QuantizationMetadata fields
        by name (meta.bits, meta.is_static, etc.) and runtime/server.py
        calls it for the HTTP route."""
        meta = build_quantization_metadata(lineage=_lineage())
        payload = quantization_metadata_to_dict(meta)
        # Field reads visible in the payload:
        assert payload["lineage"]["base_model"] == meta.base_model
        assert payload["structure"]["bits"] == meta.bits
        assert payload["structure"]["is_static"] == meta.is_static
        assert payload["structure"]["runtime_supported"] == meta.runtime_supported
        assert payload["reason"]["code"] == meta.reason_code
