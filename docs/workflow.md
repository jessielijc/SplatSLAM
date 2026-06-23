# Workflow

SplatSLAM supports three input modes:

1. Public datasets such as TUM-RGBD and 7-Scenes.
2. RGB-only monocular videos captured by a phone or camera.
3. iPhone Spectacular Rec captures with RGB frames and camera metadata.

The high-level workflow is:

```text
Input data
→ MASt3R-SLAM
→ camera trajectory + dense point cloud
→ SplatSLAM conversion / denoising
→ COLMAP-style 3DGS dataset
→ 3D Gaussian Splatting training
→ novel view rendering
```

## Key outputs from MASt3R-SLAM

- `*.txt`: camera trajectory in TUM-style format.
- `*.ply`: dense colored point cloud.
- `keyframes/`: RGB frames used for mapping.

## Key outputs for 3DGS

SplatSLAM exports a COLMAP-style folder:

```text
images/
sparse/0/cameras.txt
sparse/0/images.txt
sparse/0/points3D.txt
sparse/0/points3D.ply
```

## Project-specific post-processing

The most important post-processing step is SOR denoising. It removes isolated noisy points that otherwise initialize Gaussians at wrong 3D positions and cause floating artifacts in renderings.
