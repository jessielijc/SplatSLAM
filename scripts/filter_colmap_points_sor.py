import argparse
from pathlib import Path

import numpy as np
import open3d as o3d
from plyfile import PlyData, PlyElement


def read_points_txt(path):
    header = []
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                header.append(line)
                continue
            s = line.strip()
            if not s:
                continue
            parts = s.split()
            rows.append(parts)
    return header, rows


def write_points_txt(path, rows):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# 3D point list with one line of data per point:\n')
        f.write('# POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)\n')
        f.write(f'# Number of points: {len(rows)}, mean track length: 0\n')
        for i, row in enumerate(rows, start=1):
            x, y, z, r, g, b = row
            f.write(f'{i} {x:.8g} {y:.8g} {z:.8g} {r} {g} {b} 0\n')


def write_points_ply(path, rows):
    arr = np.empty(len(rows), dtype=[('x','f4'),('y','f4'),('z','f4'),('red','u1'),('green','u1'),('blue','u1')])
    for i, row in enumerate(rows):
        x, y, z, r, g, b = row
        arr[i] = (x, y, z, r, g, b)
    PlyData([PlyElement.describe(arr, 'vertex')], text=False).write(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sparse_dir', required=True)
    ap.add_argument('--nb_neighbors', type=int, default=20)
    ap.add_argument('--std_ratio', type=float, default=1.25)
    args = ap.parse_args()

    sparse = Path(args.sparse_dir)
    txt = sparse / 'points3D.txt'
    ply = sparse / 'points3D.ply'
    _, rows_raw = read_points_txt(txt)
    xyz = []
    colors = []
    for row in rows_raw:
        xyz.append([float(row[1]), float(row[2]), float(row[3])])
        colors.append([int(row[4]), int(row[5]), int(row[6])])
    xyz = np.asarray(xyz, dtype=np.float64)
    colors = np.asarray(colors, dtype=np.uint8)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz)
    pcd.colors = o3d.utility.Vector3dVector(colors.astype(np.float64) / 255.0)
    print('before', len(xyz))
    _, idx = pcd.remove_statistical_outlier(nb_neighbors=args.nb_neighbors, std_ratio=args.std_ratio)
    idx = np.asarray(idx, dtype=np.int64)
    xyz_keep = xyz[idx]
    colors_keep = colors[idx]
    rows = [(float(x), float(y), float(z), int(r), int(g), int(b)) for (x,y,z),(r,g,b) in zip(xyz_keep, colors_keep)]
    print('after', len(rows), 'removed', len(xyz)-len(rows))
    txt.rename(sparse / 'points3D_before_sor.txt')
    if ply.exists():
        ply.rename(sparse / 'points3D_before_sor.ply')
    write_points_txt(txt, rows)
    write_points_ply(ply, rows)


if __name__ == '__main__':
    main()
