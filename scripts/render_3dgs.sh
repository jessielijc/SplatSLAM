#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <gaussian_splatting_repo> <model_dir> [iteration]"
  exit 1
fi

GS_REPO="$1"
MODEL_DIR="$2"
ITERATION="${3:-7000}"

python "${GS_REPO}/render.py" \
  -m "${MODEL_DIR}" \
  --iteration "${ITERATION}" \
  --skip_test
