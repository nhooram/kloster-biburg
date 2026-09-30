"""Assembly clearance for the colour split, offline (manifold3d: fast + robust, keeps Blender free).
Each piece is carved against the body shifted by GAP_MM in +-x, +-y and -z, so every contact that is not a
resting seat (vertical sliding faces, anything the body overhangs) gets a GAP_MM gap; sloped seats settle a
little. Rewrites export/split/*_copper/_red STLs in place. Usage: uv run --with manifold3d --with trimesh python tools/clearance.py [GAP_MM] [SPLIT_DIR]"""
import sys, glob, numpy as np, trimesh, manifold3d as mf

GAP_MM = float(sys.argv[1]) if len(sys.argv) > 1 else 0.2
SPLIT = sys.argv[2] if len(sys.argv) > 2 else "export/split"

def to_mf(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))

def to_tm(x):
    me = x.to_mesh()
    return trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts, process=True)

body = to_mf(trimesh.load(f"{SPLIT}/body_stone_1-250.stl", force="mesh"))
g = GAP_MM
grown = body
for off in ((g, 0, 0), (-g, 0, 0), (0, g, 0), (0, -g, 0), (0, 0, -g)):
    grown = grown + body.translate(off)
for f in sorted(glob.glob(f"{SPLIT}/*.stl")):
    if "body_stone" in f: continue
    before = to_mf(trimesh.load(f, force="mesh"))
    after = before - grown
    if "roof_sidechoir" in f:   # also keep clear of the main roof's choir eave above it
        main = to_mf(trimesh.load(f"{SPLIT}/roof_main_red_1-250.stl", force="mesh"))
        for off in ((g, 0, 0), (-g, 0, 0), (0, g, 0), (0, -g, 0), (0, 0, -g), (0, 0, 0)):
            after = after - main.translate(off)
    t = to_tm(after)
    keep = [b for b in t.split(only_watertight=False) if abs(b.volume) > 0.01]   # drop zero-volume slivers at eave corners
    t = trimesh.util.concatenate(keep)
    t.export(f)
    print(f"{f.split('/')[-1]:34s} {before.volume():9.1f} -> {after.volume():9.1f} mm3  watertight={t.is_watertight} bodies={len(t.split(only_watertight=False))}")
