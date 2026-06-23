#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <mast3r_slam_repo> <input_video_or_dataset> <output_dir> [extra_mast3r_args...]"
  exit 1
fi

MAST3R_REPO="$1"
INPUT="$2"
OUTPUT_DIR="$3"
shift 3

python "${MAST3R_REPO}/demo.py" \
  --input "${INPUT}" \
  --output "${OUTPUT_DIR}" \
  "$@"
