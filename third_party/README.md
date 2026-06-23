# Third-party dependencies

SplatSLAM depends on external SLAM and rendering projects, but we do not vendor their source code in this repository.

Recommended workspace layout:

```text
workspace/
├── SplatSLAM/
├── MASt3R-SLAM/
└── gaussian-splatting/
```

Install these projects from their official repositories:

- MASt3R-SLAM: https://github.com/rmurai0610/MASt3R-SLAM
- 3D Gaussian Splatting: https://github.com/graphdeco-inria/gaussian-splatting

The code in this repository focuses on the glue logic and project-specific processing:

- MASt3R-SLAM trajectory / point cloud conversion
- COLMAP / 3DGS dataset generation
- SOR point cloud denoising
- End-to-end workflow scripts
