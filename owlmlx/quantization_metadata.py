"""Runtime-owned quantization metadata contract.

Derives a stable, structured view of an artifact's quantization from
``ModelLineage`` artifact-string fields plus runtime cache-safety truth.

Migration provenance
--------------------

`contract-mapping.md` §3 listed ``Quantization metadata truth`` as
``owned but still shell-hosted`` because owlmlx had partial coverage —
``model_lineage`` strings (``base_model`` / ``quantizer`` /
``quant_method`` / ``served_format``) and ``cache_truth.turboquant_cache_safety``
— but no single source-of-truth surface. Shell consumers had to parse
the ``quant_method`` string themselves to recover bit-width and static-
vs-dynamic structure.

This module is the consolidation. Stage 3.1 c4 migration target.

Stability boundary
------------------

The contract is intentionally narrow:

- ``bits`` is best-effort parsed from the artifact's ``quant_method``
  string. Callers should treat ``None`` as "unknown", not "no quant".
- ``runtime_supported`` is checked against
  :data:`SUPPORTED_QUANT_METHODS`. Adding a method to that set requires
  a corresponding runtime implementation path validated by tests
  (AGENTS anti-regression rule).
- ``cache_safety`` is the existing
  :func:`owlmlx.cache_truth.turboquant_cache_safety` decision, included
  verbatim so consumers don't have to know two surfaces.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .cache_truth import TurboQuantCacheSafety, turboquant_cache_safety, turboquant_cache_safety_to_dict
from .model_lineage import ModelLineage


QUANTIZATION_METADATA_SURFACE = "owlmlx.quantization_metadata"
QUANTIZATION_METADATA_VERSION = "v1"


# Runtime-supported quant methods. Adding an entry requires a real
# implementation path validated by tests — this set is checked in tests
# against the AGENTS anti-regression rule.
SUPPORTED_QUANT_METHODS = frozenset(
    {
        "mlx_4bit",
        "mlx_8bit",
        "mlx_int4",
        "mlx_int8",
        "MXFP4",
        "Q4",
        "Q8",
        "awq_4bit",
        "gptq_4bit",
    }
)


@dataclass(frozen=True, slots=True)
class QuantizationMetadata:
    """Runtime-owned quantization metadata for a served-model artifact."""

    base_model: str
    quantizer: str
    quant_method: str
    served_format: str
    bits: int | None
    is_static: bool
    runtime_supported: bool
    cache_safety: TurboQuantCacheSafety
    reason_code: str
    reason_message: str


_BIT_RE = re.compile(r"(\d+)\s*-?\s*bit", re.IGNORECASE)
_Q_RE = re.compile(r"\bq(\d+)\b", re.IGNORECASE)


def _parse_bits(quant_method: str) -> int | None:
    """Best-effort bit-width parse from a free-form quant_method string.

    Recognized patterns:
    - "4bit" / "4-bit" / "4 bit" → 4
    - "Q4" / "Q8" → 4 / 8
    - "MXFP4" → 4
    - "fp16" / "bf16" → 16
    - "fp32" → 32
    Returns None on unrecognized input.
    """
    if not quant_method:
        return None
    s = quant_method.strip()
    if not s:
        return None
    m = _BIT_RE.search(s)
    if m:
        return int(m.group(1))
    m = _Q_RE.search(s)
    if m:
        return int(m.group(1))
    sl = s.lower()
    if "mxfp4" in sl:
        return 4
    if "fp16" in sl or "bf16" in sl:
        return 16
    if "fp32" in sl:
        return 32
    return None


def build_quantization_metadata(
    *,
    lineage: ModelLineage | None,
    bits_in_cache_key: bool = False,
    invalidates_on_config_toggle: bool = False,
    runtime_verified: bool = False,
) -> QuantizationMetadata:
    """Build the runtime-owned quantization metadata contract.

    ``lineage`` may be ``None`` when no model is loaded; in that case the
    contract reports ``lineage_missing`` and surfaces unsafe cache-safety
    defaults so callers cannot mistake the empty signal for "no quant".

    The three keyword booleans pass through to
    :func:`turboquant_cache_safety`. Defaults are unsafe so a caller that
    forgets to wire runtime evidence does not get a permissive verdict.
    """
    cache_safety = turboquant_cache_safety(
        bits_in_cache_key=bits_in_cache_key,
        invalidates_on_config_toggle=invalidates_on_config_toggle,
        runtime_verified=runtime_verified,
    )

    if lineage is None:
        return QuantizationMetadata(
            base_model="",
            quantizer="",
            quant_method="",
            served_format="",
            bits=None,
            is_static=False,
            runtime_supported=False,
            cache_safety=cache_safety,
            reason_code="lineage_missing",
            reason_message=(
                "No model lineage available; quantization metadata cannot be derived"
            ),
        )

    quant_method = lineage.quant_method
    bits = _parse_bits(quant_method)
    is_static = bool(quant_method)
    runtime_supported = quant_method in SUPPORTED_QUANT_METHODS

    if not quant_method:
        reason_code = "no_quantization"
        reason_message = "Model is unquantized (full-precision weights)"
    elif runtime_supported:
        reason_code = "supported_static_quantization"
        reason_message = (
            f"Runtime supports static {quant_method} quantization "
            f"({bits}-bit)" if bits is not None
            else f"Runtime supports static {quant_method} quantization"
        )
    else:
        reason_code = "unsupported_quantization"
        reason_message = (
            f"quant_method={quant_method!r} is not in the runtime-supported "
            f"set; callers must treat the model as opaque until a runtime "
            f"implementation path is added"
        )

    return QuantizationMetadata(
        base_model=lineage.base_model,
        quantizer=lineage.quantizer,
        quant_method=quant_method,
        served_format=lineage.served_format,
        bits=bits,
        is_static=is_static,
        runtime_supported=runtime_supported,
        cache_safety=cache_safety,
        reason_code=reason_code,
        reason_message=reason_message,
    )


def quantization_metadata_to_dict(meta: QuantizationMetadata) -> dict[str, Any]:
    """Serialize the contract for HTTP consumers."""
    return {
        "contract": {
            "surface": QUANTIZATION_METADATA_SURFACE,
            "version": QUANTIZATION_METADATA_VERSION,
            "stable_sections": [
                "lineage",
                "structure",
                "cache_safety",
                "reason",
            ],
        },
        "lineage": {
            "base_model": meta.base_model,
            "quantizer": meta.quantizer,
            "quant_method": meta.quant_method,
            "served_format": meta.served_format,
        },
        "structure": {
            "bits": meta.bits,
            "is_static": meta.is_static,
            "runtime_supported": meta.runtime_supported,
            "supported_methods": sorted(SUPPORTED_QUANT_METHODS),
        },
        "cache_safety": turboquant_cache_safety_to_dict(meta.cache_safety),
        "reason": {
            "code": meta.reason_code,
            "message": meta.reason_message,
        },
    }


__all__ = [
    "QUANTIZATION_METADATA_SURFACE",
    "QUANTIZATION_METADATA_VERSION",
    "SUPPORTED_QUANT_METHODS",
    "QuantizationMetadata",
    "build_quantization_metadata",
    "quantization_metadata_to_dict",
]
