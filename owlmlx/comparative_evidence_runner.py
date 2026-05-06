"""Runtime-owned measured comparative-evidence runner primitives.

This module owns the narrow execution and aggregation primitives that
``scripts/runtime_comparative_evidence.py`` ``run-measured-short-prompt``
operator entry consumes. It does NOT import OwlOps, OwlCoda, the desktop
UI, or `/Users/yeemio/AI/Agent`. Reference and owlmlx runtimes are invoked
through caller-supplied subprocess argv lists.

It is the smallest honest path to a real `verdict_grade = "measured"`
record per ``docs/source-of-truth/comparative-evidence-harness-contract.md``.

Test discipline:

- unit tests use deterministic fake commands (e.g. ``python3 -c "..."``)
  so the runner is exercised without requiring 58G live model weights
- the live same-host measured run is left to a downstream Codex review
  lane when the runner is ready

This module never fakes measurements. If a subprocess fails to emit any
stdout, the attempt is recorded as a failure and the aggregate verdict
falls back to ``inconclusive`` or ``rejected`` per the contract.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import psutil


_RSS_SAMPLE_INTERVAL_S = 0.05


@dataclass(frozen=True, slots=True)
class RuntimeRunnerConfig:
    """One runtime's invocation contract for the measured runner.

    ``external_pids``, ``external_pid_file``, and ``external_listener_ports``
    declare process-tree roots that the runner should also sample alongside the
    spawned wrapper PID. They exist because some reference runtimes (notably
    ``omlx serve``) live in a long-running server process that the runner must
    reach into for honest RSS measurement. The wrapper subprocess (e.g. an HTTP
    client) is not where the work happens for those topologies. Listener-port
    discovery is refreshed during the attempt so service restarts and PID drift
    remain visible in the RSS evidence.

    ``first_token_strategy`` accepts:

    - ``first_nonempty_chunk`` (default): mark first-token at the first non-
      empty stdout chunk
    - ``after_marker:<substring>``: ignore stdout lines until one contains the
      substring; mark first-token at the next non-empty line after that
    - ``regex:<python pattern>``: match each non-empty stdout line against the
      pattern; mark first-token at the first matching line
    """

    runtime_id: str
    runtime_version: str
    argv: tuple[str, ...]
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    timeout_s: float = 60.0
    first_token_strategy: str = "first_nonempty_chunk"
    tokens_method: str = "max_tokens"
    external_pids: tuple[int, ...] = ()
    external_pid_file: str | None = None
    external_listener_ports: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkloadInputs:
    """The shared workload all configured runtimes must execute."""

    prompt: str
    decode_max_tokens: int
    decode_temperature: float
    model_id: str
    model_path: str
    model_quantization: str
    prompt_set_hash: str
    serving_budget_bytes: int
    workload_class: str = "single_prompt_short"


@dataclass(frozen=True, slots=True)
class AttemptResult:
    """Per-attempt measurement plus raw artifact pointers."""

    runtime_id: str
    attempt_index: int
    ok: bool
    failure_cause: str | None
    wall_clock_ms: float
    first_token_latency_ms: float | None
    throughput_tokens_per_second: float | None
    peak_resident_set_bytes: int
    generated_token_count: int
    return_code: int | None
    stdout_path: str
    stderr_path: str
    rss_samples_path: str
    command_argv: tuple[str, ...]
    started_at_iso: str
    completed_at_iso: str


@dataclass(frozen=True, slots=True)
class RuntimeAggregate:
    """Per-runtime aggregated measurement across repeats."""

    runtime_id: str
    runtime_version: str
    attempts: tuple[AttemptResult, ...]
    completed_request_count: int
    failure_count: int
    failure_causes: tuple[str, ...]
    wall_clock_ms: float
    first_token_latency_ms: float
    throughput_tokens_per_second: float
    peak_resident_set_bytes: int


def _now_iso_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _substitute_placeholders(
    argv: Sequence[str],
    *,
    workload: WorkloadInputs,
) -> tuple[str, ...]:
    """Substitute supported placeholders in the argv template."""

    mapping = {
        "prompt": workload.prompt,
        "max_tokens": str(workload.decode_max_tokens),
        "temperature": str(workload.decode_temperature),
        "model_id": workload.model_id,
        "model_path": workload.model_path,
    }
    rendered: list[str] = []
    for token in argv:
        try:
            rendered.append(token.format(**mapping))
        except (KeyError, IndexError, ValueError):
            rendered.append(token)
    return tuple(rendered)


def _count_generated_tokens(
    *,
    method: str,
    stdout_text: str,
    decode_max_tokens: int,
) -> int:
    method = (method or "max_tokens").strip()
    if method == "max_tokens":
        return int(decode_max_tokens) if stdout_text.strip() else 0
    if method == "stdout_word_count":
        return len(stdout_text.split())
    if method == "stdout_line_count":
        return sum(1 for line in stdout_text.splitlines() if line.strip())
    if method.startswith("json_field:"):
        field_name = method.split(":", 1)[1].strip()
        for line in reversed(stdout_text.splitlines()):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping) and field_name in payload:
                value = payload[field_name]
                if isinstance(value, (int, float)):
                    return int(value)
        return 0
    return int(decode_max_tokens) if stdout_text.strip() else 0


def _resolve_external_pids(
    *,
    static_pids: Sequence[int],
    pid_file: str | None,
) -> tuple[int, ...]:
    """Combine declared external PIDs with ones read from an optional file.

    ``pid_file`` is treated as one PID per line. Lines that are empty or
    start with ``#`` are ignored. Non-integer lines are ignored silently so
    a harmless trailing newline does not break sampling. Missing or
    unreadable files are silently treated as empty.
    """

    resolved: list[int] = [int(p) for p in static_pids]
    if pid_file:
        try:
            text = Path(pid_file).read_text(encoding="utf-8")
        except OSError:
            text = ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                resolved.append(int(line))
            except ValueError:
                continue
    return _dedupe_pids(resolved)


def _dedupe_pids(pids: Sequence[int]) -> tuple[int, ...]:
    deduped: list[int] = []
    seen: set[int] = set()
    for raw_pid in pids:
        pid = int(raw_pid)
        if pid not in seen:
            seen.add(pid)
            deduped.append(pid)
    return tuple(deduped)


def _listen_port_for_connection(connection: Any) -> int | None:
    try:
        laddr = connection.laddr
    except AttributeError:
        return None
    port = getattr(laddr, "port", None)
    if port is not None:
        return int(port)
    try:
        if len(laddr) >= 2:
            return int(laddr[1])
    except (TypeError, ValueError):
        return None
    return None


def _resolve_listener_pids(*, ports: Sequence[int]) -> tuple[int, ...]:
    """Resolve current LISTEN owner PIDs for local TCP ports.

    The measured runner samples long-running reference services by process
    tree. Static PIDs are useful for initial attribution, but live services can
    restart behind the same port. Resolving listener owners on each RSS sample
    keeps those PID changes represented in evidence artifacts.
    """

    wanted = {int(port) for port in ports if int(port) > 0}
    if not wanted:
        return ()
    resolved: list[int] = []
    try:
        connections = psutil.net_connections(kind="tcp")
    except (psutil.Error, OSError):
        connections = []
    for connection in connections:
        if connection.pid is None:
            continue
        if connection.status != psutil.CONN_LISTEN:
            continue
        port = _listen_port_for_connection(connection)
        if port in wanted:
            resolved.append(int(connection.pid))
    if not resolved:
        resolved.extend(_resolve_listener_pids_with_lsof(ports=tuple(wanted)))
    return _dedupe_pids(resolved)


def _resolve_listener_pids_with_lsof(*, ports: Sequence[int]) -> tuple[int, ...]:
    resolved: list[int] = []
    for port in sorted({int(port) for port in ports if int(port) > 0}):
        try:
            completed = subprocess.run(
                ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            continue
        for raw_line in completed.stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                resolved.append(int(line))
            except ValueError:
                continue
    return _dedupe_pids(resolved)


class _RssSampler:
    """Background-thread RSS sampler over multiple process trees.

    Sampling discipline:

    - on each tick, walk every configured root PID plus its live descendants
      (``psutil.Process(...).children(recursive=True)``)
    - record per-PID RSS in the JSONL artifact for reproducibility
    - the per-tick aggregate is the **sum** of RSS across live PIDs at that
      instant; the reported ``peak`` is the maximum of those per-tick sums
    - this conservative aggregate over-counts shared pages. The trade-off is
      acknowledged in the run summary; the alternative of reporting a single
      process's RSS would silently undercount runtimes that fan out into
      child workers (e.g. owlmlx's MLX runner) or that live in an external
      long-running server (e.g. ``omlx serve``)
    """

    def __init__(
        self,
        *,
        root_pids: Sequence[int],
        dynamic_pid_files: Sequence[str] = (),
        dynamic_listener_ports: Sequence[int] = (),
        output_path: Path,
    ) -> None:
        self._root_pids = list(int(pid) for pid in root_pids)
        self._dynamic_pid_files = tuple(str(path) for path in dynamic_pid_files if path)
        self._dynamic_listener_ports = tuple(
            int(port) for port in dynamic_listener_ports if int(port) > 0
        )
        self._output_path = output_path
        self._stop = threading.Event()
        self._peak = 0
        self._thread: threading.Thread | None = None
        self._samples: list[dict[str, Any]] = []
        self._last_listener_pids: tuple[int, ...] = ()
        self._last_listener_refresh_s: float = 0.0

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> int:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        try:
            self._output_path.parent.mkdir(parents=True, exist_ok=True)
            with self._output_path.open("w", encoding="utf-8") as stream:
                for sample in self._samples:
                    stream.write(json.dumps(sample, sort_keys=True))
                    stream.write("\n")
        except OSError:
            pass
        return self._peak

    def _resolved_root_pids(self) -> list[int]:
        roots = list(self._root_pids)
        for pid_file in self._dynamic_pid_files:
            roots.extend(_resolve_external_pids(static_pids=(), pid_file=pid_file))
        if self._dynamic_listener_ports:
            now_s = time.monotonic()
            if now_s - self._last_listener_refresh_s >= 0.5:
                self._last_listener_pids = _resolve_listener_pids(
                    ports=self._dynamic_listener_ports
                )
                self._last_listener_refresh_s = now_s
            roots.extend(self._last_listener_pids)
        deduped: list[int] = []
        seen: set[int] = set()
        for pid in roots:
            if pid in seen:
                continue
            seen.add(pid)
            deduped.append(pid)
        return deduped

    def _collect_tree_rss(self, root_pids: Sequence[int]) -> dict[str, int]:
        """Return ``{pid: rss_bytes}`` for live processes across all roots."""

        per_pid: dict[str, int] = {}
        for root in root_pids:
            try:
                proc = psutil.Process(root)
            except psutil.Error:
                continue
            try:
                per_pid[str(root)] = int(proc.memory_info().rss)
            except psutil.Error:
                pass
            try:
                children = proc.children(recursive=True)
            except psutil.Error:
                children = []
            for child in children:
                try:
                    per_pid[str(child.pid)] = int(child.memory_info().rss)
                except psutil.Error:
                    continue
        return per_pid

    def _run(self) -> None:
        if not self._root_pids:
            return
        while not self._stop.is_set():
            resolved_root_pids = self._resolved_root_pids()
            per_pid = self._collect_tree_rss(resolved_root_pids)
            if not per_pid:
                # All tracked processes have exited.
                break
            tick_total = sum(per_pid.values())
            self._peak = max(self._peak, tick_total)
            self._samples.append(
                {
                    "t_s": round(time.monotonic(), 6),
                    "tracked_root_pids": list(self._root_pids),
                    "dynamic_pid_files": list(self._dynamic_pid_files),
                    "dynamic_listener_ports": list(self._dynamic_listener_ports),
                    "resolved_root_pids": list(resolved_root_pids),
                    "per_pid_rss_bytes": per_pid,
                    "tick_total_rss_bytes": tick_total,
                }
            )
            self._stop.wait(_RSS_SAMPLE_INTERVAL_S)


class _FirstTokenDetector:
    """Stateful first-token detector for the supported strategies.

    Strategies (per ``RuntimeRunnerConfig.first_token_strategy``):

    - ``first_nonempty_chunk`` (default): mark first-token at the first
      non-empty stdout line
    - ``after_marker:<substring>``: ignore lines until one contains
      ``substring``; mark first-token at the next non-empty line after that
    - ``regex:<python regex>``: mark first-token at the first non-empty line
      matching the regex
    """

    def __init__(self, strategy: str) -> None:
        import re as _re

        spec = (strategy or "first_nonempty_chunk").strip()
        self._strategy = spec
        self._marker: str | None = None
        self._marker_seen: bool = False
        self._regex: Any | None = None
        if spec == "first_nonempty_chunk":
            return
        if spec.startswith("after_marker:"):
            self._marker = spec[len("after_marker:"):]
            return
        if spec.startswith("regex:"):
            pattern = spec[len("regex:"):]
            try:
                self._regex = _re.compile(pattern)
            except _re.error as exc:
                raise ValueError(
                    f"invalid first_token_strategy regex {pattern!r}: {exc}"
                ) from exc
            return
        # Unknown strategies fall back to the safe default rather than crashing
        # mid-run; tests cover the explicit error path on config load.
        self._strategy = "first_nonempty_chunk"

    @property
    def strategy(self) -> str:
        return self._strategy

    def observe(self, line: str) -> bool:
        """Return True when this line counts as the first generated token."""

        stripped = line.strip()
        if not stripped:
            return False
        if self._strategy == "first_nonempty_chunk":
            return True
        if self._marker is not None:
            if not self._marker_seen:
                if self._marker in line:
                    self._marker_seen = True
                return False
            return True
        if self._regex is not None:
            return bool(self._regex.search(line))
        return True


def execute_attempt(
    *,
    runtime_config: RuntimeRunnerConfig,
    workload: WorkloadInputs,
    attempt_index: int,
    artifact_dir: Path,
) -> AttemptResult:
    """Execute one subprocess attempt and return its measurement.

    The runner streams stdout in line-buffered mode to detect the first
    non-empty chunk; that chunk's monotonic timestamp becomes the first-
    token latency. RSS is sampled in a background thread. Stdout, stderr,
    and RSS samples are written to per-attempt artifact files.
    """

    argv = _substitute_placeholders(runtime_config.argv, workload=workload)
    if not argv:
        return _failed_attempt(
            runtime_config=runtime_config,
            attempt_index=attempt_index,
            artifact_dir=artifact_dir,
            failure_cause="harness_runtime_invocation_error_empty_argv",
            command_argv=argv,
        )

    artifact_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = artifact_dir / f"{runtime_config.runtime_id}_attempt{attempt_index}.stdout.txt"
    stderr_path = artifact_dir / f"{runtime_config.runtime_id}_attempt{attempt_index}.stderr.txt"
    rss_path = artifact_dir / f"{runtime_config.runtime_id}_attempt{attempt_index}.rss.jsonl"

    env = os.environ.copy()
    env.update({str(key): str(value) for key, value in runtime_config.env.items()})

    started_iso = _now_iso_utc()
    started_monotonic = time.monotonic()

    try:
        process = subprocess.Popen(
            list(argv),
            cwd=runtime_config.cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            text=True,
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        completed_iso = _now_iso_utc()
        wall_clock_ms = (time.monotonic() - started_monotonic) * 1000.0
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(f"runner_spawn_error: {exc!r}\n", encoding="utf-8")
        rss_path.write_text("", encoding="utf-8")
        return AttemptResult(
            runtime_id=runtime_config.runtime_id,
            attempt_index=attempt_index,
            ok=False,
            failure_cause="harness_runtime_invocation_error_spawn_failed",
            wall_clock_ms=wall_clock_ms,
            first_token_latency_ms=None,
            throughput_tokens_per_second=None,
            peak_resident_set_bytes=0,
            generated_token_count=0,
            return_code=None,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            rss_samples_path=str(rss_path),
            command_argv=argv,
            started_at_iso=started_iso,
            completed_at_iso=completed_iso,
        )

    external_pids = _resolve_external_pids(
        static_pids=runtime_config.external_pids,
        pid_file=runtime_config.external_pid_file,
    )
    listener_pids = _resolve_listener_pids(
        ports=runtime_config.external_listener_ports,
    )
    root_pids: list[int] = [process.pid, *external_pids, *listener_pids]
    dynamic_pid_files = (
        (runtime_config.external_pid_file,)
        if runtime_config.external_pid_file
        else ()
    )
    sampler = _RssSampler(
        root_pids=root_pids,
        dynamic_pid_files=dynamic_pid_files,
        dynamic_listener_ports=runtime_config.external_listener_ports,
        output_path=rss_path,
    )
    sampler.start()

    detector = _FirstTokenDetector(runtime_config.first_token_strategy)

    stdout_chunks: list[str] = []
    first_token_monotonic: float | None = None
    timed_out = False

    try:
        assert process.stdout is not None
        for line in process.stdout:
            if first_token_monotonic is None and detector.observe(line):
                first_token_monotonic = time.monotonic()
            stdout_chunks.append(line)
            if (time.monotonic() - started_monotonic) > runtime_config.timeout_s:
                timed_out = True
                break
        if timed_out:
            try:
                process.kill()
            except OSError:
                pass
        return_code = process.wait(timeout=max(runtime_config.timeout_s, 5.0))
        stderr_text = process.stderr.read() if process.stderr is not None else ""
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            process.kill()
        except OSError:
            pass
        return_code = process.wait()
        stderr_text = process.stderr.read() if process.stderr is not None else ""
    finally:
        peak_rss = sampler.stop()

    completed_iso = _now_iso_utc()
    wall_clock_ms = (time.monotonic() - started_monotonic) * 1000.0
    stdout_text = "".join(stdout_chunks)

    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")

    if timed_out:
        return AttemptResult(
            runtime_id=runtime_config.runtime_id,
            attempt_index=attempt_index,
            ok=False,
            failure_cause="harness_runtime_invocation_error_timeout",
            wall_clock_ms=wall_clock_ms,
            first_token_latency_ms=None,
            throughput_tokens_per_second=None,
            peak_resident_set_bytes=peak_rss,
            generated_token_count=0,
            return_code=return_code,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            rss_samples_path=str(rss_path),
            command_argv=argv,
            started_at_iso=started_iso,
            completed_at_iso=completed_iso,
        )

    if return_code != 0:
        return AttemptResult(
            runtime_id=runtime_config.runtime_id,
            attempt_index=attempt_index,
            ok=False,
            failure_cause="harness_runtime_invocation_error_non_zero_exit",
            wall_clock_ms=wall_clock_ms,
            first_token_latency_ms=None,
            throughput_tokens_per_second=None,
            peak_resident_set_bytes=peak_rss,
            generated_token_count=0,
            return_code=return_code,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            rss_samples_path=str(rss_path),
            command_argv=argv,
            started_at_iso=started_iso,
            completed_at_iso=completed_iso,
        )

    if first_token_monotonic is None:
        return AttemptResult(
            runtime_id=runtime_config.runtime_id,
            attempt_index=attempt_index,
            ok=False,
            failure_cause="first_token_latency_unobservable",
            wall_clock_ms=wall_clock_ms,
            first_token_latency_ms=None,
            throughput_tokens_per_second=None,
            peak_resident_set_bytes=peak_rss,
            generated_token_count=0,
            return_code=return_code,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            rss_samples_path=str(rss_path),
            command_argv=argv,
            started_at_iso=started_iso,
            completed_at_iso=completed_iso,
        )

    first_token_latency_ms = (first_token_monotonic - started_monotonic) * 1000.0
    generated_tokens = _count_generated_tokens(
        method=runtime_config.tokens_method,
        stdout_text=stdout_text,
        decode_max_tokens=workload.decode_max_tokens,
    )
    throughput = (
        (generated_tokens / (wall_clock_ms / 1000.0))
        if wall_clock_ms > 0 and generated_tokens > 0
        else 0.0
    )

    return AttemptResult(
        runtime_id=runtime_config.runtime_id,
        attempt_index=attempt_index,
        ok=True,
        failure_cause=None,
        wall_clock_ms=wall_clock_ms,
        first_token_latency_ms=first_token_latency_ms,
        throughput_tokens_per_second=throughput,
        peak_resident_set_bytes=peak_rss,
        generated_token_count=generated_tokens,
        return_code=return_code,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        rss_samples_path=str(rss_path),
        command_argv=argv,
        started_at_iso=started_iso,
        completed_at_iso=completed_iso,
    )


def _failed_attempt(
    *,
    runtime_config: RuntimeRunnerConfig,
    attempt_index: int,
    artifact_dir: Path,
    failure_cause: str,
    command_argv: tuple[str, ...],
) -> AttemptResult:
    started_iso = completed_iso = _now_iso_utc()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = artifact_dir / f"{runtime_config.runtime_id}_attempt{attempt_index}.stdout.txt"
    stderr_path = artifact_dir / f"{runtime_config.runtime_id}_attempt{attempt_index}.stderr.txt"
    rss_path = artifact_dir / f"{runtime_config.runtime_id}_attempt{attempt_index}.rss.jsonl"
    stdout_path.write_text("", encoding="utf-8")
    stderr_path.write_text(f"{failure_cause}\n", encoding="utf-8")
    rss_path.write_text("", encoding="utf-8")
    return AttemptResult(
        runtime_id=runtime_config.runtime_id,
        attempt_index=attempt_index,
        ok=False,
        failure_cause=failure_cause,
        wall_clock_ms=0.0,
        first_token_latency_ms=None,
        throughput_tokens_per_second=None,
        peak_resident_set_bytes=0,
        generated_token_count=0,
        return_code=None,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        rss_samples_path=str(rss_path),
        command_argv=command_argv,
        started_at_iso=started_iso,
        completed_at_iso=completed_iso,
    )


def aggregate_runtime(
    *,
    runtime_config: RuntimeRunnerConfig,
    attempts: Sequence[AttemptResult],
) -> RuntimeAggregate:
    """Aggregate per-attempt measurements into one runtime entry."""

    successes = [a for a in attempts if a.ok]
    failures = [a for a in attempts if not a.ok]

    if successes:
        wall_clock_ms = sum(a.wall_clock_ms for a in successes) / len(successes)
        first_token_latency_ms = sum(
            float(a.first_token_latency_ms or 0.0) for a in successes
        ) / len(successes)
        throughput = sum(
            float(a.throughput_tokens_per_second or 0.0) for a in successes
        ) / len(successes)
    else:
        wall_clock_ms = 0.0
        first_token_latency_ms = 0.0
        throughput = 0.0

    peak_rss = max((a.peak_resident_set_bytes for a in attempts), default=0)
    failure_causes = tuple(
        sorted({a.failure_cause for a in failures if a.failure_cause})
    )

    return RuntimeAggregate(
        runtime_id=runtime_config.runtime_id,
        runtime_version=runtime_config.runtime_version,
        attempts=tuple(attempts),
        completed_request_count=len(successes),
        failure_count=len(failures),
        failure_causes=failure_causes,
        wall_clock_ms=wall_clock_ms,
        first_token_latency_ms=first_token_latency_ms,
        throughput_tokens_per_second=throughput,
        peak_resident_set_bytes=peak_rss,
    )


def compute_verdict(
    *,
    aggregates: Sequence[RuntimeAggregate],
    expected_repeats: int,
    workload: WorkloadInputs,
    host_class: str,
) -> tuple[str, str]:
    """Return ``(verdict_grade, verdict_text)`` for a set of runtime aggregates.

    Policy:

    - if every runtime has ``completed_request_count >= expected_repeats`` and
      no failures, emit ``measured`` with throughput comparison
    - if at least one runtime has zero successful attempts, emit ``rejected``
      with the first failing runtime's failure cause
    - otherwise (partial success), emit ``inconclusive`` with the union of
      failure causes
    """

    if expected_repeats <= 0:
        raise ValueError("expected_repeats must be positive")

    if len(aggregates) < 2:
        raise ValueError("at least two runtimes are required for a comparative record")

    fully_failed = [a for a in aggregates if a.completed_request_count == 0]
    if fully_failed:
        first = fully_failed[0]
        cause = first.failure_causes[0] if first.failure_causes else "harness_runtime_invocation_error"
        text = (
            f"rejected: {first.runtime_id}_runtime_invocation_failed:{cause} on "
            f"host_class={host_class}, workload_class={workload.workload_class}"
        )
        return "rejected", text

    fully_successful = all(
        agg.completed_request_count >= expected_repeats and agg.failure_count == 0
        for agg in aggregates
    )
    if not fully_successful:
        causes = sorted(
            {cause for agg in aggregates for cause in agg.failure_causes}
        )
        joined = ",".join(causes) if causes else "partial_repeat_success"
        text = (
            f"inconclusive: {joined} on "
            f"host_class={host_class}, workload_class={workload.workload_class}"
        )
        return "inconclusive", text

    primary, reference = aggregates[0], aggregates[1]
    text = (
        f"measured: {primary.runtime_id} tokens_per_second "
        f"{primary.throughput_tokens_per_second:.4f} vs "
        f"{reference.runtime_id} tokens_per_second "
        f"{reference.throughput_tokens_per_second:.4f} on "
        f"host_class={host_class}, workload_class={workload.workload_class}"
    )
    return "measured", text


def aggregate_to_record_runtime(
    aggregate: RuntimeAggregate,
) -> dict[str, Any]:
    """Serialize a runtime aggregate to the record's runtime entry shape."""

    measurement: dict[str, Any] = {
        "throughput_tokens_per_second": float(aggregate.throughput_tokens_per_second),
        "first_token_latency_ms": float(aggregate.first_token_latency_ms),
        "peak_resident_set_bytes": int(aggregate.peak_resident_set_bytes),
        "wall_clock_ms": float(aggregate.wall_clock_ms),
        "completed_request_count": int(aggregate.completed_request_count),
        "failure_count": int(aggregate.failure_count),
    }
    if aggregate.failure_count > 0 or aggregate.failure_causes:
        measurement["failure_causes"] = list(aggregate.failure_causes)
    return {
        "runtime_id": aggregate.runtime_id,
        "runtime_version": aggregate.runtime_version,
        "measurement": measurement,
    }


def attempt_to_dict(attempt: AttemptResult) -> dict[str, Any]:
    payload = asdict(attempt)
    payload["command_argv"] = list(attempt.command_argv)
    return payload


def write_run_artifacts(
    *,
    artifact_dir: Path,
    workload: WorkloadInputs,
    runtime_configs: Sequence[RuntimeRunnerConfig],
    aggregates: Sequence[RuntimeAggregate],
    repeats: int,
    host_class: str,
    verdict_grade: str,
    verdict_text: str,
    ledger_path: Path,
    appended_record: Mapping[str, Any] | None,
    started_at: str,
    completed_at: str,
) -> dict[str, Path]:
    """Write manifest, commands, and summary artifacts for one run."""

    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_dir / "manifest.json"
    commands_path = artifact_dir / "commands.json"
    summary_path = artifact_dir / "summary.md"

    manifest = {
        "host_class": host_class,
        "workload": {
            "workload_class": workload.workload_class,
            "prompt": workload.prompt,
            "decode_max_tokens": workload.decode_max_tokens,
            "decode_temperature": workload.decode_temperature,
            "model_id": workload.model_id,
            "model_path": workload.model_path,
            "model_quantization": workload.model_quantization,
            "prompt_set_hash": workload.prompt_set_hash,
            "serving_budget_bytes": workload.serving_budget_bytes,
        },
        "repeats": int(repeats),
        "started_at": started_at,
        "completed_at": completed_at,
        "verdict_grade": verdict_grade,
        "verdict_text": verdict_text,
        "ledger_path": str(ledger_path),
        "appended_record": dict(appended_record) if appended_record is not None else None,
        "runtimes": [
            {
                "runtime_id": agg.runtime_id,
                "runtime_version": agg.runtime_version,
                "completed_request_count": agg.completed_request_count,
                "failure_count": agg.failure_count,
                "failure_causes": list(agg.failure_causes),
                "wall_clock_ms": agg.wall_clock_ms,
                "first_token_latency_ms": agg.first_token_latency_ms,
                "throughput_tokens_per_second": agg.throughput_tokens_per_second,
                "peak_resident_set_bytes": agg.peak_resident_set_bytes,
                "attempts": [attempt_to_dict(a) for a in agg.attempts],
            }
            for agg in aggregates
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    commands = {
        "rerun_python": sys.executable,
        "runtime_argv": [
            {
                "runtime_id": cfg.runtime_id,
                "runtime_version": cfg.runtime_version,
                "argv": list(_substitute_placeholders(cfg.argv, workload=workload)),
                "env": dict(cfg.env),
                "cwd": cfg.cwd,
                "tokens_method": cfg.tokens_method,
                "first_token_strategy": cfg.first_token_strategy,
                "timeout_s": cfg.timeout_s,
                "external_pids": list(cfg.external_pids),
                "external_pid_file": cfg.external_pid_file,
                "external_listener_ports": list(cfg.external_listener_ports),
            }
            for cfg in runtime_configs
        ],
    }
    commands_path.write_text(
        json.dumps(commands, indent=2, sort_keys=True), encoding="utf-8"
    )

    summary_lines = [
        "# Comparative Evidence Run Summary",
        "",
        f"- host_class: `{host_class}`",
        f"- workload_class: `{workload.workload_class}`",
        f"- model_id: `{workload.model_id}`",
        f"- repeats per runtime: `{repeats}`",
        f"- started_at: `{started_at}`",
        f"- completed_at: `{completed_at}`",
        f"- verdict_grade: `{verdict_grade}`",
        f"- verdict_text: `{verdict_text}`",
        f"- ledger_path: `{ledger_path}`",
        "",
        "## Runtimes",
        "",
    ]
    for agg in aggregates:
        summary_lines.extend(
            [
                f"### `{agg.runtime_id}` ({agg.runtime_version})",
                "",
                f"- completed_request_count: `{agg.completed_request_count}`",
                f"- failure_count: `{agg.failure_count}`",
                f"- failure_causes: `{list(agg.failure_causes)}`",
                f"- wall_clock_ms (mean of successes): `{agg.wall_clock_ms:.4f}`",
                f"- first_token_latency_ms (mean of successes): `{agg.first_token_latency_ms:.4f}`",
                f"- throughput_tokens_per_second (mean of successes): `{agg.throughput_tokens_per_second:.4f}`",
                f"- peak_resident_set_bytes (max-per-tick sum across wrapper PID + descendants + external PIDs across attempts): `{agg.peak_resident_set_bytes}`",
                "",
            ]
        )
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    return {
        "manifest": manifest_path,
        "commands": commands_path,
        "summary": summary_path,
    }


def load_runner_config_file(
    path: str | Path,
) -> tuple[RuntimeRunnerConfig, RuntimeRunnerConfig]:
    """Load a JSON runner config and return ``(owlmlx_cfg, reference_cfg)``."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("runner config must be a JSON object")
    owlmlx_payload = payload.get("owlmlx")
    reference_payload = payload.get("reference")
    if not isinstance(owlmlx_payload, Mapping) or not isinstance(
        reference_payload, Mapping
    ):
        raise ValueError(
            "runner config must contain 'owlmlx' and 'reference' object entries"
        )
    return (
        _runner_from_payload(owlmlx_payload, default_id="owlmlx"),
        _runner_from_payload(reference_payload, default_id=None),
    )


def _runner_from_payload(
    payload: Mapping[str, Any], *, default_id: str | None
) -> RuntimeRunnerConfig:
    runtime_id = payload.get("runtime_id") or default_id
    if not isinstance(runtime_id, str) or not runtime_id:
        raise ValueError("runner config entry requires 'runtime_id'")
    runtime_version = payload.get("runtime_version")
    if not isinstance(runtime_version, str) or not runtime_version:
        raise ValueError(
            f"runner config entry for {runtime_id!r} requires 'runtime_version'"
        )
    argv_raw = payload.get("argv")
    if not isinstance(argv_raw, list) or not argv_raw or not all(
        isinstance(token, str) for token in argv_raw
    ):
        raise ValueError(
            f"runner config entry for {runtime_id!r} requires non-empty 'argv' list of strings"
        )
    env_raw = payload.get("env") or {}
    if not isinstance(env_raw, Mapping):
        raise ValueError(
            f"runner config entry for {runtime_id!r} 'env' must be an object"
        )
    cwd = payload.get("cwd")
    if cwd is not None and not isinstance(cwd, str):
        raise ValueError(
            f"runner config entry for {runtime_id!r} 'cwd' must be a string or null"
        )
    timeout_s = float(payload.get("timeout_s", 60.0))
    first_token_strategy = str(payload.get("first_token_strategy", "first_nonempty_chunk"))
    _validate_first_token_strategy(first_token_strategy, runtime_id=runtime_id)
    tokens_method = str(payload.get("tokens_method", "max_tokens"))
    external_pids_raw = payload.get("external_pids") or ()
    if not isinstance(external_pids_raw, (list, tuple)) or not all(
        isinstance(pid, int) for pid in external_pids_raw
    ):
        raise ValueError(
            f"runner config entry for {runtime_id!r} 'external_pids' must be a list of ints"
        )
    external_pid_file = payload.get("external_pid_file")
    if external_pid_file is not None and not isinstance(external_pid_file, str):
        raise ValueError(
            f"runner config entry for {runtime_id!r} 'external_pid_file' must be a string"
        )
    external_listener_ports_raw = payload.get("external_listener_ports") or ()
    if not isinstance(external_listener_ports_raw, (list, tuple)) or not all(
        isinstance(port, int) for port in external_listener_ports_raw
    ):
        raise ValueError(
            f"runner config entry for {runtime_id!r} 'external_listener_ports' must be a list of ints"
        )
    return RuntimeRunnerConfig(
        runtime_id=runtime_id,
        runtime_version=runtime_version,
        argv=tuple(argv_raw),
        env={str(k): str(v) for k, v in env_raw.items()},
        cwd=cwd,
        timeout_s=timeout_s,
        first_token_strategy=first_token_strategy,
        tokens_method=tokens_method,
        external_pids=tuple(int(pid) for pid in external_pids_raw),
        external_pid_file=external_pid_file,
        external_listener_ports=tuple(int(port) for port in external_listener_ports_raw),
    )


def _validate_first_token_strategy(value: str, *, runtime_id: str) -> None:
    spec = (value or "").strip()
    if spec == "first_nonempty_chunk":
        return
    if spec.startswith("after_marker:") and len(spec) > len("after_marker:"):
        return
    if spec.startswith("regex:") and len(spec) > len("regex:"):
        import re as _re

        try:
            _re.compile(spec[len("regex:"):])
        except _re.error as exc:
            raise ValueError(
                f"runner config entry for {runtime_id!r} has invalid "
                f"first_token_strategy regex: {exc}"
            ) from exc
        return
    raise ValueError(
        f"runner config entry for {runtime_id!r} has unsupported "
        f"first_token_strategy {value!r}; expected first_nonempty_chunk, "
        f"after_marker:<substring>, or regex:<pattern>"
    )


__all__ = [
    "AttemptResult",
    "RuntimeAggregate",
    "RuntimeRunnerConfig",
    "WorkloadInputs",
    "aggregate_runtime",
    "aggregate_to_record_runtime",
    "attempt_to_dict",
    "compute_verdict",
    "execute_attempt",
    "load_runner_config_file",
    "write_run_artifacts",
]
