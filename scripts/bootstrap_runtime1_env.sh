#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="${1:-$ROOT_DIR/.runtime1-mlx}"

echo "Bootstrapping clean Runtime-1 MLX environment at: $ENV_DIR"

python3 -m venv "$ENV_DIR"
"$ENV_DIR/bin/pip" install --upgrade pip
"$ENV_DIR/bin/pip" install \
  "mlx>=0.22.0" \
  "mlx-lm>=0.22.0" \
  "fastapi>=0.115.0" \
  "uvicorn[standard]>=0.34.0"

echo
echo "Bootstrap complete."
echo "Next probe:"
echo "  $ENV_DIR/bin/python $ROOT_DIR/scripts/runtime1_mlx_lm_smoke.py"
