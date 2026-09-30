# Colour-split print set: stone body + red roofs + copper helms / apse cones, each exported as its own STL.
# Rebuilds the master first (exec of build_church.py), so run it on its own. SCALE / OUTDIR optional.
# Body = the master's own boolean pipeline with the roof/helm/cone parts taken out (+ peg holes in the tower
# tops). Each piece = its parts - body - wall blockers expanded by CLEAR, so it drops straight down onto the
# body, seats exactly on the sloped tops and keeps a CLEAR gap wherever it meets a wall. (Subtracting pieces
# from the finished master instead fails: every face coincides and the exact solver breaks.)
import bpy, bmesh, os, struct
BUILD = "/home/hooram/code/cad-work/kloster-biburg/blender/build_church.py"
g = {k: globals()[k] for k in ("SACRISTY", "FINIALS") if k in globals()}   # pass variant switches through
exec(open(BUILD).read(), g)
SCALE = globals().get("SCALE", 250)
OUTDIR = globals().get("OUTDIR", "/home/hooram/code/cad-work/kloster-biburg/export/split")
CLEAR = 0.05      # m: 0.2 mm at 1:250
BIG = 100

tmp = bpy.data.collections.new("Biburg_tmp"); g["root"].children.link(tmp)
out = bpy.data.collections.new("Biburg_split"); g["root"].children.link(out)

def boxobj(name, x0, x1, y0, y1, z0=-BIG, z1=BIG):
    return g["box"](name, x0, x1, y0, y1, z0, z1, g["M_STONE"], tmp)

def bake(name, members, minus=(), mat=None, tolerant=True):
    """New object = (union of members) - (union of minus), booleans applied."""
    base = bpy.data.objects.new(name, members[0].data.copy() if members[0].type == "MESH" else None)
    tmp.objects.link(base)
    for i, (objs, op) in enumerate(((members[1:], "UNION"), (list(minus), "DIFFERENCE"))):
        if not objs: continue
        c = bpy.data.collections.new(f"{name}_{op}"); tmp.children.link(c)
        for o in objs: c.objects.link(o) if o.name not in c.objects else None
        m = base.modifiers.new(op, "BOOLEAN"); m.operation = op; m.operand_type = "COLLECTION"; m.collection = c
        m.solver = "EXACT"; m.use_hole_tolerant = tolerant
    me = bpy.data.meshes.new_from_object(base.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    o = bpy.data.objects.new(name, me); out.objects.link(o)
    if mat: me.materials.clear(); me.materials.append(mat)
    return o

def write_stl(o, path):
    me = o.data; me.calc_loop_triangles(); k = 1000.0 / SCALE
    with open(path, "wb") as fh:
        fh.write(o.name.encode().ljust(80, b" ")[:80] + struct.pack("<I", len(me.loop_triangles)))
        for t in me.loop_triangles:
            fh.write(struct.pack("<3f", *t.normal))
            for vi in t.vertices: fh.write(struct.pack("<3f", *(me.vertices[vi].co * k)))
            fh.write(b"\0\0")

def check(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    r = (sum(1 for e in bm.edges if not e.is_manifold), round(bm.calc_volume(signed=True), 2)); bm.free(); return r

P = {o.name: o for o in g["C_PARTS"].objects}
X_W, X_TW, X_TE, X_TC, X_E = (g[k] for k in ("X_W", "X_TW", "X_TE", "X_TC", "X_E"))
NHW, TRY, TX0, TY0, TY1 = g["NAVE_HW"], g["TR_Y"], g["TOWER_X0"], g["TOWER_Y0"], g["TOWER_Y1"]

def blockers(tag):
    """Wall blockers expanded by CLEAR (removed from roof pieces -> assembly clearance)."""
    e = CLEAR
    return {
        # (towers reach 0.3 m past the east wall: trims the choir eave stub that would poke out beside them)
        "towers": [boxobj(f"{tag}_tS", TX0 - e, X_E + 0.3, -TY1 - e, -TY0 + e), boxobj(f"{tag}_tN", TX0 - e, X_E + 0.3, TY0 - e, TY1 + e)],
        "nave": [boxobj(f"{tag}_nave", X_W - 5, X_TC, -NHW - e, NHW + e)],
        "transept": [boxobj(f"{tag}_tr", X_TW - e, X_TE + e, -TRY - 5, TRY + 5)],
        "transept_core": [boxobj(f"{tag}_trc", X_TW - e, X_TE + e, -TRY - e, TRY + e)],   # the transept itself only
        "choir": [boxobj(f"{tag}_ch", X_TC, X_E + 5, -NHW - e, NHW + e)],
        "east": [boxobj(f"{tag}_east", -BIG, X_E + e, -BIG, BIG)],
    }
EXP = blockers("exp")

R, C = g["M_ROOF"], g["M_COPPER"]
# The 45 deg eave fillets (print supports under the flatter eaves) go with their roof piece in the split: a clean,
# solid eave on the piece, and no stone ledge left under the red roof on the body.
pieces = {  # name: (member part names, blocker keys, material)
    "roof_main_red": (["cross_roof"], ["towers"], R),
    "roof_aisle_S_red": (["aisle_S_roof", "aisle_front_S_roof", "aisle_S_eavefillet", "aisle_front_S_eavefillet"], ["nave", "transept"], R),
    "roof_aisle_N_red": (["aisle_N_roof", "aisle_front_N_roof", "aisle_N_eavefillet", "aisle_front_N_eavefillet"], ["nave", "transept"], R),
    "roof_sidechoir_S_red": (["sidebay_-1_roof"], ["towers", "transept", "choir"], R),
    "roof_sidechoir_N_red": (["sidebay_1_roof"], ["towers", "transept", "choir"], R),
    "apse_main_copper": (["apse_roof", "apse_seam*"], ["east"], C),
    "apse_S_copper": (["sapse_-1_roof", "sapse_-1_seam*"], ["east"], C),
    "apse_N_copper": (["sapse_1_roof", "sapse_1_seam*"], ["east"], C),
}
if g["SACRISTY"]:
    pieces["roof_sacristy_red"] = (["sacristy_roof", "sacristy_chimney*", "sacristy_fillet*"], ["towers", "transept_core"], R)
pegs = {}
for t, (y0, y1) in (("S", (-TY1, -TY0)), ("N", (TY0, TY1))):
    cx, cy, te = (TX0 + X_E) / 2, (y0 + y1) / 2, g["TOWER_EAVES"]
    mem = [f"tower_{t}_helm", f"tower_{t}_seam*"] + [n for n in (f"tower_{t}_ball", f"tower_{t}_rod", f"tower_{t}_arm") if n in P]
    # peg stands up from the tower top (body), hole in the helm -> the helm keeps a flat bottom to print on
    peg = boxobj(f"peg{t}", cx - 0.6 + CLEAR, cx + 0.6 - CLEAR, cy - 0.6 + CLEAR, cy + 0.6 - CLEAR, te - 0.3, te + 0.8)
    hole = boxobj(f"peg{t}_hole", cx - 0.6, cx + 0.6, cy - 0.6, cy + 0.6, te - 0.5, te + 0.8 + CLEAR)
    pegs[t] = peg
    pieces[f"helm_{t}_copper"] = (mem, [], C, hole)

# body: take every piece part out of the master's union, add the peg holes to its cutters, evaluate
master = bpy.data.objects["KlosterkircheBiburg"]
expand = lambda names: [n for pat in names for n in P if (n.startswith(pat[:-1]) if pat.endswith("*") else n == pat)]
moved = [P[n] for v in pieces.values() for n in expand(v[0])]
for o in moved: g["C_PARTS"].objects.unlink(o); tmp.objects.link(o)
for h in pegs.values(): tmp.objects.unlink(h); g["C_ADD"].objects.link(h)
dg = bpy.context.evaluated_depsgraph_get(); dg.update()
body = bpy.data.objects.new("body_stone", bpy.data.meshes.new_from_object(master.evaluated_get(dg)))
out.objects.link(body)
# restore the master
for o in moved: tmp.objects.unlink(o); g["C_PARTS"].objects.link(o)
for h in pegs.values(): g["C_ADD"].objects.unlink(h); tmp.objects.link(h)

results = {"body_stone": body}
for name, v in pieces.items():
    mem, keys, mat = v[:3]
    extra = [v[3]] if len(v) > 3 else []   # helm: peg hole
    if name.startswith("roof_sidechoir"): extra.append(results["roof_main_red"])   # fits under the choir eave
    results[name] = bake(name, [P[m] for m in expand(mem)], [b for k in keys for b in EXP[k]] + [body] + extra, mat)

os.makedirs(OUTDIR, exist_ok=True)
report = {}
for name, o in results.items():
    bm = bmesh.new(); bm.from_mesh(o.data)   # weld boolean seams (near-duplicate verts) like export_stl.py does
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)   # zero-area slivers from the booleans
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    write_stl(o, os.path.join(OUTDIR, f"{name}_1-{SCALE}.stl"))
    report[name] = check(o)
# clean temp scaffolding (op collections only *link* master parts, so just drop them), keep the split pieces
for c in list(tmp.children): bpy.data.collections.remove(c)
for o in list(tmp.objects): bpy.data.objects.remove(o)
bpy.data.collections.remove(tmp)
out.hide_viewport = out.hide_render = True
result = {"out": OUTDIR, "pieces (non_manifold, vol m3)": report}
