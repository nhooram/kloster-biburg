#!/usr/bin/env bash
# Rebuild and export every print variant, apply clearance, validate. Run from the project root.
set -euo pipefail
B="python3 tools/bl.py"
UV="uv run --quiet --with manifold3d --with trimesh --with numpy --with networkx --with scipy --with rtree python"
# church only (no sacristy): master + colour split
{ echo 'SACRISTY=False'; cat blender/build_church.py; } | $B >/dev/null
{ echo 'SUFFIX="_no-sacristy"'; cat tools/export_stl.py; } | $B >/dev/null
{ echo 'SACRISTY=False'; echo 'OUTDIR="/home/hooram/code/cad-work/kloster-biburg/export/split_no-sacristy"'; cat tools/split_parts.py; } | $B >/dev/null
$UV tools/clearance.py 0.2 export/split_no-sacristy >/dev/null 2>&1
# with sacristy (default): no-finials master, colour split, master
{ echo 'FINIALS=False'; cat blender/build_church.py; } | $B >/dev/null
{ echo 'SUFFIX="_no-finials"'; cat tools/export_stl.py; } | $B >/dev/null
$B tools/split_parts.py >/dev/null
$UV tools/clearance.py 0.2 export/split >/dev/null 2>&1
$B tools/export_stl.py >/dev/null           # leaves the default master in the scene
echo 'import bpy; bpy.ops.wm.save_as_mainfile(filepath="/home/hooram/code/cad-work/kloster-biburg/blender/kloster_biburg.blend", copy=True); result={"ok":1}' | $B >/dev/null
$UV - <<'PY' 2>/dev/null
import trimesh, glob
fs = sorted(glob.glob("export/*.stl") + glob.glob("export/split*/*.stl"))
bad = [f for f in fs if not (lambda s: s.is_watertight and len(s.split(only_watertight=False)) == 1)(trimesh.load(f, force="mesh"))]
print("files checked:", len(fs), "bad:", bad)
PY
