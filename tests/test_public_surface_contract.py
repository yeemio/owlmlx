"""Validation test for ``docs/source-of-truth/public-surface.md`` (release floor 3.7A).

This test enforces the narrow boundary contract from
``release-readiness-backlog.md`` §3.7:

- the public-surface document exists
- every linked owlmlx doc path resolves to a real file
- every listed operator script path resolves to a real file
- the text declares the internal-default rule (`internal by default`)
- the text references the runtime-enforced banned-verdict vocabulary
- the text does **not** make any banned positive claim about owlmlx as a
  current release-floor capability
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SURFACE_PATH = REPO_ROOT / "docs" / "source-of-truth" / "public-surface.md"


# Words the harness contract / backlog §4.3 treat as banned current claims for
# any owlmlx surface, mirrored from
# ``owlmlx.comparative_evidence_schema.BANNED_VERDICT_VOCABULARY``.
BANNED_CURRENT_CLAIM_WORDS: tuple[str, ...] = (
    "release-ready",
    "release_ready",
    "parity",
    "equivalent",
    "replaces",
    "replacement",
    "production-ready",
    "production_ready",
    "production-grade",
    "production_grade",
    "superior",
    "wins",
    "beats",
    "matches",
)


def _public_surface_text() -> str:
    assert PUBLIC_SURFACE_PATH.exists(), (
        f"public-surface.md must exist at {PUBLIC_SURFACE_PATH}"
    )
    return PUBLIC_SURFACE_PATH.read_text(encoding="utf-8")


def test_public_surface_document_exists() -> None:
    assert PUBLIC_SURFACE_PATH.is_file(), (
        f"public-surface.md must exist at {PUBLIC_SURFACE_PATH}"
    )


def test_public_surface_lists_supported_label_vocabulary() -> None:
    text = _public_surface_text()
    for label in ("supported", "partial", "experimental", "internal", "not in scope"):
        assert f"`{label}`" in text, f"missing label entry {label!r}"


def test_public_surface_declares_internal_default_rule() -> None:
    text = " ".join(_public_surface_text().lower().split())
    # Strip Markdown backticks so the rule reads cleanly whether the text uses
    # `internal` by default or internal-by-default.
    stripped = text.replace("`", "")
    assert (
        "internal by default" in stripped
        or "internal-by-default" in stripped
    ), "public-surface.md must declare the internal-default rule"


def test_public_surface_references_banned_verdict_vocabulary() -> None:
    """The unsupported-claims section must explicitly link to the schema enforcement."""

    text = _public_surface_text()
    assert "BANNED_VERDICT_VOCABULARY" in text, (
        "public-surface.md must reference BANNED_VERDICT_VOCABULARY so the "
        "doc-level boundary is tied to schema-level enforcement"
    )


def test_public_surface_lists_unsupported_claim_section() -> None:
    text = _public_surface_text()
    # Section heading present (any level)
    assert re.search(
        r"(?im)^#+\s.*unsupported claims",
        text,
    ), "public-surface.md must contain an explicitly-unsupported-claims section"


def _referenced_doc_paths(text: str) -> set[str]:
    """Return repository-relative doc paths cited in the public surface."""

    paths: set[str] = set()
    for match in re.findall(r"`(docs/source-of-truth/[A-Za-z0-9_./-]+\.md)`", text):
        paths.add(match)
    if "`AGENTS.md`" in text:
        paths.add("AGENTS.md")
    return paths


def _referenced_script_paths(text: str) -> set[str]:
    paths: set[str] = set()
    for match in re.findall(r"`(scripts/runtime_[A-Za-z0-9_./-]+\.py)`", text):
        paths.add(match)
    return paths


def test_every_referenced_doc_path_exists() -> None:
    text = _public_surface_text()
    referenced = _referenced_doc_paths(text)
    assert referenced, "expected at least one referenced source-of-truth doc"
    missing = [
        path for path in sorted(referenced) if not (REPO_ROOT / path).is_file()
    ]
    assert not missing, f"public-surface.md references missing docs: {missing}"


def test_every_referenced_script_path_exists() -> None:
    text = _public_surface_text()
    referenced = _referenced_script_paths(text)
    assert referenced, "expected at least one referenced operator script"
    missing = [
        path for path in sorted(referenced) if not (REPO_ROOT / path).is_file()
    ]
    assert not missing, f"public-surface.md references missing scripts: {missing}"


def test_public_surface_lists_supported_release_floor_routes() -> None:
    """Sanity-check that the floors closed in the backlog are reflected here."""

    text = _public_surface_text()
    must_appear = (
        "/v1/runtime/status",
        "/healthz",
        "/v1/runtime/orchestration-status",
        "/v1/runtime/recovery-supervisor-contract",
        "/v1/runtime/termination-recovery-policy",
        "/v1/runtime/comparative-evidence",
        "/v1/runtime/comparative-evidence/history",
    )
    for route in must_appear:
        assert route in text, f"public-surface.md must list HTTP route {route}"


def test_public_surface_lists_runtime_comparative_evidence_script() -> None:
    text = _public_surface_text()
    assert "scripts/runtime_comparative_evidence.py" in text


def test_public_surface_does_not_make_banned_current_claims() -> None:
    """No line may positively assert owlmlx is release-ready / parity / etc.

    Banned words are allowed inside negative or referential contexts (the
    explicit `Explicitly Unsupported Claims` listing, `BANNED_VERDICT_VOCABULARY`
    cross-reference, and the change-rule's deprecation language). Lines that
    use a banned word **as a current positive claim** are rejected.
    """

    text = _public_surface_text()

    # Allowed contexts: lines that include any of these tokens are treated as
    # negative or referential and are excluded from the banned-claim check.
    allowed_context_tokens = (
        "never",
        "not",
        "no ",
        "banned",
        "unsupported",
        "rejects",
        "rejected",
        "explicitly",
        "must",
        "may not",
        "without",
        "outside",
        "mirror",
        "BANNED_VERDICT_VOCABULARY",
        "interim",
        "deprecat",
    )

    in_unsupported_section = False
    for raw_line in text.splitlines():
        stripped_raw = raw_line.strip()
        lowered = stripped_raw.lower()

        # Track whether we are inside the §10 "Explicitly Unsupported Claims"
        # section; banned words appearing there are listing entries, not claims.
        heading_match = re.match(r"^#+\s+(.+?)\s*$", stripped_raw)
        if heading_match:
            heading_text = heading_match.group(1).lower()
            in_unsupported_section = "unsupported claims" in heading_text
            continue

        if not lowered or lowered.startswith("#"):
            continue
        if in_unsupported_section:
            continue
        for banned in BANNED_CURRENT_CLAIM_WORDS:
            if banned not in lowered:
                continue
            if any(token.lower() in lowered for token in allowed_context_tokens):
                continue
            pytest.fail(
                f"public-surface.md line uses banned current-claim word "
                f"{banned!r} without a negative/referential context: {raw_line!r}"
            )


def test_public_surface_does_not_assert_owlmlx_is_replacement_or_parity() -> None:
    """Direct-assertion check, independent of the line-level scan."""

    text = " ".join(_public_surface_text().lower().split())
    forbidden_positive_phrases = (
        "owlmlx is release-ready",
        "owlmlx is production-grade",
        "owlmlx is at parity",
        "owlmlx replaces ",
        "owlmlx is equivalent",
        "owlmlx is a replacement",
        "owlmlx beats",
    )
    for phrase in forbidden_positive_phrases:
        assert phrase not in text, (
            f"public-surface.md must not assert {phrase!r}"
        )


def test_public_surface_records_closed_floor_boundary_without_release_claim() -> None:
    """The doc must reflect 7/7 closure without promoting the claim."""

    text = " ".join(_public_surface_text().lower().split())
    assert "7 / 7" in text and "3.6 external customer evidence" in text, (
        "public-surface.md must record the closed floor-3.6 boundary"
    )
    assert "3.7 public surface freeze" in text, (
        "public-surface.md must record the closed floor-3.7 boundary"
    )
    assert "not a release" in text and "release-ready" in text, (
        "public-surface.md must prevent 7/7 closure from becoming a "
        "release-ready claim"
    )
