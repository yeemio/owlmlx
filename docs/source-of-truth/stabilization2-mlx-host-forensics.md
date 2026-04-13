# owlmlx Stabilization-2: Host-Level MLX Crash Forensics

> Status: authoritative  
> Updated: 2026-04-13  
> Scope: runtime-owned host forensics for the current machine's MLX import crash path

## 1. Purpose

This document freezes the machine-level evidence needed for either:

- upstream-correlated MLX/Metal debugging
- or a clean decision to move large-weight first smoke to another host

It does not attempt to solve the crash. It makes the current host truth
portable and machine-readable.

## 2. Runtime-Owned Surface

`owlmlx` now exposes:

- `scripts/runtime_mlx_host_forensics.py`

Contract:

- `surface = "owlmlx.mlx_host_forensics"`
- `version = "stabilization2"`

Stable sections:

- `summary`
- `readiness`
- `crash_reports`

## 3. Current Verified Host Signature

Current repeated crash signature on this machine:

- `exception_name = NSRangeException`
- `signal = SIGABRT`
- `mlx_symbol = mlx::core::metal::Device::Device()`
- `model_code = Mac17,6`
- `os_version = macOS 26.4.1 (25E253)`

This signature appears repeatedly across recent `Python-*.ips` reports under:

- `~/Library/Logs/DiagnosticReports`

## 4. Relationship To Readiness Truth

The host forensics report is not separate from runtime readiness.

It embeds:

- current `owlmlx.mlx_environment` readiness contract
- recent MLX crash evidence from macOS diagnostics

This means the local handoff question can now be answered without manual
cross-reading:

- if readiness is `blocked`
- and crash reports still show the same MLX/Metal signature

then the system is blocked at the host MLX import layer, not at the specimen
directory layer.

## 5. What This Proves

It proves:

- the current host still produces repeated MLX import crashes
- the crash signature is stable enough to summarize formally
- `owlmlx` now owns a machine-level handoff surface for this blocker

It does not prove:

- MiniMax-M2.7 itself is incompatible
- another host would fail the same way
- upstream has no fix

## 6. Current Next Step

The next rational step is now one of:

1. correlate this host signature with upstream MLX issues and version windows
2. try the same specimen on a distinct host/system image
3. only re-open local first smoke after one verified-safe baseline exists again
