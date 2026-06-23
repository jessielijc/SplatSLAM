#!/usr/bin/env python3
"""Statistical Outlier Removal for COLMAP/3DGS point clouds.

This module is one of the project-specific contributions of SplatSLAM. It
filters noisy MASt3R-SLAM points before 3D Gaussian Splatting training to
reduce floating artifacts while preserving useful scene geometry.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import open3d as o3d
from plyfile import PlyData, PlyElement


def read_colmap_points_txt(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            line = line.strip()
            if line:
                rows.append(line.split())
    return rows


def write_colmap_points_txt(path: Path, rows: Iterable[tuple[float, float, float, int, int, int]]) -> None:
    rows = list(rows)
    with path.open("w", encoding="utf-8") as f:
        f.write("# 3D point list with one line of data per point:\n")
        f.write("# POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)\n")
        f.write(f"# Number of points: {len(rows)}, mean track length: 0\n")
        for point_id, (x, y, z, r, g, b) in enumerate(rows, start=1):
            f.write(f"{point_id} {x:.8g} {y:.8g} {z:.8g} {r} {g} {b} 0\n")


def write_points_ply(path: Path, rows: Iterable[tuple[float, float, float, int, int, int]]) -> None:
    rows = list(rows)
    arr = np.empty(
        len(rows),
        dtype=[("x", "f4"), ("y", "f4"), ("z", "f4"), ("red", "u1"), ("green", "u1"), ("blue", "u1")],
    )
    for i, (x, y, z, r, g, b) in enumerate(rows):
        arr[i] = (x, y, z, r, g, b)
    PlyData([PlyElement.describe(arr, "vertex")], text=False).write(path)


def apply_sor_to_colmap_sparse(sparse_dir: Path, nb_neighbors: int = 20, std_ratio: float = 1.25) -> dict[str, int]:
    """Apply SOR to a COLMAP sparse/0 folder.

    The function backs up the original `points3D.txt` / `points3D.ply` as
    `points3D_before_sor.*`, then writes filtered versions in place.
    """
    sparse_dir = Path(sparse_dir)
    txt_path = sparse_dir / "points3D.txt"
    ply_path = sparse_dir / "points3D.ply"
    if not txt_path.is_file():
        raise FileNotFoundError(f"Missing COLMAP points file: {txt_path}")

    rows_raw = read_colmap_points_txt(txt_path)
    xyz = np.asarray([[float(row[1]), float(row[2]), float(row[3])] for row in rows_raw], dtype=np.float64)
    colors = np.asarray([[int(row[4]), int(row[5]), int(row[6])] for row in rows_raw], dtype=np.uint8)

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz)
    pcd.colors = o3d.utility.Vector3dVector(colors.astype(np.float64) / 255.0)

    _, keep_indices = pcd.remove_statistical_outlier(nb_neighbors=nb_neighbors, std_ratio=std_ratio)
    keep_indices = np.asarray(keep_indices, dtype=np.int64)
    filtered = [
        (float(x), float(y), float(z), int(r), int(g), int(b))
        for (x, y, z), (r, g, b) in zip(xyz[keep_indices], colors[keep_indices])
    ]

    backup_txt = sparse_dir / "points3D_before_sor.txt"
    backup_ply = sparse_dir / "points3D_before_sor.ply"
    if not backup_txt.exists():
        txt_path.rename(backup_txt)
    if ply_path.exists() and not backup_ply.exists():
        ply_path.rename(backup_ply)

    write_colmap_points_txt(txt_path, filtered)
    write_points_ply(ply_path, filtered)

    return {"before": len(rows_raw), "after": len(filtered), "removed": len(rows_raw) - len(filtered)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply SOR denoising to COLMAP sparse/0 points before 3DGS training.")
    parser.add_argument("--sparse_dir", required=True, help="Path to COLMAP sparse/0 directory")
    parser.add_argument("--nb_neighbors", type=int, default=20)
    parser.add_argument("--std_ratio", type=float, default=1.25)
    args = parser.parse_args()

    stats = apply_sor_to_colmap_sparse(Path(args.sparse_dir), args.nb_neighbors, args.std_ratio)
    print(f"SOR finished: {stats['before']} -> {stats['after']} points, removed {stats['removed']} points")


if __name__ == "__main__":
    main()
