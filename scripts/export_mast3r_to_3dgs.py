#!/usr/bin/env python3
import argparse
import math
import random
import shutil
import struct
from pathlib import Path

import numpy as np


def normalize_quaternion(q):
    q = np.asarray(q, dtype=np.float64)
    n = np.linalg.norm(q)
    if n == 0:
        raise ValueError("Zero-length quaternion")
    return q / n


def quat_xyzw_to_rotmat(qx, qy, qz, qw):
    qx, qy, qz, qw = normalize_quaternion([qx, qy, qz, qw])
    xx, yy, zz = qx * qx, qy * qy, qz * qz
    xy, xz, yz = qx * qy, qx * qz, qy * qz
    wx, wy, wz = qw * qx, qw * qy, qw * qz
    return np.array(
        [
            [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
            [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
            [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
        ],
        dtype=np.float64,
    )


def rotmat_to_quat_wxyz(R):
    R = np.asarray(R, dtype=np.float64)
    trace = np.trace(R)
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        qw = 0.25 * s
        qx = (R[2, 1] - R[1, 2]) / s
        qy = (R[0, 2] - R[2, 0]) / s
        qz = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s
    qw, qx, qy, qz = normalize_quaternion([qw, qx, qy, qz])
    if qw < 0:
        qw, qx, qy, qz = -qw, -qx, -qy, -qz
    return qw, qx, qy, qz


def mast3r_twc_to_colmap_tcw(tx, ty, tz, qx, qy, qz, qw):
    R_wc = quat_xyzw_to_rotmat(qx, qy, qz, qw)
    t_wc = np.array([tx, ty, tz], dtype=np.float64)
    R_cw = R_wc.T
    t_cw = -R_cw @ t_wc
    qw_cw, qx_cw, qy_cw, qz_cw = rotmat_to_quat_wxyz(R_cw)
    return qw_cw, qx_cw, qy_cw, qz_cw, t_cw[0], t_cw[1], t_cw[2]


def read_trajectory(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 8:
                raise ValueError(f"Expected 8 values in trajectory line, got {len(parts)}: {line}")
            timestamp = parts[0]
            tx, ty, tz, qx, qy, qz, qw = map(float, parts[1:])
            rows.append((timestamp, tx, ty, tz, qx, qy, qz, qw))
    return rows


def read_image_size(path):
    try:
        from PIL import Image

        with Image.open(path) as img:
            return img.size
    except Exception:
        import cv2

        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise RuntimeError(f"Could not read image: {path}")
        return img.shape[1], img.shape[0]


def read_binary_ply_xyzrgb(path, max_points=None, seed=0):
    with open(path, "rb") as f:
        header_bytes = b""
        while b"end_header\n" not in header_bytes:
            chunk = f.readline()
            if not chunk:
                raise ValueError("Invalid PLY: missing end_header")
            header_bytes += chunk
        header = header_bytes.decode("ascii", errors="replace")
        if "format binary_little_endian 1.0" not in header:
            raise ValueError("Only binary_little_endian PLY is supported by this script")
        vertex_count = None
        properties = []
        in_vertex = False
        for line in header.splitlines():
            if line.startswith("element vertex"):
                vertex_count = int(line.split()[2])
                in_vertex = True
                continue
            if line.startswith("element ") and not line.startswith("element vertex"):
                in_vertex = False
            if in_vertex and line.startswith("property"):
                properties.append(line.split()[2])
        required = ["x", "y", "z", "red", "green", "blue"]
        if vertex_count is None:
            raise ValueError("PLY header does not contain vertex count")
        if properties != required:
            raise ValueError(f"Expected PLY vertex properties {required}, got {properties}")

        record_size = struct.calcsize("<fffBBB")
        if max_points is None or max_points <= 0 or max_points >= vertex_count:
            selected = None
        else:
            rng = random.Random(seed)
            selected = set(rng.sample(range(vertex_count), max_points))

        points = []
        for idx in range(vertex_count):
            data = f.read(record_size)
            if len(data) != record_size:
                raise ValueError("Unexpected EOF while reading PLY vertices")
            if selected is not None and idx not in selected:
                continue
            x, y, z, r, g, b = struct.unpack("<fffBBB", data)
            if np.isfinite(x) and np.isfinite(y) and np.isfinite(z):
                points.append((x, y, z, r, g, b))
    return points, vertex_count


def match_keyframes_to_poses(keyframe_dir, poses):
    pose_by_timestamp = {timestamp: row for timestamp, *row in poses}
    pairs = []
    missing = []
    for img_path in sorted(keyframe_dir.glob("*.png"), key=lambda p: float(p.stem)):
        timestamp = img_path.stem
        row = pose_by_timestamp.get(timestamp)
        if row is None:
            missing.append(img_path.name)
        else:
            pairs.append((img_path, timestamp, row))
    if missing:
        raise ValueError(f"Missing trajectory rows for keyframes: {missing[:10]}")
    if len(pairs) != len(poses):
        print(f"[warning] matched {len(pairs)} keyframes but trajectory has {len(poses)} poses")
    return pairs


def write_dataset(args):
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    scene = args.scene or source.name
    keyframe_dir = source / "keyframes" / scene
    traj_path = source / f"{scene}.txt"
    ply_path = source / f"{scene}.ply"

    if not keyframe_dir.is_dir():
        raise FileNotFoundError(f"Keyframe directory not found: {keyframe_dir}")
    if not traj_path.is_file():
        raise FileNotFoundError(f"Trajectory file not found: {traj_path}")
    if not ply_path.is_file():
        raise FileNotFoundError(f"PLY file not found: {ply_path}")

    poses = read_trajectory(traj_path)
    pairs = match_keyframes_to_poses(keyframe_dir, poses)
    if not pairs:
        raise RuntimeError("No keyframes matched trajectory")

    images_dir = output / "images"
    sparse_dir = output / "sparse" / "0"
    images_dir.mkdir(parents=True, exist_ok=True)
    sparse_dir.mkdir(parents=True, exist_ok=True)

    first_w, first_h = read_image_size(pairs[0][0])
    fx = args.fx if args.fx is not None else args.focal
    fy = args.fy if args.fy is not None else args.focal
    if fx is None or fy is None:
        fov_x_rad = math.radians(args.fov_x)
        fx = first_w / (2.0 * math.tan(fov_x_rad / 2.0))
        fy = fx
    cx = args.cx if args.cx is not None else first_w / 2.0
    cy = args.cy if args.cy is not None else first_h / 2.0

    image_name_by_timestamp = {}
    for image_id, (src_img, timestamp, _) in enumerate(pairs, start=1):
        dst_name = f"{image_id:06d}{src_img.suffix.lower()}"
        image_name_by_timestamp[timestamp] = dst_name
        shutil.copy2(src_img, images_dir / dst_name)

    with open(sparse_dir / "cameras.txt", "w", encoding="utf-8") as f:
        f.write("# Camera list with one line of data per camera:\n")
        f.write("# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n")
        f.write("# Number of cameras: 1\n")
        f.write(f"1 PINHOLE {first_w} {first_h} {fx:.12g} {fy:.12g} {cx:.12g} {cy:.12g}\n")

    with open(sparse_dir / "images.txt", "w", encoding="utf-8") as f:
        f.write("# Image list with two lines of data per image:\n")
        f.write("# IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, IMAGE_NAME\n")
        f.write("# POINTS2D[] as (X, Y, POINT3D_ID)\n")
        f.write(f"# Number of images: {len(pairs)}, mean observations per image: 0\n")
        for image_id, (_, timestamp, row) in enumerate(pairs, start=1):
            tx, ty, tz, qx, qy, qz, qw = row
            qw_cw, qx_cw, qy_cw, qz_cw, tx_cw, ty_cw, tz_cw = mast3r_twc_to_colmap_tcw(
                tx, ty, tz, qx, qy, qz, qw
            )
            image_name = image_name_by_timestamp[timestamp]
            f.write(
                f"{image_id} {qw_cw:.17g} {qx_cw:.17g} {qy_cw:.17g} {qz_cw:.17g} "
                f"{tx_cw:.17g} {ty_cw:.17g} {tz_cw:.17g} 1 {image_name}\n\n"
            )

    points, original_vertex_count = read_binary_ply_xyzrgb(ply_path, args.max_points, args.seed)
    with open(sparse_dir / "points3D.txt", "w", encoding="utf-8") as f:
        f.write("# 3D point list with one line of data per point:\n")
        f.write("# POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)\n")
        f.write(f"# Number of points: {len(points)}, mean track length: 0\n")
        for point_id, (x, y, z, r, g, b) in enumerate(points, start=1):
            f.write(f"{point_id} {x:.8g} {y:.8g} {z:.8g} {r} {g} {b} 0\n")

    print(f"Converted scene: {scene}")
    print(f"Source: {source}")
    print(f"Output: {output}")
    print(f"Images: {len(pairs)}")
    print(f"Image size: {first_w} x {first_h}")
    print(f"Camera PINHOLE: fx={fx:.3f}, fy={fy:.3f}, cx={cx:.3f}, cy={cy:.3f}")
    print(f"Points: {len(points)} / {original_vertex_count}")
    print("Done.")


def main():
    parser = argparse.ArgumentParser(description="Export MASt3R-SLAM results to a COLMAP text dataset for 3DGS.")
    parser.add_argument("--source", required=True, help="MASt3R-SLAM result folder, e.g. results/mp4/test1")
    parser.add_argument("--output", required=True, help="Output 3DGS dataset folder")
    parser.add_argument("--scene", default=None, help="Scene name. Defaults to source folder name")
    parser.add_argument("--max-points", type=int, default=200000, help="Randomly downsample PLY to this many points. <=0 keeps all")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--focal", type=float, default=None, help="Shared fx=fy focal length in pixels")
    parser.add_argument("--fx", type=float, default=None)
    parser.add_argument("--fy", type=float, default=None)
    parser.add_argument("--cx", type=float, default=None)
    parser.add_argument("--cy", type=float, default=None)
    parser.add_argument("--fov-x", type=float, default=60.0, help="Used to estimate focal length if focal/fx/fy are not provided")
    args = parser.parse_args()
    write_dataset(args)


if __name__ == "__main__":
    main()
