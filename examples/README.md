# Example input layout

A MASt3R-SLAM output folder is expected to look like:

```text
scene_result/
├── keyframes/
│   └── scene_name/
│       ├── 0.000000.png
│       ├── 0.100000.png
│       └── ...
├── scene_name.txt
└── scene_name.ply
```

Then convert it with:

```bash
bash scripts/convert_to_3dgs.sh scene_result outputs/3dgs_dataset scene_name 300000
```
