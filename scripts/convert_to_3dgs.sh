#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <source_mast3r_result_dir> <output_3dgs_dataset_dir> <scene_name> [max_points]"
  exit 1
fi

SOURCE_DIR="$1"
OUTPUT_DIR="$2"
SCENE="$3"
MAX_POINTS="${4:-300000}"

python scripts/export_mast3r_to_3dgs.py \
  --source "${SOURCE_DIR}" \
  --output "${OUTPUT_DIR}" \
  --scene "${SCENE}" \
  --max-points "${MAX_POINTS}" \
  --fov-x 60
