# Example datasets

This folder contains the self-captured example datasets used in SplatSLAM.

## Contents

```text
examples/datasets/
├── mast3r_slam/
│   ├── test6/      # keyframes + trajectory + point cloud from MASt3R-SLAM
│   ├── test9/      # trajectory + point cloud; use 3dgs/test9_dataset for training
│   └── test10/     # keyframes + trajectory + point cloud from MASt3R-SLAM
└── 3dgs/
    ├── test6_dataset/   # COLMAP / 3DGS-ready dataset
    ├── test9_dataset/
    └── test10_dataset/
```

## Recommended usage

If you want to test the full SplatSLAM conversion pipeline, start from:

```text
examples/datasets/mast3r_slam/test6
examples/datasets/mast3r_slam/test10
```

If you want to directly test 3DGS training, start from:

```text
examples/datasets/3dgs/test6_dataset
examples/datasets/3dgs/test9_dataset
examples/datasets/3dgs/test10_dataset
```

## Git LFS

Some point clouds are close to or above GitHub's 100MB normal file limit. The repository uses `.gitattributes` to track large files with Git LFS.

Before pushing the repository, install and initialize Git LFS:

```bash
git lfs install
git lfs track "*.ply"
git lfs track "*.mp4"
git add .gitattributes
```
