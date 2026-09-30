"""README comparison figures + numbers (offline). Run from the project root after make_docs.sh has rendered
docs/img/_match2020.png. Writes docs/img/cmp_*.png / split_*.png and prints docs/img/metrics.json."""
import json, glob, numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from PIL import Image, ImageFilter, ImageChops

D = "docs/img"
K = 4.0                                   # STL mm per model m at 1:250
# church_local.json keeps the LoD2 tile's local origin: its nave ridge runs at y = +1.45..1.56 (model: y = 0)
LOD_DY = -1.5
lod = [(t, [[x, y + LOD_DY, z] for x, y, z in ps]) for t, ps in json.load(open("refs/lod2/church_local.json"))]
M = {}                                    # metrics

def stl(f):
    m = trimesh.load(f, force="mesh"); m.apply_scale(1 / K); return m

master = stl("export/KlosterkircheBiburg_1-250.stl")
nosac = stl("export/KlosterkircheBiburg_1-250_no-sacristy.stl")

# --- 1. photo overlay: model rendered from the PnP-solved camera over the 2020 photo
photo = Image.open("refs/photos/2020_St_Maria_Biburg.jpg").convert("RGB")
rend = Image.open(f"{D}/_match2020.png").convert("RGBA").resize(photo.size)
a = rend.split()[3].point(lambda v: 255 if v > 128 else 0)
edge = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(5)), a.filter(ImageFilter.MinFilter(5)))
tint = Image.composite(Image.blend(photo, rend.convert("RGB"), 0.55), photo, a)
over = Image.composite(Image.new("RGB", photo.size, (255, 40, 40)), tint, edge)
Image.fromarray(np.hstack([np.asarray(photo), np.asarray(over)])).resize((1920, 773)).save(f"{D}/cmp_photo2020.jpg", quality=88)
edge_only = Image.composite(Image.new("RGB", photo.size, (255, 40, 40)), photo, edge)
edge_only.crop((0, 0, 1920, 1546)).resize((1200, 966)).save(f"{D}/cmp_photo2020_outline.jpg", quality=88)

# drone frames next to renders from a similar (hand-picked, not solved) viewpoint
for fr, rn in (("w_040", "drone_e"), ("k1_45", "drone_s")):
    f_ = Image.open(f"refs/frames/{fr}.jpg").convert("RGB"); r_ = Image.open(sorted(glob.glob(f"{D}/{rn}.*"))[-1]).convert("RGB")   # .png fresh, .jpg once converted
    h = 520; f_ = f_.resize((round(f_.width * h / f_.height), h)); r_ = r_.resize((round(r_.width * h / r_.height), h))
    Image.fromarray(np.hstack([np.asarray(f_), np.asarray(r_)])).save(f"{D}/cmp_{rn}.jpg", quality=88)

# --- 2. plan: LoD2 ground outline vs model section 1.5 m above ground
fig, ax = plt.subplots(figsize=(12, 6.2))
for t, ps in lod:
    if t == "GroundSurface":
        p = np.array(ps); ax.fill(p[:, 0], p[:, 1], color="#9ecae1", alpha=.5, lw=0, label="LoD2 ground surface")
for m, c, lab, ls in ((master, "k", "model (with sacristy), section z = 1.5 m", "-"), (nosac, "#d62728", "model church-only", "--")):
    s = m.section(plane_origin=[0, 0, 1.5], plane_normal=[0, 0, 1])
    for i, e in enumerate(s.discrete):
        ax.plot(e[:, 0], e[:, 1], c, lw=1.1 if ls == "-" else 0.9, ls=ls, label=lab if i == 0 else None)
ax.set_aspect("equal"); ax.grid(alpha=.3); ax.legend(loc="lower left", fontsize=9)
ax.set_xlabel("x along the nave axis [m] (axis 17.85° N of E)"); ax.set_ylabel("y [m]")
ax.set_title("Plan: model vs. LoD2 footprint (DEBY_LOD2_5717218)")
plt.tight_layout(); plt.savefig(f"{D}/cmp_plan.png", dpi=110); plt.close()

# footprint agreement (area, IoU) from shapely polygons
from shapely.geometry import Polygon
g = Polygon([p[:2] for t, ps in lod if t == "GroundSurface" for p in ps])
mp = Polygon()
for e in master.section(plane_origin=[0, 0, 1.5], plane_normal=[0, 0, 1]).discrete:   # even-odd: holes cancel out
    mp = mp.symmetric_difference(Polygon(e[:, :2]).buffer(0))
M["plan"] = {"lod2_area_m2": round(g.area, 1), "model_area_m2": round(mp.area, 1),
             "iou": round(g.intersection(mp).area / g.union(mp).area, 3),
             "sym_diff_m2": round(g.symmetric_difference(mp).area, 1)}

# --- 3. elevations: model silhouette vs LoD2 wireframe (LoD2 tower pyramids are wrong, see README)
def silhouette(ax, m, i, j):
    tri = m.vertices[m.faces][:, :, [i, j]]
    ax.add_collection(PolyCollection(tri, facecolor="#bdbdbd", edgecolor="none"))
fig, axs = plt.subplots(1, 2, figsize=(15, 6.4), gridspec_kw={"width_ratios": [2.1, 1]})
for ax, (i, j, title, flip) in zip(axs, ((0, 2, "South elevation (looking north)", False), (1, 2, "West elevation (looking east)", True))):
    silhouette(ax, master, i, j)
    first = True
    for t, ps in lod:
        if t == "GroundSurface": continue
        p = np.array(ps + [ps[0]])
        ax.plot(p[:, i], p[:, j], color="#1f77b4" if t == "RoofSurface" else "#6baed6", lw=.6,
                label="LoD2 surfaces" if first else None); first = False
    for z, lab in ((20.86, "ridge 20.86"), (14.84, "eaves 14.84"), (28.81, "tower eaves 28.8 (model)"), (36.7, "helm apex 36.7 (model)")):
        ax.axhline(z, color="#d62728", lw=.5, ls=":"); ax.text(master.bounds[0][i] + .3, z + .25, lab, fontsize=7, color="#d62728")
    ax.set_xlim(master.bounds[0][i] - 1, master.bounds[1][i] + 1); ax.set_ylim(-1, 41)
    if flip: ax.invert_xaxis()
    ax.set_aspect("equal"); ax.grid(alpha=.25); ax.set_title(title); ax.set_xlabel("m"); ax.legend(loc="upper left", fontsize=8)
axs[0].set_ylabel("z [m]")
plt.tight_layout(); plt.savefig(f"{D}/cmp_elevations.png", dpi=110); plt.close()

# heights: LoD2 vs model at a few control points
def top_at(m, x, y):
    r, _, _ = m.ray.intersects_location([[x, y, 60]], [[0, 0, -1]])
    return round(float(r[:, 2].max()), 2) if len(r) else None
from shapely.geometry import Point
def lz(x, y):   # LoD2 roof height at (x, y): highest roof plane whose polygon contains the point
    best = None
    for t, ps in lod:
        p = np.array(ps)
        if t != "RoofSurface" or not Polygon(p[:, :2]).buffer(1e-3).contains(Point(x, y)): continue
        nrm = np.cross(p[1] - p[0], p[2] - p[0])
        if abs(nrm[2]) < 1e-6: continue
        z = p[0][2] - (nrm[0] * (x - p[0][0]) + nrm[1] * (y - p[0][1])) / nrm[2]
        best = z if best is None else max(best, z)
    return None if best is None else round(float(best), 2)
pts = {"nave ridge": (-15, 0), "nave roof, mid-slope": (-15, -2.2), "aisle roof, mid": (-15, -6.5),
       "transept ridge": (3.45, -10), "choir ridge": (8.6, 0), "main apse cone, near tip": (16.0, 0.0),
       "side apse cone S": (15.9, -6.1), "S tower top": (12.41, -6.55), "sacristy roof": (14, 12)}
M["heights"] = {k: {"lod2": lz(*v), "model": top_at(master, *v)} for k, v in pts.items()}

# --- 4. split: per-piece numbers + how far each piece settles onto its seats (sloped seats lose GAP to clearance)
body = trimesh.load("export/split/body_stone_1-250.stl", force="mesh")
rows = []
for f in sorted(glob.glob("export/split/*.stl")):
    p = trimesh.load(f, force="mesh"); name = f.split("/")[-1][:-10]
    row = {"piece": name, "vol_cm3": round(p.volume / 1000, 2), "size_mm": np.round(p.extents, 1).tolist(),
           "watertight": bool(p.is_watertight), "bodies": len(p.split(only_watertight=False))}
    if "body" not in name:
        pts, fi = trimesh.sample.sample_surface_even(p, 6000)
        down = p.face_normals[fi][:, 2] < -0.2
        o = pts[down] + [0, 0, 0.01]   # start just inside the piece, so a face lying on the body reads 0
        loc, idx, _ = body.ray.intersects_location(o, np.tile([0, 0, -1.0], (len(o), 1)), multiple_hits=False)
        row["settle_mm"] = round(float((o[idx][:, 2] - loc[:, 2]).min() - 0.01), 3) if len(loc) else None
    rows.append(row)
M["split"] = rows

# --- 5. split cross-sections: aisle eave, main roof over the nave, helm on its peg
def secplot(ax, x_or_y, val, lim, title):
    n = [1, 0, 0] if x_or_y == "x" else [0, 1, 0]; o = [val * K, 0, 0] if x_or_y == "x" else [0, val * K, 0]
    for f, c in (("export/split/body_stone_1-250.stl", "#7f7f7f"), *[(g_, "#d62728" if "red" in g_ else "#2ca02c") for g_ in glob.glob("export/split/*_red_*.stl") + glob.glob("export/split/*_copper_*.stl")]):
        s = trimesh.load(f, force="mesh").section(plane_origin=o, plane_normal=n)
        if s is None: continue
        for e in s.discrete:
            h = e[:, 1] if x_or_y == "x" else e[:, 0]
            ax.plot(h, e[:, 2], c, lw=.9)
    ax.set_xlim(*lim[0]); ax.set_ylim(*lim[1]); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_title(title, fontsize=10); ax.set_xlabel("mm at 1:250")
fig, axs = plt.subplots(1, 3, figsize=(15, 4.6))
secplot(axs[0], "x", -20, ((-37.5, -29), (26.5, 34)), "S aisle eave, x = -20 m")
secplot(axs[1], "x", -20, ((-19, -10), (56, 64)), "nave eave + aisle top, x = -20 m")
secplot(axs[2], "x", 12.41, ((-31, -21), (110, 122)), "S helm on its peg, x = 12.41 m")
axs[0].set_ylabel("z [mm]")
plt.suptitle("Colour split sections (grey body, red roof, green copper) — gaps are the 0.2 mm clearance", fontsize=11)
plt.tight_layout(); plt.savefig(f"{D}/split_sections.png", dpi=110); plt.close()

# --- 6. print files
M["files"] = {}
for f in sorted(glob.glob("export/*.stl")):
    m = trimesh.load(f, force="mesh")
    M["files"][f.split("/")[-1]] = {"size_mm": np.round(m.extents, 1).tolist(), "vol_cm3": round(m.volume / 1000, 1),
                                    "tris": len(m.faces), "watertight": bool(m.is_watertight)}
json.dump(M, open(f"{D}/metrics.json", "w"), indent=1)
print(json.dumps(M, indent=1))

# renders -> jpg (the README only needs them for viewing; keeps the repo small)
import os
for f in glob.glob(f"{D}/*.png"):
    b = os.path.basename(f)
    if b.startswith(("_", "cmp_", "split_sections")): continue
    Image.open(f).convert("RGB").save(f[:-4] + ".jpg", quality=87); os.remove(f)
