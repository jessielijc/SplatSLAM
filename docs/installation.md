# Installation

## 1. Clone SplatSLAM

```bash
git clone https://github.com/jessielijc/SplatSLAM.git
cd SplatSLAM
pip install -r requirements.txt
```

## 2. Install MASt3R-SLAM

Follow the official instructions from MASt3R-SLAM:

https://github.com/rmurai0610/MASt3R-SLAM

## 3. Install 3D Gaussian Splatting

Follow the official instructions from GraphDECO 3DGS:

https://github.com/graphdeco-inria/gaussian-splatting

## 4. Recommended layout

```text
workspace/
├── SplatSLAM/
├── MASt3R-SLAM/
└── gaussian-splatting/
```

Then run SplatSLAM scripts from the `SplatSLAM` folder.
