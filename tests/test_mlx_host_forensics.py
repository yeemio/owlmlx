from __future__ import annotations

from pathlib import Path

from owlmlx.runtime.mlx_environment import (
    build_mlx_host_forensics_report,
    host_forensics_to_dict,
    parse_mlx_crash_report,
)


def _sample_report() -> str:
    return "\n".join(
        [
            '{"app_name":"Python","timestamp":"2026-04-13 11:54:10.00 +0800","incident_id":"ABC","os_version":"macOS 26.4.1 (25E253)"}',
            '{"modelCode":"Mac17,6","exception":{"signal":"SIGABRT"},"exceptionReason":{"name":"NSRangeException","composed_message":"*** -[__NSArray0 objectAtIndex:]: index 0 beyond bounds for empty array"},"lastExceptionBacktrace":[{"symbol":"__exceptionPreprocess"},{"symbol":"mlx::core::metal::Device::Device()"}],"usedImages":[{"name":"Python","path":"/opt/homebrew/bin/python3"}]}',
        ]
    )


def test_parse_mlx_crash_report_extracts_signature(tmp_path: Path) -> None:
    report = tmp_path / "Python-2026-04-13-115410.ips"
    report.write_text(_sample_report(), encoding="utf-8")

    parsed = parse_mlx_crash_report(report)

    assert parsed is not None
    assert parsed.exception_name == "NSRangeException"
    assert parsed.signal == "SIGABRT"
    assert parsed.mlx_symbol == "mlx::core::metal::Device::Device()"
    assert parsed.model_code == "Mac17,6"
    assert parsed.python_path == "/opt/homebrew/bin/python3"


def test_parse_mlx_crash_report_ignores_non_matching_report(tmp_path: Path) -> None:
    report = tmp_path / "Python-2026-04-13-000000.ips"
    report.write_text(
        "\n".join(
            [
                '{"app_name":"Python","timestamp":"2026-04-13 00:00:00.00 +0800"}',
                '{"exceptionReason":{"name":"ValueError","composed_message":"plain python error"},"lastExceptionBacktrace":[]}',
            ]
        ),
        encoding="utf-8",
    )

    assert parse_mlx_crash_report(report) is None


def test_build_mlx_host_forensics_report_includes_recent_crash_reports(
    monkeypatch,
    tmp_path: Path,
) -> None:
    report = tmp_path / "Python-2026-04-13-115410.ips"
    report.write_text(_sample_report(), encoding="utf-8")

    monkeypatch.setattr(
        "owlmlx.runtime.mlx_environment.default_environment_candidates",
        lambda **_: (),
    )

    built = build_mlx_host_forensics_report(
        include_known_candidates=False,
        crash_report_directory=tmp_path,
        crash_limit=3,
        quarantine_path=tmp_path / "q.json",
    )
    payload = host_forensics_to_dict(built)

    assert built.blocked is True
    assert payload["contract"]["surface"] == "owlmlx.mlx_host_forensics"
    assert payload["summary"]["crash_report_count"] == 1
    assert payload["crash_reports"][0]["mlx_symbol"] == "mlx::core::metal::Device::Device()"
    assert payload["readiness"]["summary"]["blocked_reason"] == "no safe default mlx-lm python candidates available"
