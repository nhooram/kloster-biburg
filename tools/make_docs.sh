#!/usr/bin/env bash
# Regenerate the README figures in docs/img (renders + comparison plots). Run from the project root after export_all.sh.
set -euo pipefail
B="python3 tools/bl.py"
UV="uv run --quiet --with trimesh --with numpy --with scipy --with rtree --with networkx --with shapely --with matplotlib --with pillow python"
D="$PWD/docs/img"
views() { { echo "OUT='$D'"; echo "VIEWS=$1"; cat tools/render_views.py; } | $B >/dev/null; }
# variants first (each rebuild replaces the scene), the default master last
{ echo 'SACRISTY=False'; cat blender/build_church.py; } | $B >/dev/null
views '{"var_no-sacristy": ((64, 60, 36), (4, 2, 14), 35)}'
{ echo 'FINIALS=False'; cat blender/build_church.py; } | $B >/dev/null
views '{"var_no-finials": ((-12, -45, 42), (12.4, -3, 31), 50)}'
$B blender/build_church.py >/dev/null
views '{
 "hero_sw": ((-55, -45, 18), (-3, 0, 13), 35),
 "hero_se": ((55, -55, 45), (0, 0, 10), 35),
 "hero_ne": ((56, 52, 32), (4, 2, 14), 35),
 "hero_nw": ((-50, 45, 40), (0, 0, 10), 35),
 "var_master": ((64, 60, 36), (4, 2, 14), 35),
 "var_finials": ((-12, -45, 42), (12.4, -3, 31), 50),
 "elev_south": ((-4, -220, 16), (-4, 0, 16), 110),
 "elev_west": ((-220, 0, 17), (0, 0, 17), 150),
 "top": ((-4, -0.01, 160), (-4, 0, 0), 75),
 "cu_belfry": ((16, -27, 26), (12.4, -6.5, 26), 45),
 "cu_portal": ((-39, -4, 3.6), (-27.4, 0.3, 3.4), 50),
 "cu_westgable": ((-47, -7, 16), (-27.4, 0, 15.5), 50),
 "cu_apse": ((33, -9, 9), (16.5, 0, 9.5), 40),
 "cu_shoulder": ((-35, -18, 13), (-27, -8, 8.5), 45),
 "cu_sacristy": ((27, 26, 11), (13, 11, 5), 40),
 "drone_e": ((52, -4, 60), (4, 0, 6), 30),
 "drone_s": ((-2, -52, 34), (-6, 0, 11), 30)}'
{ echo "CAMJSON='$PWD/analysis/cam2020.json'"; echo "OUTPNG='$D/_match2020.png'"; cat tools/match_render.py; } | $B >/dev/null
$B tools/split_parts.py >/dev/null
{ echo "OUTPNG='$D/split_exploded.png'"; echo "CAM=((-52, -55, 44), (-3, 0, 21))"; cat tools/render_exploded.py; } | $B >/dev/null
{ echo "OUTPNG='$D/split_exploded_ne.png'"; echo "CAM=((54, 54, 44), (3, 0, 21))"; cat tools/render_exploded.py; } | $B >/dev/null
uv run --quiet --with manifold3d --with trimesh --with numpy --with networkx python tools/clearance.py 0.2 >/dev/null 2>&1   # split_parts rewrote the STLs: put the clearance back
$UV tools/doc_plots.py
