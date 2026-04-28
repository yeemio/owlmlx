# owlmlx Release Floor 3.6A External Customer Evidence Minimum Record Handoff

> Date: 2026-04-28
> Outcome label: `owlmlx_release_floor_3_6A_external_customer_evidence_pass_candidate`
> Repository: `/Users/yeemio/AI/gitrep/owlmlx`
> Evidence directory: `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/`

## Verdict

`3.6A` produced one external customer / deployment-boundary evidence record.

Verdict: `pass`

Floor `3.6` is closeout-recommended, but this lane did not flip
`release-readiness-backlog.md`.

No release, parity, replacement, production-grade, superiority, wins, beats, or
equivalent claim was made.

## Deployment Boundary

External consumer boundary:

```text
/Users/yeemio/AI/gitrep/owlops
```

The live command was issued from the OwlOps repository boundary. OwlOps source
defines `owlmlx` as an upstream runtime truth source through
`OwlmlxAdapter.fetchFullStatus()` (`/v1/runtime/status`),
`OwlmlxAdapter.fetchLiveness()` (`/healthz`), and `ConnectionValidator` checks
for the `owlmlx_base_url` field.

No OwlOps source files were edited.

## Host Class

```text
Mac17,6-arm64-macOS-26.4.1-128GB
```

Captured values:

```text
hw.model=Mac17,6
machine=arm64
macos=26.4.1
mem_bytes=137438953472
```

## Workload Class

```text
external_runtime_status_probe
```

Runtime surfaces:

```text
GET /v1/runtime/status
GET /healthz
```

## Command / HTTP Request

Runtime server started from `/Users/yeemio/AI/gitrep/owlmlx`:

```bash
PYTHONPATH=. python3 -m uvicorn owlmlx.runtime.server:create_fake_app \
  --factory --host 127.0.0.1 --port 8065 --log-level info
```

External consumer command run from `/Users/yeemio/AI/gitrep/owlops`:

```bash
python3 - <<'PY'
import json
import urllib.request
from datetime import datetime, timezone
base = 'http://127.0.0.1:8065'
results = []
for path in ['/v1/runtime/status', '/healthz']:
    req = urllib.request.Request(
        base + path,
        headers={'User-Agent': 'owlops-external-consumer-probe/3.6A'},
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        body = response.read().decode('utf-8')
        parsed = json.loads(body)
        results.append({
            'path': path,
            'http_status': response.status,
            'content_type': response.headers.get('content-type'),
            'json_top_level_keys': sorted(parsed.keys()),
            'runtime': parsed.get('runtime') or parsed.get('summary', {}).get('runtime'),
            'status': parsed.get('status') or parsed.get('health', {}).get('status'),
            'readiness': parsed.get('readiness') or parsed.get('health', {}).get('readiness'),
            'contract_surface': parsed.get('contract', {}).get('surface'),
            'body': parsed,
        })
print(json.dumps({
    'recorded_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    'consumer_boundary': 'owlops repo external cwd minimal HTTP consumer',
    'cwd': '/Users/yeemio/AI/gitrep/owlops',
    'base_url': base,
    'results': results,
}, indent=2, sort_keys=True))
PY
```

Result summary:

```text
exit_status = 0
stderr_bytes = 0
/v1/runtime/status -> HTTP 200, contract_surface = owlmlx.runtime.status
/healthz -> HTTP 200, contract_surface = owlmlx.healthz
```

## External Success

```text
OwlOps-boundary external consumer successfully fetched owlmlx runtime status
and health truth over HTTP from outside the owlmlx repository.
```

The runtime status response reported degraded readiness because this run used
the fake-backend status service with no loaded model. That is acceptable for
this narrow workload: it proves external runtime-truth consumption, not
inference quality.

## Evidence Pointer

```text
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/
```

Key files:

```text
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/external-run-notes.md
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/host-class.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlmlx-port-8065-listen-before.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlmlx-port-8065-listen-after.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stdout.json
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stderr.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.exit-status
```

## Commands Run

```bash
pytest -q tests/test_customer_runtime_evidence.py
# 53 passed in 18.12s

python3 scripts/runtime_customer_runtime_evidence.py --help
# printed help successfully

python3 -m py_compile \
  owlmlx/customer_runtime_evidence.py \
  scripts/runtime_customer_runtime_evidence.py
# passed with no output

lsof -n -iTCP:8065 -sTCP:LISTEN
# before: Python 67075 listening on 127.0.0.1:8065
# after cleanup: no output

git diff --check
# passed with no output
```

## Files Changed

- `docs/source-of-truth/phase45-customer-runtime-evidence-ledger.md`
- `docs/source-of-truth/release-readiness-execution-plan.md`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/external-run-notes.md`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/host-class.txt`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlmlx-port-8065-listen-before.txt`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlmlx-port-8065-listen-after.txt`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stdout.json`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stderr.txt`
- `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.exit-status`
- `files/execution-prompts/owlmlx/owlmlx-release-floor-3-6A-external-customer-evidence-minimum-record-handoff.md`

## Closeout Recommendation

Floor `3.6` is closeout-recommended.

Recommended next prompt:

```text
Run a narrow 3.6B / final ledger closeout review after the parallel 3.7A result
is available. Verify this external evidence record, confirm no release/parity/
replacement claim was made, and only then decide whether to flip
release-readiness-backlog.md row 3.6.
```
