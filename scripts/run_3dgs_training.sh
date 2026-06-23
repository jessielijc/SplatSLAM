#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <gaussian_splatting_repo> <dataset_dir> [model_dir] [iterations]"
  exit 1
fi

GS_REPO="$1"
DATASET_DIR="$2"
MODEL_DIR="${3:-outputs/3dgs_model}"
ITERATIONS="${4:-7000}"

python "${GS_REPO}/train.py" \
  -s "${DATASET_DIR}" \
  -m "${MODEL_DIR}" \
  --iterations "${ITERATIONS}" \
  --save_iterations "${ITERATIONS}" \
  --test_iterations "${ITERATIONS}" \
  --disable_viewer
