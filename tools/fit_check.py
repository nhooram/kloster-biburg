"""Clearance check for the colour split: where does each piece touch the body, and on what kind of face?
Piece faces touching the body: facing down = seat (fine); vertical = sliding fit with 0 gap (needs clearance);
facing up = body above the piece (cannot be assembled by lowering it)."""
import trimesh, numpy as np, glob, sys
S = 250 / 1000.0                      # mm -> m (1:250)
body = trimesh.load("export/split/body_stone_1-250.stl", force="mesh")
pq = trimesh.proximity.ProximityQuery(body)
for f in sorted(glob.glob("export/split/*.stl")):
    if "body" in f: continue
    p = trimesh.load(f, force="mesh")
    pts, fi = trimesh.sample.sample_surface_even(p, 20000)
    d = np.abs(pq.signed_distance(pts))          # mm
    nz = p.face_normals[fi][:, 2]                 # piece face normal (outward); piece is lowered straight down
    touch = d < 0.05                              # within 0.05 mm = touching
    seat, wall, lock = touch & (nz < -0.2), touch & (np.abs(nz) <= 0.2), touch & (nz > 0.2)
    A = p.area / len(pts)
    loc = lambda m: np.round(pts[m].mean(0) * S, 1).tolist() if m.any() else "-"
    print(f"{f.split('/')[-1][:-10]:22s} seat {seat.sum()*A:7.1f} mm2 | zero-gap vertical {wall.sum()*A:6.1f} mm2 at {loc(wall)} | undercut {lock.sum()*A:6.1f} mm2 at {loc(lock)}")
