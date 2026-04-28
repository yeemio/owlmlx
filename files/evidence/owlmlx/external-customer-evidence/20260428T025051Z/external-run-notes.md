# owlmlx 3.6A External Customer Evidence Run Notes

> Date: 2026-04-28
> Evidence directory: `files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/`
> Runtime port: `8065`
> External consumer boundary: `/Users/yeemio/AI/gitrep/owlops`

## Boundary

This run used a minimal external HTTP consumer from the OwlOps repository
working directory. It did not edit OwlOps and did not count any internal
`owlmlx` script or test as the external deployment evidence.

OwlOps source already defines `owlmlx` as an upstream runtime truth source:

- `OwlmlxAdapter.fetchFullStatus()` calls `/v1/runtime/status`.
- `OwlmlxAdapter.fetchLiveness()` calls `/healthz`.
- `ConnectionValidator` validates the same two `owlmlx` routes for the
  `owlmlx_base_url` field.

## Host Class

```text
hw.model=Mac17,6
machine=arm64
macos=26.4.1
mem_bytes=137438953472
```

Frozen host class:

```text
Mac17,6-arm64-macOS-26.4.1-128GB
```

## Runtime Server

Started from `/Users/yeemio/AI/gitrep/owlmlx`:

```bash
PYTHONPATH=. python3 -m uvicorn owlmlx.runtime.server:create_fake_app \
  --factory --host 127.0.0.1 --port 8065 --log-level info
```

PID / port evidence:

```text
Python 67075 ... TCP 127.0.0.1:8065 (LISTEN)
```

## External Consumer Command

Run from `/Users/yeemio/AI/gitrep/owlops`:

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

Result:

```text
exit_status = 0
stderr_bytes = 0
/v1/runtime/status -> HTTP 200, contract_surface = owlmlx.runtime.status
/healthz -> HTTP 200, contract_surface = owlmlx.healthz
```

The runtime status response reported degraded readiness because this was a
fake-backend status service with no loaded model. That does not invalidate this
record: the workload was external runtime-truth consumption, not inference
quality or release readiness.

## Cleanup

The uvicorn PID `67075` was terminated after the external probe.

```text
lsof -n -iTCP:8065 -sTCP:LISTEN
# no output
```

## Artifact Pointers

```text
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/host-class.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlmlx-port-8065-listen-before.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlmlx-port-8065-listen-after.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stdout.json
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.stderr.txt
files/evidence/owlmlx/external-customer-evidence/20260428T025051Z/owlops-external-runtime-status-probe.exit-status
```

## Verdict

`pass`

External success:

```text
OwlOps-boundary external consumer successfully fetched owlmlx runtime status
and health truth over HTTP from outside the owlmlx repository.
```

This is a 3.6 closeout candidate, not a release claim and not a backlog flip.
