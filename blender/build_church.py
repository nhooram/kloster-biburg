# Klosterkirche Maria Immaculata, Biburg -- parametric generator.
# Run inside Blender (via tools/bl.py). Units: metres. Frame: +x east (church axis), +y north,
# y=0 on the nave axis, z=0 ground. Rotation from real world: axis is 17.85 deg north of east.
# Sources: see ../README.md. Dimensions from Bavarian LoD2 (DEBY_LOD2_5717218) unless noted.
import bpy, bmesh, math
from mathutils import Vector

# ---------------------------------------------------------------- dimensions (calibration knobs)
X_W = -27.46          # west facade plane
X_TW, X_TE = -0.95, 7.85  # transept west / east walls
X_TC = (X_TW + X_TE) / 2  # transept ridge line / crossing centre
X_E = 15.42           # choir + tower east wall plane
NAVE_HW = 4.30        # nave half width (outer)
AISLE_Y = 8.65        # aisle outer wall |y|
TR_Y = 11.95          # transept gable walls |y|
RIDGE = 20.86         # nave / transept / choir ridge
EAVES = 14.84         # nave / transept / choir eaves
AISLE_TOP, AISLE_EAVES = 10.50, 7.30
TOWER_X0 = 9.40       # tower west face (side-choir bay between transept and tower)
TOWER_Y0, TOWER_Y1 = 4.30, 8.80
# Tower heights from a camera-pose fit (tools/pnp_check.py) of refs/photos/2020_St_Maria_Biburg.jpg
# against LoD2 corners: eaves 27.2-28.6, helm apex 35.0-35.7, cross top ~37.9 (LoD2 max 39.2 = the cross;
# its 23.4 m eave line is a bad pyramid fit). Wikipedia: "36 m" towers.
# The eave height is then set by the belfry layout (upper end of the fitted range):
#  - lower band at 20.3 m (KlosterkircheBiburg2_Niederbayern.JPG); the two belfry storeys are identical, the eave
#    cornice (chamfer starts at TOWER_EAVES - 0.63) acting as the band above the upper storey (bands reach 0.28 down)
#  - the upper storey's recessed panel on the front/back (E/W, 4.5 m) faces is nearly square with an even margin
#    PANEL_M of plain wall at both sides and at the top (under the cornice).
T_LOWER, PANEL_M, HELM_H = 20.3, 0.9, 7.9
PANEL_W = (TOWER_Y1 - TOWER_Y0) - 2 * PANEL_M                     # 2.7 m
# eaves = upper band + 0.2 (panel foot) + PANEL_W (square panel) + PANEL_M + 0.63, upper band = storey midpoint:
TOWER_EAVES = T_LOWER - 0.35 + 2 * (0.83 + PANEL_W + PANEL_M)     # ~28.8 m
TOWER_APEX = TOWER_EAVES + HELM_H
STOREY = (TOWER_EAVES - 0.63 + 0.28 - T_LOWER) / 2               # ~4.1 m
T_UPPER = T_LOWER + STOREY                                       # ~24.4 m
BELFRY_SILL = 0.15              # arcade sill above its band line
NH_BELFRY = 2.6                 # niche height, both storeys
CLOCK_Z = 18.85   # clear of the lower band chamfer
# Apse cone tips: LoD2 gives 13.73 / 9.17 m (~27 / 39 deg, a poor fit like its tower pyramids); the photos
# (MI_Apsis_880/881) show steeper cones -> 50 deg for all three (slope over the eave ring r + 0.3).
APSE_PITCH = 50                       # deg, all three apse cones (photos)
APSE_R, APSE_EAVES = 3.95, 11.60
APSE_APEX = APSE_EAVES + (APSE_R + 0.3) * math.tan(math.radians(APSE_PITCH))
SAPSE_EAVES = 8.3   # LoD2 7.45 m; photos show the side apses taller relative to the main apse
SAPSE_R, SAPSE_Y = 1.80, 6.10
SAPSE_APEX = SAPSE_EAVES + (SAPSE_R + 0.3) * math.tan(math.radians(APSE_PITCH))
SIDEBAY_HI, SIDEBAY_LO = 14.20, 8.60
# Window x-centres back-projected from the 2020 photo via the solved camera (tools/pnp_check.py).
CLERE_X = [-24.78, -20.47, -16.27, -12.12, -7.92, -3.73]
AISLE_X = [-24.04, -19.71, -15.60, -11.61, -7.55, -3.63]
PORTAL_Y = 0.3        # west portal sits ~0.3 m north of the nave axis (photo back-projection)
EAVE_OV, GABLE_OV, ROOF_T = 0.35, 0.10, 0.30
BASE = True           # printable plinth under the building
FINIALS = globals().get("FINIALS", True)   # tower balls + crosses; False for the no-finial print variant
SACRISTY = globals().get("SACRISTY", True)  # the low sacristy annex north of the north tower; False = church only
SEG = 16              # arc resolution

COL = "Biburg"

# ---------------------------------------------------------------- scene setup
def reset():
    if COL in bpy.data.collections:
        c = bpy.data.collections[COL]
        for ch in list(c.children):
            for o in list(ch.objects): bpy.data.objects.remove(o)
            bpy.data.collections.remove(ch)
        for o in list(c.objects): bpy.data.objects.remove(o)
        bpy.data.collections.remove(c)
    bpy.data.orphans_purge(do_recursive=True)   # stale meshes would make new names get .001 suffixes
    for n in ("Cube",):
        if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
    root = bpy.data.collections.new(COL); bpy.context.scene.collection.children.link(root)
    parts = bpy.data.collections.new(COL + "_parts"); root.children.link(parts)
    cuts = bpy.data.collections.new(COL + "_cutters"); root.children.link(cuts)
    adds = bpy.data.collections.new(COL + "_details"); root.children.link(adds)  # unioned AFTER the cuts
    return root, parts, cuts, adds

def mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf: bsdf.inputs["Base Color"].default_value = (*rgb, 1); bsdf.inputs["Roughness"].default_value = 0.85
    return m

M_STONE = mat("bib_stone", (0.78, 0.75, 0.68))
M_ROOF = mat("bib_roof", (0.62, 0.22, 0.13))
M_COPPER = mat("bib_copper", (0.30, 0.55, 0.45))
M_DARK = mat("bib_opening", (0.05, 0.05, 0.06))
M_GOLD = mat("bib_gold", (0.8, 0.6, 0.15))

root, C_PARTS, C_CUTS, C_ADD = reset()

def obj(name, verts, faces, m, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o

def extrude(name, pts3_a, pts3_b, m, coll):
    """Closed prism between two congruent 3D loops."""
    n = len(pts3_a)
    faces = [list(range(n))[::-1], list(range(n, 2 * n))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return obj(name, list(pts3_a) + list(pts3_b), faces, m, coll)

def prism(name, poly, plane, a0, a1, m=M_STONE, coll=None):
    """poly: 2D loop. plane 'YZ' extrudes along x, 'XZ' along y, 'XY' along z."""
    f = {"YZ": lambda s, t, a: (a, s, t), "XZ": lambda s, t, a: (s, a, t), "XY": lambda s, t, a: (s, t, a)}[plane]
    return extrude(name, [f(s, t, a0) for s, t in poly], [f(s, t, a1) for s, t in poly], m, coll or C_PARTS)

def box(name, x0, x1, y0, y1, z0, z1, m=M_STONE, coll=None):
    return prism(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "XY", z0, z1, m, coll)

def ledge(name, x0, x1, y0, y1, p, z0, z1, m=M_STONE, coll=None):
    """Band projecting p around a rectangle from z0 to z1, with a 45 deg chamfered underside (prints unsupported)."""
    sq = lambda o, z: [(x0 - o, y0 - o, z), (x1 + o, y0 - o, z), (x1 + o, y1 + o, z), (x0 - o, y1 + o, z)]
    extrude(name + "_chamfer", sq(-0.02, z0 - p - 0.02), sq(p, z0), m, coll or C_PARTS)
    box(name, x0 - p, x1 + p, y0 - p, y1 + p, z0 - 0.02, z1, m, coll)

# ---------------------------------------------------------------- massing helpers
BELL_K = 1.2   # m: bell-cast eave kick (photos): over the last BELL_K the roof flattens to 60 % of its pitch

def bell(t, sl):
    """Height gain over the straight roof line at distance t (m) inward from the eave tip: raised tip, slope
    0.6*sl at the tip, blending tangentially into the main plane at t = BELL_K."""
    return 0.2 * sl * (BELL_K - t) ** 2 / BELL_K if t < BELL_K else 0.0

BELL_T = (0.0, 0.3, 0.6, 0.9, BELL_K)

def gable_profile(s0, s1, ze, zr, kick=False):
    """House section. kick: the wall tops follow the roof's bell-cast curve (the roof has an even thickness,
    so its underside curves up at the eave too and the walls must rise with it)."""
    if not kick:
        return [(s0, 0), (s1, 0), (s1, ze), ((s0 + s1) / 2, zr), (s0, ze)]
    sl = (zr - ze) / ((s1 - s0) / 2)
    ts = [t for t in BELL_T if t > EAVE_OV]   # t: distance inward from the eave tip (the wall is at t = EAVE_OV)
    right = [(s1, ze + bell(EAVE_OV, sl))] + [(s1 + EAVE_OV - t, ze + sl * (t - EAVE_OV) + bell(t, sl)) for t in ts]
    left = [(s0 - EAVE_OV + t, ze + sl * (t - EAVE_OV) + bell(t, sl)) for t in reversed(ts)] + [(s0, ze + bell(EAVE_OV, sl))]
    return [(s0, 0), (s1, 0)] + right + [((s0 + s1) / 2, zr)] + left

def leanto(name, a0, a1, y_out, y_in, z_out, z_in, plane="YZ", go0=None, go1=None, fillet_a0=None):
    """Wall + roof slab of a lean-to; y_in against the taller wall. Bell-cast eave with an even roof thickness:
    the slab's underside and the wall top follow the same curve as its top."""
    sgn = 1 if y_in > y_out else -1
    sl = (z_in - z_out) / abs(y_in - y_out)
    ts = [t for t in BELL_T if t > EAVE_OV]   # t: distance inward from the eave tip (the wall is at t = EAVE_OV)
    wall_top = [(y_out + sgn * (t - EAVE_OV), z_out + sl * (t - EAVE_OV) + bell(t, sl)) for t in reversed(ts)]
    prism(name, [(y_out, 0), (y_in, 0), (y_in, z_in)] + wall_top + [(y_out, z_out + bell(EAVE_OV, sl))], plane, a0, a1)
    lo = (y_out - sgn * EAVE_OV, z_out - EAVE_OV * sl); hi = (y_in + sgn * 0.4, z_in + 0.4 * sl)
    top = [(lo[0] + sgn * t, lo[1] + ROOF_T + sl * t + bell(t, sl)) for t in BELL_T]   # bell-cast eave
    bottom = [(lo[0] + sgn * t, lo[1] - 0.1 + sl * t + bell(t, sl)) for t in reversed(BELL_T)]
    prism(name + "_roof", top + [(hi[0], hi[1] + ROOF_T), (hi[0], hi[1] - 0.1)] + bottom,
          plane, a0 - (GABLE_OV if go0 is None else go0), a1 + (GABLE_OV if go1 is None else go1), M_ROOF)
    if sl < 1:  # roof underside flatter than 45 deg: fill under the eave with a 45 deg stone fillet
        tip = (lo[0] + sgn * 0.02, lo[1] - 0.05 + 0.02 * sl + bell(0.02, sl))   # 2 cm inside the eave face
        wall_hi = (y_out + sgn * 0.05, z_out - 0.05 + 0.05 * sl + bell(EAVE_OV + 0.05, sl))
        wall_lo = (y_out + sgn * 0.05, lo[1] - 0.1 - EAVE_OV - 0.05)
        prism(name + "_eavefillet", [tip, wall_hi, wall_lo], plane, a0 + 0.02 if fillet_a0 is None else fillet_a0, a1)

def arc_pts(cx, cy, r, a0, a1, n=SEG):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]

def apse(name, cx, cy, r, ze, za, wall_seg=SEG * 2, seams=0):
    """wall_seg: facets of the wall; chosen so every frieze arch centre lands mid-facet (a flat arch
    cutter tangent on a facet corner edge is degenerate for the boolean)."""
    back = 0.6
    ring = arc_pts(cx, cy, r, -math.pi / 2, math.pi / 2, wall_seg)
    prism(name, ring + [(cx - back, cy + r), (cx - back, cy - r)], "XY", 0, ze)
    # plinth ring
    prism(name + "_plinth", arc_pts(cx, cy, r + 0.12, -math.pi / 2, math.pi / 2, wall_seg) +
          [(cx - back, cy + r + 0.12), (cx - back, cy - r - 0.12)], "XY", 0, 0.7)
    # cornice
    def ring(rr, z, seg=SEG * 2): return [(x, y, z) for x, y in arc_pts(cx, cy, rr, -math.pi / 2, math.pi / 2, seg) + [(cx - back, cy + rr), (cx - back, cy - rr)]]
    extrude(name + "_cornice_chamfer", ring(r + 0.09, ze - 0.44), ring(r + 0.18, ze - 0.35), M_STONE, C_PARTS)
    prism(name + "_cornice", arc_pts(cx, cy, r + 0.18, -math.pi / 2, math.pi / 2, SEG * 2) +
          [(cx - back, cy + r + 0.18), (cx - back, cy - r - 0.18)], "XY", ze - 0.37, ze + 0.03)  # proud of wall top: no coplanar faces
    extrude(name + "_roof_flare", ring(r + 0.16, ze - 0.14, SEG * 3), ring(r + 0.28, ze - 0.01, SEG * 3), M_STONE, C_PARTS)  # facets offset from the cornice's  # 45 deg under the cone eave
    # half cone roof
    # The cone wraps 2 deg past the wall at each end and its tip sits 2 cm inside the wall: no vertex of it lies
    # exactly on the wall plane, so cuts against that wall (split: cone - body) stay clean.
    R = r + 0.3; z0 = ze - 0.02; wrap = math.radians(2)
    ringR = [(x, y, z0) for x, y in arc_pts(cx, cy, R, -math.pi / 2 - wrap, math.pi / 2 + wrap, SEG * 2)]
    n = len(ringR)
    tip_x = cx - 0.02
    verts = ringR + [(cx - back, cy + R, z0), (cx - back, cy - R, z0), (tip_x, cy, za), (cx - back, cy, za + 0.3)]
    bp, bm_, ap, ab = n, n + 1, n + 2, n + 3
    faces = [list(range(n)) + [bp, bm_]]
    faces += [[i, i + 1, ap] for i in range(n - 1)]
    faces += [[n - 1, bp, ab, ap], [bm_, 0, ap, ab], [bp, bm_, ab]]
    obj(name + "_roof", verts, faces, M_COPPER, C_PARTS)
    # copper standing seams (photos): triangular ridges from the eave almost to the tip.
    # 0.12 m wide x 0.08 m tall = 0.48 x 0.32 mm at 1:250; triangular section, so no overhang to print.
    w, h = 0.12, 0.08
    apex = Vector((tip_x, cy, za))
    for i in range(seams):
        th = -math.pi / 2 + math.pi * (i + 0.5) / seams
        rim = Vector((cx + R * math.cos(th), cy + R * math.sin(th), z0))
        nrm = Vector((math.cos(th) * (za - z0), math.sin(th) * (za - z0), R)).normalized()   # cone surface normal
        tng = Vector((-math.sin(th), math.cos(th), 0))
        def section(t):   # width + height taper with the distance to the tip (seams converge)
            p = apex + (rim - apex) * t
            return [p + tng * (w * t / 2) - nrm * 0.02, p - tng * (w * t / 2) - nrm * 0.02, p + nrm * (h * max(t, 0.4))]
        # end 3% short of the eave (clear of the cone's flat underside) and keep the tip >= 0.15 m in front of
        # the wall, clear of the plane the split cuts the cone's back off at
        t_tip = max(0.08, 0.15 / max(R * math.cos(th), 1e-3))
        if t_tip < 0.9:
            obj(f"{name}_seam{i}", section(0.97) + section(t_tip), [[0, 1, 2], [3, 5, 4], [0, 3, 4, 1], [1, 4, 5, 2], [2, 5, 3, 0]], M_COPPER, C_PARTS)

# ---------------------------------------------------------------- cutters (recesses)
def wall_frame(origin, u_dir, normal):
    O, U, N = Vector(origin), Vector(u_dir).normalized(), Vector(normal).normalized()
    Z = Vector((0, 0, 1))
    return lambda u, v, n: O + U * u + Z * v + N * n

def cut_loop(name, frame, loop, depth, m=M_STONE, outside=0.4):
    return extrude(name, [frame(u, v, outside) for u, v in loop], [frame(u, v, -depth) for u, v in loop], m, C_CUTS)

def arch_loop(uc, sill, w, h, n=SEG):
    r = w / 2; spring = sill + h - r
    top = [(uc + r * math.cos(math.pi * i / n), spring + r * math.sin(math.pi * i / n)) for i in range(n + 1)]
    return [(uc - r, sill), (uc + r, sill)] + top[:-1] + [(uc - r, spring)]

def circle_loop(uc, vc, r, n=SEG * 2):
    return [(uc + r * math.cos(2 * math.pi * i / n), vc + r * math.sin(2 * math.pi * i / n)) for i in range(n)]

def cross_loop(uc, vc, s, t):
    a, b = s / 2, t / 2
    return [(uc - b, vc - a), (uc + b, vc - a), (uc + b, vc - b), (uc + a, vc - b), (uc + a, vc + b), (uc + b, vc + b),
            (uc + b, vc + a), (uc - b, vc + a), (uc - b, vc + b), (uc - a, vc + b), (uc - a, vc - b), (uc - b, vc - b)]

def window(name, frame, uc, sill, w, h, niche=None, depth=0.45):
    """Window opening. With `niche` (outer arch w, h, sill at the wall face) it is a Romanesque splayed
    embrasure: the reveal slopes straight from the outer arch to the glass arch `depth` inside."""
    if not niche:
        cut_loop(name, frame, arch_loop(uc, sill, w, h), depth, M_DARK)
        return
    nw, nh, ns = niche
    inner, outer = arch_loop(uc, sill, w, h), arch_loop(uc, ns, nw, nh)
    o = 0.3  # carry the splay on past the wall face so the cut exits cleanly
    beyond = [(uo + (uo - ui) * o / depth, vo + (vo - vi) * o / depth) for (ui, vi), (uo, vo) in zip(inner, outer)]
    cut = extrude(name, [frame(u, v, -depth) for u, v in inner], [frame(u, v, o) for u, v in beyond], M_STONE, C_CUTS)
    cut.data.materials.append(M_DARK)
    n0 = len(inner)  # the inner cap (the glass) is the face made only of the first loop's verts
    for f in cut.data.polygons:
        if all(vi < n0 for vi in f.vertices): f.material_index = 1

def bifora(name, frame, uc, sill, face_w, nh):
    """Coupled belfry arcade (photos): arched niche holding two arched openings that spring from a
    colonnette (base, shaft, 45 deg capital) standing between them."""
    nw = min(2.2, face_w - 1.4)
    cut_loop(name + "_n", frame, arch_loop(uc, sill, nw, nh), 0.22)
    # Snug fit (photos): the twin arches spring from the same line as the niche arch and fill it, leaving an
    # m-wide margin at the jambs and a small tympanum above the colonnette.
    g, m = 0.3, 0.08                      # pier above the colonnette, margin inside the niche
    ow = (nw - 2 * m - g) / 2             # each opening ~0.87 m
    spring = sill + nh - nw / 2           # = the niche arch's springing line
    o0 = sill + 0.08
    h = spring - o0 + ow / 2
    for k, du in enumerate((-1, 1)):
        cut_loop(f"{name}_o{k}", frame, arch_loop(uc + du * (g / 2 + ow / 2), o0, ow, h), 0.8, M_DARK)
    # open the space between the two openings below the springing: the colonnette stands in it
    # (depth / floor offset from the openings' so no cutter faces coincide)
    cut_loop(f"{name}_mid", frame, [(uc - g / 2 - 0.02, o0 - 0.01), (uc + g / 2 + 0.02, o0 - 0.01), (uc + g / 2 + 0.02, spring - 0.05), (uc - g / 2 - 0.02, spring - 0.05)], 0.78, M_DARK)
    nc, r = -0.225 - (g / 2 - 0.01), 0.1  # colonnette set so its capital's top edge is flush (3 mm back) with the arch face
    col = lambda rr, z0, z1, nm: extrude(nm, [frame(a, z0, b) for a, b in circle_loop(uc, nc, rr, 16)],
                                         [frame(a, z1, b) for a, b in circle_loop(uc, nc, rr, 16)], M_STONE, C_ADD)
    col(r + 0.04, o0 - 0.05, o0 + 0.12, f"{name}_cbase")   # radius < g/2: not tangent to the jambs
    col(r, o0 - 0.05, spring - 0.3, f"{name}_cshaft")
    sq = lambda q, z: [frame(uc - q, z, nc - q), frame(uc + q, z, nc - q), frame(uc + q, z, nc + q), frame(uc - q, z, nc + q)]
    cw = g / 2 - 0.01                     # capital no wider than the pier between the two arches
    extrude(f"{name}_ccap", sq(r, spring - 0.3), sq(cw, spring - 0.2), M_STONE, C_ADD)        # flared capital
    # impost block into the pier, its front flush with the face the arches are cut into (niche back, n = -0.22;
    # 2 mm behind it so the two faces never coincide)
    blk = lambda z: [frame(uc - cw, z, nc - cw), frame(uc + cw, z, nc - cw), frame(uc + cw, z, -0.222), frame(uc - cw, z, -0.222)]
    extrude(f"{name}_cblk", blk(spring - 0.21), blk(spring + 0.06), M_STONE, C_ADD)

def taper_cut(name, frame, loop, depth, outside):
    """Cutter whose profile rises 45 deg as it comes out of the wall, so the cut leaves a sloped
    (printable) underside instead of a flat overhang."""
    return extrude(name, [frame(u, v, -depth) for u, v in loop],
                   [frame(u, v + outside + depth, outside) for u, v in loop], M_STONE, C_CUTS)

def arch_line(n, pitch, w, h, top_c, slope):
    """Stepped arch line of a rising arch frieze, right outer -> centre -> left outer, and the cell sills.
    Each pier between two arches hangs to one level (the outer, lower cell's), flush with the arch jambs."""
    c = [pitch * (i + 0.5) for i in range(n)]            # arch centres (right side)
    sills = [top_c - ci * slope - h for ci in c]          # pier-bottom level of each cell
    R = [ci + w / 2 for ci in c]                          # right jamb of each arch
    spring = [sl + h - w / 2 for sl in sills]
    right = []
    for k in reversed(range(n)):
        arc = [(c[k] + (w / 2) * math.cos(math.pi * j / SEG), spring[k] + (w / 2) * math.sin(math.pi * j / SEG)) for j in range(SEG + 1)]
        right += [(R[k], sills[k])] + arc + [(R[k] - w, sills[k])]
        right += [((R[k - 1], sills[k]) if k else (0, sills[0]))]   # pier bottom, then step up at next jamb
    right = right[:-1]                                    # centre point added once below
    left = [(-u, v) for u, v in reversed(right)]
    return right + [(0, sills[0])] + left, sills

# ================================================================ BUILD
# --- nave, aisles, transept, choir (walls + roof slabs)
prism("nave", gable_profile(-NAVE_HW, NAVE_HW, EAVES, RIDGE, kick=True), "YZ", X_W, X_TC)
# The west front's shoulders over the aisle ends have their own roof strip (photos): FACADE_D deep, same top edge
# against the nave wall (+2 cm, so the two never share faces), ~2.5 deg flatter, so its eave sits ~0.3 m higher
# and it steps down onto the aisle roof behind it.
FACADE_D = 0.9
a_pitch = math.atan((AISLE_TOP - AISLE_EAVES) / (AISLE_Y - NAVE_HW))
SHOULDER_EAVES = AISLE_TOP - (AISLE_Y - NAVE_HW) * math.tan(a_pitch - math.radians(2.5))   # ~7.6 m
for s in (-1, 1):
    t = 'N' if s > 0 else 'S'
    leanto(f"aisle_front_{t}", X_W, X_W + FACADE_D, s * AISLE_Y, s * (NAVE_HW - 0.2), SHOULDER_EAVES, AISLE_TOP + 0.02, go1=0)
    # aisle roof + fillet start at the shoulder strip's back edge (2 cm under it): a clean step, no tab below
    leanto(f"aisle_{t}", X_W + FACADE_D - 0.3, X_TW + 0.2, s * AISLE_Y, s * (NAVE_HW - 0.2), AISLE_EAVES, AISLE_TOP,
           go0=-0.28, fillet_a0=X_W + FACADE_D - 0.02)
prism("transept", gable_profile(X_TW, X_TE, EAVES, RIDGE, kick=True), "XZ", -TR_Y, TR_Y)

# --- roof of the cross, as ONE shell: (outer envelope) - (inner envelope).
# Each envelope is the union of two gable blocks (nave+choir, transept). A union of gable blocks gives the right
# valleys by itself, on the top surface and on the underside, so no corner pieces are needed.
# Outer top = gable plane + ROOF_T, underside = gable plane - 0.1 (sits 0.1 into the walls); eaves overhang OV.
OV, FLOOR = EAVE_OV, EAVES - 2.5

def gable_block(name, plane, s0, s1, a0, a1, lift, grow, floor, coll, zr=RIDGE, kick=False):
    """Prism under a gable roof plane raised by `lift`, footprint grown by `grow`, from `floor` up.
    kick: bell-cast eaves (used on the outer AND inner envelope, so the roof keeps an even thickness)."""
    sl = (zr - EAVES) / ((s1 - s0) / 2); sc = (s0 + s1) / 2
    e0, e1 = s0 - OV - grow, s1 + OV + grow
    z_edge = zr + lift - sl * (sc - e0)
    ts = BELL_T if kick else (0.0,)
    right = [(e1 - t, z_edge + sl * t + bell(t, sl)) for t in ts]
    left = [(e0 + t, z_edge + sl * t + bell(t, sl)) for t in reversed(ts)]
    return prism(name, [(e0, floor), (e1, floor)] + right + [(sc, zr + lift)] + left, plane,
                 a0 - grow, a1 + grow, M_ROOF, coll)

tmpc = bpy.data.collections.new(COL + "_rooftmp"); root.children.link(tmpc)
outer = [gable_block("ro_nave", "YZ", -NAVE_HW, NAVE_HW, X_W - GABLE_OV, X_E + GABLE_OV, ROOF_T, 0, FLOOR, tmpc, kick=True),
         gable_block("ro_tr", "XZ", X_TW, X_TE, -TR_Y - GABLE_OV, TR_Y + GABLE_OV, ROOF_T, 0, FLOOR - 0.3, tmpc, kick=True)]
inner = [gable_block("ri_nave", "YZ", -NAVE_HW, NAVE_HW, X_W - GABLE_OV, X_E + GABLE_OV, -0.1, 0.01, FLOOR - 1, tmpc, kick=True),
         gable_block("ri_tr", "XZ", X_TW, X_TE, -TR_Y - GABLE_OV, TR_Y + GABLE_OV, -0.1, 0.01, FLOOR - 1.3, tmpc, kick=True)]
ci = bpy.data.collections.new(COL + "_rooftmp_in"); tmpc.children.link(ci)
for o in inner: tmpc.objects.unlink(o); ci.objects.link(o)
co = bpy.data.collections.new(COL + "_rooftmp_out"); tmpc.children.link(co)
for o in outer[1:]: tmpc.objects.unlink(o); co.objects.link(o)
m1 = outer[0].modifiers.new("u", "BOOLEAN"); m1.operation = "UNION"; m1.operand_type = "COLLECTION"; m1.collection = co; m1.solver = "EXACT"
m2 = outer[0].modifiers.new("d", "BOOLEAN"); m2.operation = "DIFFERENCE"; m2.operand_type = "COLLECTION"; m2.collection = ci; m2.solver = "EXACT"
roof_me = bpy.data.meshes.new_from_object(outer[0].evaluated_get(bpy.context.evaluated_depsgraph_get()))
roof_me.name = "cross_roof"
cross_roof = bpy.data.objects.new("cross_roof", roof_me); C_PARTS.objects.link(cross_roof)
for c in (ci, co, tmpc):
    for o in list(c.objects): bpy.data.objects.remove(o)
    bpy.data.collections.remove(c)

prism("choir", gable_profile(-NAVE_HW, NAVE_HW, EAVES, RIDGE, kick=True), "YZ", X_TC, X_E)


# --- side-choir bays between transept and towers (lean-tos)
for s in (-1, 1):
    # roof ends 3 cm into the tower: its eave overhang must not stick out in front of the tower face
    leanto(f"sidebay_{s}", X_TE - 0.2, TOWER_X0 + 0.2, s * TOWER_Y1, s * (NAVE_HW - 0.2), SIDEBAY_LO, SIDEBAY_HI, go1=-0.17)

# --- sacristy (drone frames 001-027; footprint + roof from LoD2): low annex in the corner between the north
# transept and the north tower, running past the tower and, east of it, south until its wall meets the north
# side apse (staying well below the apse's top). Roof = the lower of a north-falling and an east-falling slope
# (LoD2 pitch), i.e. a lean-to against the tower with a hipped east end: a diagonal hip from the tower corner.
SAC_X0, SAC_X1, SAC_Y1, SAC_YS = X_TE - 0.55, 16.9, 13.47, 7.0  # SAC_YS: south edge east of the tower (inside the apse)
# angled north-west wall (LoD2 footprint (7.54, 12.01) -> (9.36, 13.44)): it starts on the transept's north face,
# west of the transept's corner, so it is part of the floor plan (no cutter, no slivers)
SAC_K = (13.44 - 12.01) / (9.36 - 7.54)
def sac_cx(y, d=0.0):
    """x of the angled wall line at y, shifted outward (north-west) by d."""
    return 7.54 + (y - 12.01) / SAC_K - d * math.sqrt(1 + SAC_K ** 2) / SAC_K
SAC_EAVES = 6.35
SAC_OV = 0.12        # small eaves, straight roof (no bell-cast kick) on the sacristy (photos)
sac_sl = (9.33 - 6.27) / (13.44 - 9.10)                         # LoD2 roof pitch

def baked(name, base, steps, coll, m):
    """Apply boolean steps [(op, obj)] to `base` and return a new object in `coll`; temp objects removed."""
    for i, (op, o) in enumerate(steps):
        md = base.modifiers.new(f"b{i}", "BOOLEAN"); md.operation = op; md.object = o; md.solver = "EXACT"
    me = bpy.data.meshes.new_from_object(base.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    me.materials.clear(); me.materials.append(m)
    res = bpy.data.objects.new(name, me); coll.objects.link(res)
    for o in [base] + [o for _, o in steps]: bpy.data.objects.remove(o)
    return res

if SACRISTY:
    tmps = bpy.data.collections.new(COL + "_sactmp"); root.children.link(tmps)
    def slopes(tag, lift):   # half-spaces under the north- and east-falling planes, raised by `lift`
        zN = lambda y: SAC_EAVES + lift + sac_sl * (SAC_Y1 - y)
        zE = lambda x: SAC_EAVES + lift + sac_sl * (SAC_X1 - x)
        # (kept local: far out the falling top would drop below the block's floor and fold it inside-out)
        y0, y1, x0, x1 = SAC_YS - 2, SAC_Y1 + 2, SAC_X0 - 2, SAC_X1 + 2
        hn = prism(f"sac_hn{tag}", [(y0, -5), (y1, -5), (y1, zN(y1)), (y0, zN(y0))], "YZ", x0, x1, M_STONE, tmps)
        he = prism(f"sac_he{tag}", [(x0, -5), (x1, -5), (x1, zE(x1)), (x0, zE(x0))], "XZ", y0, y1, M_STONE, tmps)
        return hn, he
    def plan(g, gy, d, e=0.0):   # footprint; g / gy grow the free east / north sides, d the angled wall, e all hidden sides
        yt = TR_Y - 0.03 - e     # the angled wall starts just inside the transept
        return [(SAC_X0 - e, TOWER_Y1 - 0.2 - e), (X_E - 0.2 + e, TOWER_Y1 - 0.2 - e), (X_E - 0.2 + e, SAC_YS - e),
                (SAC_X1 + g, SAC_YS - e), (SAC_X1 + g, SAC_Y1 + gy), (sac_cx(SAC_Y1 + gy, d), SAC_Y1 + gy),
                (sac_cx(yt, d), yt), (SAC_X0 - e, yt)]
    # walls
    hn, he = slopes("w", 0)
    # hidden sides 5 cm deeper into tower / transept / apse than the roof's, roof 3 cm proud of the angled wall
    walls = prism("sac_walls", plan(0, 0, 0, 0.05), "XY", 0, 14, M_STONE, tmps)
    baked("sacristy", walls, [("INTERSECT", hn), ("INTERSECT", he)], C_PARTS, M_STONE)
    # roof shell: (under planes + ROOF_T, eaves overhang) - (under planes - 0.1, 1 cm wider)
    hn, he = slopes("o", ROOF_T); hn2, he2 = slopes("i", -0.1)
    OVE = SAC_OV + 0.03    # east overhang 3 cm wider: the hip must not end exactly on the corner (degenerate)
    outer_ = prism("sac_ro", plan(OVE, SAC_OV, 0.03), "XY", SAC_EAVES - 2, 16, M_ROOF, tmps)
    # inner block 1 cm larger on EVERY side (on the hidden sides too), so no face of it meets the outer's
    inner_ = prism("sac_ri", plan(OVE + 0.01, SAC_OV + 0.01, 0.04, 0.01), "XY", SAC_EAVES - 3, 16, M_ROOF, tmps)
    inner_b = baked("sac_ri_b", inner_, [("INTERSECT", hn2), ("INTERSECT", he2)], tmps, M_ROOF)
    baked("sacristy_roof", outer_, [("INTERSECT", hn), ("INTERSECT", he), ("DIFFERENCE", inner_b)], C_PARTS, M_ROOF)
    bpy.data.collections.remove(tmps)
    # small rectangular windows (drone frames 019/021/003): two in the north wall, one in the east wall
    rect = lambda u, z0, w, h: [(u - w / 2, z0), (u + w / 2, z0), (u + w / 2, z0 + h), (u - w / 2, z0 + h)]
    fn = wall_frame((0, SAC_Y1, 0), (1, 0, 0), (0, 1, 0))
    fe_ = wall_frame((SAC_X1, 0, 0), (0, 1, 0), (1, 0, 0))
    for i, xw in enumerate((10.4, 12.6)):
        cut_loop(f"sacristy_win_N{i}", fn, rect(xw, 3.8, 0.6, 0.9), 0.3, M_DARK)
    cut_loop("sacristy_win_E", fe_, rect(10.8, 3.8, 0.6, 0.9), 0.3, M_DARK)
    cut_loop("sacristy_win_E_lo", fe_, rect(10.8, 1.4, 0.6, 0.9), 0.3, M_DARK)          # second, lower east window
    for i, xd in enumerate((11.5, 14.6)):                                                 # ground-level doors, north wall
        cut_loop(f"sacristy_door{i}", fn, rect(xd, 0.1, 1.0, 2.1), 0.35, M_DARK)
    # window centred on the angled north-west wall
    p0 = Vector((sac_cx(TR_Y), TR_Y, 0)); p1 = Vector((sac_cx(SAC_Y1), SAC_Y1, 0))
    fd_ = wall_frame(p0, p1 - p0, (-SAC_K, 1, 0))
    cut_loop("sacristy_win_NW", fd_, rect((p1 - p0).length / 2, 3.8, 0.6, 0.9), 0.3, M_DARK)
    # chimney (drone frames 001/003/019): brick-red stack through the north slope toward the east end, with a cap;
    # part of the sacristy roof piece in the colour split (its part below the roof line is cut away there)
    box("sacristy_chimney", 13.7, 14.3, 10.7, 11.3, 5.5, 9.4, M_ROOF)
    box("sacristy_chimney_cap", 13.64, 14.36, 10.64, 11.36, 9.38, 9.5, M_ROOF)
    # 45 deg stone fillets under the north and east eaves (the 35 deg roof underside is too flat to print)
    lo = SAC_EAVES - SAC_OV * sac_sl
    fil = [(SAC_OV - 0.02, lo - 0.05 + 0.02 * sac_sl), (-0.05, SAC_EAVES - 0.05 + 0.05 * sac_sl), (-0.05, lo - 0.1 - SAC_OV - 0.05)]
    prism("sacristy_fillet_N", [(SAC_Y1 + d, z) for d, z in fil], "YZ", sac_cx(SAC_Y1) + 0.1, SAC_X1 + SAC_OV - 0.02)
    prism("sacristy_fillet_E", [(SAC_X1 + d, z) for d, z in fil], "XZ", SAC_YS + 0.02, SAC_Y1 + SAC_OV - 0.02)

# --- apses
apse("apse", X_E, 0.0, APSE_R, APSE_EAVES, APSE_APEX, 45, seams=11)       # 15 arches, 12 deg apart -> 4 deg facets
for s in (-1, 1):
    apse(f"sapse_{s}", X_E, s * SAPSE_Y, SAPSE_R, SAPSE_EAVES, SAPSE_APEX, 40, seams=7)   # 8 arches, 22.5 deg apart -> 4.5 deg facets

# --- towers
def tower(tag, y0, y1):
    x0, x1 = TOWER_X0, X_E
    box(f"tower_{tag}", x0, x1, y0, y1, 0, TOWER_EAVES)
    box(f"tower_{tag}_shaftledge", x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 + 0.06, 0, T_LOWER)   # lower shaft slightly wider
    for z in (T_LOWER, T_UPPER):   # (rope-moulded) string courses
        ledge(f"tower_{tag}_band{z}", x0, x1, y0, y1, 0.14, z - 0.12, z + 0.14)
    ledge(f"tower_{tag}_cornice", x0, x1, y0, y1, 0.16, TOWER_EAVES - 0.45, TOWER_EAVES + 0.02)
    o = 0.4; zb = TOWER_EAVES - 0.25; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sq = lambda q: [(x0 - q, y0 - q), (x1 + q, y0 - q), (x1 + q, y1 + q), (x0 - q, y1 + q)]
    # helm: base ring at the cornice line, then bell-cast rings (eave kick over the last BELL_K), then the apex.
    # Ring heights follow the short (E/W) face's pitch; rings are offset rectangles, so the kick is the same all round.
    # The helm is steep (~71 deg): raising its eave for the kick (as on the red roofs) would add a tall band, so
    # here the eave stays put and the lower part flares out instead (slope 0.6 at the edge, tangent at HK).
    z0 = TOWER_EAVES + 0.12
    s_ = (TOWER_APEX - z0) / ((y1 - y0) / 2 + o)
    HK = 0.8
    rings = [(o - t, z0 + s_ * t - 0.4 * s_ * (t - t * t / (2 * HK))) for t in (0.0, 0.2, 0.4, 0.6, HK)]
    verts = [(x, y, zb) for x, y in sq(0.16)]
    for q, z in rings: verts += [(x, y, z) for x, y in sq(q)]
    verts.append((cx, cy, TOWER_APEX))
    nr, ap = len(rings), 4 * (len(rings) + 1)
    faces = [[3, 2, 1, 0]]
    for k in range(nr):
        a_, b_ = 4 * k, 4 * (k + 1)
        faces += [[a_ + i, a_ + (i + 1) % 4, b_ + (i + 1) % 4, b_ + i] for i in range(4)]
    faces += [[4 * nr + i, 4 * nr + (i + 1) % 4, ap] for i in range(4)]
    obj(f"tower_{tag}_helm", verts, faces, M_COPPER, C_PARTS)
    helm_seams(tag, [(sq(q), z) for q, z in rings], Vector((cx, cy, TOWER_APEX)))
    # finial: ball + cross (thick enough to print at 1:250)
    if FINIALS:
        finial(tag, cx, cy)
    return tower_faces(tag, x0, x1, y0, y1)

def helm_seams(tag, rings, apex, spacing=0.6, w=0.12, h=0.08):
    """Copper standing seams on the helm (photos): on each face, ridges up the fall line (perpendicular to the
    eave) over the bell-cast rings and on up the pyramid face, each stopping just short of the hip edges.
    rings: [(rectangle corners, z)] from the eave inward. Triangular section, like the apse seams."""
    k = 0
    for j in range(4):
        edge = lambda r: (Vector((*r[0][j], r[1])), Vector((*r[0][(j + 1) % 4], r[1])))
        e0, e1 = edge(rings[0]); along = (e1 - e0).normalized(); L0 = (e1 - e0).length
        n = max(1, int(L0 / spacing))
        for i in range(n):
            d = ((i + 0.5) / n - 0.5) * L0                         # offset from the face centre line, kept all the way up
            path = []
            for r in rings:
                a0, a1 = edge(r)
                if abs(d) > (a1 - a0).length / 2 - 0.08: break      # hits the hip before this ring
                path.append((a0 + a1) / 2 + along * d)
            if len(path) == len(rings):                            # reached the top ring: continue up the pyramid face
                a0, a1 = edge(rings[-1]); mid = (a0 + a1) / 2; half = (a1 - a0).length / 2
                vmax = 1 - abs(d) / half - 0.06
                if vmax > 0.05: path.append(mid + along * d + (apex - mid) * vmax)
            if len(path) < 2: continue
            path[0] = path[0] + (path[1] - path[0]) * 0.03         # start just above the eave tip
            secs = []
            for m, p in enumerate(path):
                dirv = (path[m + 1] - p) if m + 1 < len(path) else (p - path[m - 1])
                nrm = along.cross(dirv).normalized()
                if nrm.z < 0: nrm = -nrm
                secs += [p + along * (w / 2) - nrm * 0.02, p - along * (w / 2) - nrm * 0.02, p + nrm * h]
            ns = len(path)
            faces = [[0, 1, 2], [3 * (ns - 1) + 0, 3 * (ns - 1) + 2, 3 * (ns - 1) + 1]]
            for m in range(ns - 1):
                a_, b_ = 3 * m, 3 * (m + 1)
                faces += [[a_ + 0, b_ + 0, b_ + 1, a_ + 1], [a_ + 1, b_ + 1, b_ + 2, a_ + 2], [a_ + 2, b_ + 2, b_ + 0, a_ + 0]]
            obj(f"tower_{tag}_seam{k}", secs, faces, M_COPPER, C_PARTS)
            k += 1

def finial(tag, cx, cy):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.32)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, cy, TOWER_APEX + 0.2))
    me = bpy.data.meshes.new(f"tower_{tag}_ball"); bm.to_mesh(me); bm.free(); me.materials.append(M_GOLD)
    b = bpy.data.objects.new(f"tower_{tag}_ball", me); C_PARTS.objects.link(b)
    t = 0.11
    box(f"tower_{tag}_rod", cx - t, cx + t, cy - t, cy + t, TOWER_APEX - 0.3, TOWER_APEX + 2.0, M_GOLD)
    box(f"tower_{tag}_arm", cx - t, cx + t, cy - 0.5, cy + 0.5, TOWER_APEX + 1.3, TOWER_APEX + 1.52, M_GOLD)

def tower_faces(tag, x0, x1, y0, y1):
    # belfry arcades on all four faces
    faces_def = [  # (origin, u_dir, normal, u_centre, width)
        ((x0, y0, 0), (1, 0, 0), (0, -1, 0), (x1 - x0) / 2, x1 - x0),
        ((x0, y1, 0), (1, 0, 0), (0, 1, 0), (x1 - x0) / 2, x1 - x0),
        ((x0, y0, 0), (0, 1, 0), (-1, 0, 0), (y1 - y0) / 2, y1 - y0),
        ((x1, y0, 0), (0, 1, 0), (1, 0, 0), (y1 - y0) / 2, y1 - y0)]
    for k, (org, u, n, uc, w) in enumerate(faces_def):
        fr = wall_frame(org, u, n)
        # both belfry storeys get identical arcades, each sitting the same 0.3 m below the band above it
        bifora(f"t{tag}_lo{k}", fr, uc, T_LOWER + BELFRY_SILL, w, NH_BELFRY)
        bifora(f"t{tag}_up{k}", fr, uc, T_UPPER + BELFRY_SILL, w, NH_BELFRY)
        # upper storey: rectangular blind field framing the arcade
        # recessed panel: PANEL_W wide, from just above the band to PANEL_M under the cornice, centred
        f0, f1 = T_UPPER + 0.2, TOWER_EAVES - 0.63 - PANEL_M
        cut_loop(f"t{tag}_field{k}", fr, [(uc - PANEL_W / 2, f0), (uc + PANEL_W / 2, f0), (uc + PANEL_W / 2, f1), (uc - PANEL_W / 2, f1)], 0.07)
    return faces_def

tower("S", -TOWER_Y1, -TOWER_Y0)
tower("N", TOWER_Y0, TOWER_Y1)
# clock face (south tower, south face only: the one the photos show), raised disc
for org, u, n, uc in [((TOWER_X0, -TOWER_Y1, 0), (1, 0, 0), (0, -1, 0), (X_E - TOWER_X0) / 2)]:
    fr = wall_frame(org, u, n)
    lp = circle_loop(uc, CLOCK_Z, 0.95)
    lb = circle_loop(uc, CLOCK_Z, 0.95 + 0.24)  # bevelled rim: 45 deg underside
    extrude("clock", [fr(a, b, -0.1) for a, b in lb], [fr(a, b, 0.14) for a, b in lp], M_GOLD, C_PARTS)

# (lion corbels at the gable feet omitted: carved sculpture, reads as stray blocks when boxed)

# --- west facade: portal, band + pilasters, gable decoration
fw = wall_frame((X_W, 0, 0), (0, 1, 0), (-1, 0, 0))
# West portal (refs/photos/MI_Portal_818.jpg, straight-on; scaled so the outer arch crown = 5.8 m):
# twice-stepped jambs with two 3/4 columns per side, capitals + carved impost band running out past the
# jambs, the columns continuing as roll mouldings round the arch, a sawtooth (dentil) outer archivolt,
# tympanum with Christ relief over the lintel, stone platform step in front.
P = PORTAL_Y
SPRING = 3.45                         # centre of the archivolts (top of impost band)
STEPS = [(1.85, 0.25, 0.16), (1.45, 0.50, 0.13), (1.06, 0.75, 0.10)]   # (half width, depth, sill)
for k, (hw, dp, sl) in enumerate(STEPS):
    cut_loop(f"portal_step{k}", fw, arch_loop(P, sl, 2 * hw, SPRING + hw - sl), dp)
cut_loop("portal_door", fw, [(P - 0.85, 0.07), (P + 0.85, 0.07), (P + 0.85, 3.17), (P - 0.85, 3.17)], 1.0, M_DARK)
# sawtooth archivolt: semicircular groove in the wall face, re-filled with radial dentils (below)
R0, R1 = 2.12, 2.32   # sawtooth band ~0.2 m wide (photo)
groove = [(P + R1 * math.cos(math.pi * i / 32), SPRING + R1 * math.sin(math.pi * i / 32)) for i in range(33)] + \
         [(P + R0 * math.cos(math.pi * i / 32), SPRING + R0 * math.sin(math.pi * i / 32)) for i in range(32, -1, -1)]
cut_loop("portal_groove", fw, groove, 0.12)

def solid_un(name, frame, loop_un, z0, z1, m=M_STONE, coll=None):
    """Vertical prism from a plan loop given in wall coords (u along wall, n out of wall)."""
    return extrude(name, [frame(u, z0, n) for u, n in loop_un], [frame(u, z1, n) for u, n in loop_un], m, coll or C_ADD)

def half_torus(name, frame, uc, vc, nc, R, r, m=M_STONE, coll=None, ns=32, ms=10, ext=0.06):
    """Roll moulding: tube of radius r swept over a semicircle of radius R (in the wall plane at depth nc)."""
    verts, faces = [], []
    for i in range(ns + 1):
        t = -ext + (math.pi + 2 * ext) * i / ns   # ends dip into the impost, no coplanar caps
        for j in range(ms):
            ph = 2 * math.pi * j / ms
            rr = R + r * math.cos(ph)
            verts.append(frame(uc + rr * math.cos(t), vc + rr * math.sin(t), nc + r * math.sin(ph)))
    for i in range(ns):
        for j in range(ms):
            a, b = i * ms + j, i * ms + (j + 1) % ms
            faces.append([a, b, b + ms, a + ms])
    faces += [list(range(ms))[::-1], list(range(ns * ms, ns * ms + ms))]
    return obj(name, verts, faces, m, coll or C_ADD)

CR = 0.13                             # column radius
CS = 0.19                             # capital top half-width
cols = [(1.85 - 0.6 * CR, -0.25 + 0.6 * CR), (1.45 - 0.6 * CR, -0.50 + 0.6 * CR)]   # sunk so the step corner is inside the column (no tangency, no trapped void)
for side in (-1, 1):
    for k, (cu, cn) in enumerate(cols):
        u = P + side * cu
        solid_un(f"portal_col{side}{k}", fw, circle_loop(u, cn, CR), 0.05, 2.92)                     # shaft
        solid_un(f"portal_base{side}{k}", fw, circle_loop(u, cn, CR + 0.06), 0.05, 0.4)             # attic base
        solid_un(f"portal_plinth{side}{k}", fw, [(u - 0.2, cn - 0.2), (u + 0.2, cn - 0.2), (u + 0.2, cn + 0.2), (u - 0.2, cn + 0.2)], 0.05, 0.22)
        # capital: flares from the round shaft to a square top (steeper than 45 deg) right under the impost
        circ = circle_loop(u, cn, CR, 16)
        sqr = [(u + max(-1, min(1, 1.5 * math.cos(2 * math.pi * i / 16))) * CS, cn + max(-1, min(1, 1.5 * math.sin(2 * math.pi * i / 16))) * CS) for i in range(16)]
        extrude(f"portal_cap{side}{k}", [fw(a, 2.86, b) for a, b in circ], [fw(a, 3.14, b) for a, b in sqr], M_STONE, C_ADD)   # not 3.15 (lintel bottom)
        # impost wraps round the capital: projecting block over it, 45 deg underside
        sq = lambda q, z: [fw(u - q, z, cn - q), fw(u + q, z, cn - q), fw(u + q, z, cn + q), fw(u - q, z, cn + q)]
        extrude(f"portal_imp_cap{side}{k}", sq(CS + 0.05, 3.135 + 0.004 * k), sq(CS + 0.05, SPRING + 0.015 - 0.004 * k), M_STONE, C_ADD)  # 6 cm lip: fine unsupported
for k, (cu, cn) in enumerate(cols):
    half_torus(f"portal_roll{k}", fw, P, SPRING, cn, cu, CR)
# impost band: follows the stepped jambs 6 cm proud, runs out 0.7 m past them onto the wall face
def impost_outline(o, u0=0.9, u1=2.58):
    return [(u1, o), (1.85 - o, o), (1.85 - o, -0.25 + o), (1.45 - o, -0.25 + o), (1.45 - o, -0.50 + o),
            (1.06 - o, -0.50 + o), (1.06 - o, -0.75 + o), (u0, -0.75 + o), (u0, -1.3), (u1, -1.3)]
for side in (-1, 1):
    top = [(P + side * a, b) for a, b in impost_outline(0.06)]
    ctop, cbot = ([(P + side * a, b) for a, b in impost_outline(q, 0.92, 2.56)] for q in (0.06, -0.02))  # ends inset: no shared end planes
    if side < 0: top, ctop, cbot = top[::-1], ctop[::-1], cbot[::-1]
    solid_un(f"portal_impost{side}", fw, top, 3.13, SPRING + 0.02)   # not 3.15 = lintel bottom
    extrude(f"portal_impost_chamfer{side}", [fw(a, 3.09, b) for a, b in cbot], [fw(a, 3.17, b) for a, b in ctop], M_STONE, C_ADD)
# sawtooth band in the groove (photo): a continuous row of radial wedges, ridge at the wall face.
# Each wedge overlaps its neighbours slightly so the union has no shared faces.
nd, eps = 36, 0.004
for i in range(nd):
    t0, t1, tm = math.pi * i / nd - eps, math.pi * (i + 1) / nd + eps, math.pi * (i + 0.5) / nd
    pt = lambda rr, t, n: fw(P + rr * math.cos(t), SPRING + rr * math.sin(t), n)
    a_, b_, c_, d_ = pt(R0 - 0.02, t0, -0.14), pt(R1 + 0.02, t0, -0.14), pt(R1 + 0.02, t1, -0.14), pt(R0 - 0.02, t1, -0.14)
    e_, f_ = pt(R0 - 0.02, tm, -0.01), pt(R1 + 0.02, tm, -0.01)
    obj(f"portal_tooth{i}", [a_, b_, c_, d_, e_, f_], [[0, 1, 2, 3], [0, 4, 5, 1], [3, 2, 5, 4], [0, 3, 4], [1, 5, 2]], M_STONE, C_ADD)
# lintel + tympanum relief (Christ, bust in low relief) on the tympanum plane n=-0.75
solid_un("portal_lintel", fw, [(P - 1.1, -0.8), (P + 1.1, -0.8), (P + 1.1, -0.68), (P - 1.1, -0.68)], 3.15, 3.4)
tn = -0.75
torso = [(P - 0.42, 3.4), (P + 0.42, 3.4), (P + 0.3, 3.85), (P + 0.14, 3.95), (P - 0.14, 3.95), (P - 0.3, 3.85)]
extrude("portal_christ_body", [fw(a, b, tn - 0.02) for a, b in torso], [fw(a, b, tn + 0.07) for a, b in torso], M_STONE, C_ADD)
hl = circle_loop(P, 4.12, 0.15)
extrude("portal_christ_head", [fw(a, b, tn - 0.02) for a, b in hl], [fw(a, b, tn + 0.09) for a, b in hl], M_STONE, C_ADD)
nl = circle_loop(P, 4.12, 0.26)
extrude("portal_christ_nimbus", [fw(a, b, tn - 0.02) for a, b in nl], [fw(a, b, tn + 0.03) for a, b in nl], M_STONE, C_ADD)
# platform step in front of the portal
box("portal_platform", X_W - 1.3, X_W + 0.05, P - 3.0, P + 3.0, -0.79, 0.145, M_STONE, C_ADD)  # to plinth bottom (1 cm up: avoids coplanar boolean faces)
# Gable field (photo): between plain corner strips, from the ledge at ~10.1 m up to the rising arch line,
# the wall is sunk 0.12 m; the arches are the field's upper edge, the wall above stays flush with the facade.
# Tapered cut: floor and arch ceilings slope 45 deg (no flat overhangs).
WF_D, WF_EDGE = 0.12, NAVE_HW - 0.6
wl, ws = arch_line(5, 0.62, 0.5, 0.55, 17.95, 0.9)
taper_cut("west_field", fw, [(-WF_EDGE, 10.1), (WF_EDGE, 10.1), (WF_EDGE, ws[-1])] + wl + [(-WF_EDGE, ws[-1])], WF_D, 0.3)
cut_loop("west_cross", fw, cross_loop(0, 16.35, 1.1, 0.38), 0.6, M_DARK)
for s in (-1, 1):
    cut_loop(f"west_oculus{s}", fw, circle_loop(s * 1.2, 15.3, 0.42), 0.6, M_DARK)
    cut_loop(f"west_oculus_ring{s}", fw, circle_loop(s * 1.2, 15.3, 0.58), WF_D + 0.07)   # ring recessed into the sunken field
cut_loop("west_oculus_top", fw, circle_loop(0, 19.3, 0.32), 0.6, M_DARK)

# --- nave clerestory + aisle windows (6 bays)
for s in (-1, 1):
    fc = wall_frame((0, s * NAVE_HW, 0), (1, 0, 0), (0, s, 0))
    fa = wall_frame((0, s * AISLE_Y, 0), (1, 0, 0), (0, s, 0))
    if s > 0:   # north aisle only: round-arched side door near the west end, by the portal (photos: asymmetric)
        cut_loop("aisle_N_door", fa, arch_loop(X_W + 1.85, 0.1, 1.2, 2.5), 0.5, M_DARK)
    for i, (xc, xa) in enumerate(zip(CLERE_X, AISLE_X)):
        window(f"clere{s}_{i}", fc, xc, 11.6, 0.72, 2.0, niche=(1.3, 2.75, 11.2))
        window(f"aisle{s}_{i}", fa, xa, 4.25, 0.6, 1.65, niche=(1.1, 2.3, 3.95))

# --- side-choir bays + tower outer faces (MI_883.jpg, drone frames 050-053): an arched, splayed window in each bay's
# outer wall under its lean-to roof; on each tower's outer face an arched ground-level window and two slits above.
# With the sacristy, the north bay wall and tower foot are inside it: there only the upper slit (south mirrored
# to the north otherwise: it faces the cloister, no photo shows it).
for s in (-1, 1):
    fb = wall_frame((0, s * TOWER_Y1, 0), (1, 0, 0), (0, s, 0))
    if s > 0 and SACRISTY:
        z = 16.6
        cut_loop(f"tower{s}_slit{z}", fb, [((TOWER_X0 + X_E) / 2 - 0.12, z - 0.35), ((TOWER_X0 + X_E) / 2 + 0.12, z - 0.35),
                                           ((TOWER_X0 + X_E) / 2 + 0.12, z + 0.35), ((TOWER_X0 + X_E) / 2 - 0.12, z + 0.35)], 0.35, M_DARK)
        continue
    window(f"bay{s}_win", fb, (X_TE + TOWER_X0) / 2, 4.6, 0.5, 1.4, niche=(0.9, 1.9, 4.35))
    window(f"tower{s}_groundwin", fb, (TOWER_X0 + X_E) / 2, 4.6, 0.5, 1.4, niche=(0.9, 1.9, 4.35))   # ground-level arched window (frame 050)
    for z in (16.6, 9.8):
        cut_loop(f"tower{s}_slit{z}", fb, [((TOWER_X0 + X_E) / 2 - 0.12, z - 0.35), ((TOWER_X0 + X_E) / 2 + 0.12, z - 0.35),
                                           ((TOWER_X0 + X_E) / 2 + 0.12, z + 0.35), ((TOWER_X0 + X_E) / 2 - 0.12, z + 0.35)], 0.35, M_DARK)

# --- transept gable ends: 2+2 windows, cross, oculus; south transept west door
for s in (-1, 1):
    ft = wall_frame((0, s * TR_Y, 0), (1, 0, 0), (0, s, 0))
    for du in (-1.9, 1.9):
        window(f"tr{s}_lo{du}", ft, X_TC + du, 3.9, 0.8, 2.5, niche=(1.35, 3.05, 3.6))
        window(f"tr{s}_up{du}", ft, X_TC + du, 10.0, 0.8, 2.5, niche=(1.35, 3.05, 9.7))
    if s < 0:   # south gable: cross-shaped opening; north gable: a plain rectangular one (photos: asymmetric)
        cut_loop(f"tr{s}_cross", ft, cross_loop(X_TC, 16.4, 0.9, 0.28), 0.5, M_DARK)
    else:
        cut_loop(f"tr{s}_slot", ft, [(X_TC - 0.4, 15.65), (X_TC + 0.4, 15.65), (X_TC + 0.4, 17.15), (X_TC - 0.4, 17.15)], 0.5, M_DARK)   # ~0.8 x 1.5 m (frame 003)
    cut_loop(f"tr{s}_oculus", ft, circle_loop(X_TC, 19.0, 0.3), 0.5, M_DARK)
fd = wall_frame((X_TW, 0, 0), (0, 1, 0), (-1, 0, 0))
cut_loop("south_door", fd, arch_loop(-10.3, 0.1, 1.4, 2.8), 0.6, M_DARK)

# --- choir east gable (above main apse): oculus + rising arch frieze
fe = wall_frame((X_E, 0, 0), (0, -1, 0), (1, 0, 0))
cut_loop("east_oculus", fe, circle_loop(0, 18.6, 0.3), 0.5, M_DARK)
# rising arch frieze: shallower than the rake, its top arch sitting just above the apse cone tip (photo)
# Same treatment as the west gable: the field under the arch line is sunk WF_D, wall above + corner strips flush.
# The field's lower edge follows the apse cone (5 cm above where it meets the wall), so the cut never touches it.
E_SLOPE, E_H, E_PITCH = 0.8, 0.5, 0.55
el, es = arch_line(5, E_PITCH, 0.42, E_H, APSE_APEX + 0.25 + E_H + E_PITCH / 2 * E_SLOPE, E_SLOPE)
cone_k = (APSE_APEX - (APSE_EAVES - 0.02)) / (APSE_R + 0.3)       # cone drop per metre along the wall
u_c = (APSE_APEX + 0.05 - EAVES) / cone_k                         # where the cone line crosses the eave level
taper_cut("east_field", fe, [(-WF_EDGE, EAVES), (-u_c, EAVES), (0, APSE_APEX + 0.05), (u_c, EAVES), (WF_EDGE, EAVES), (WF_EDGE, es[-1])]
          + el + [(-WF_EDGE, es[-1])], WF_D, 0.3)

# --- apse windows + arch friezes under the cornice
def apse_details(tag, cy, r, ze, wins, glass, niche, fw_, fh):
    for ang in wins:
        a = math.radians(ang)
        c = Vector((X_E + r * math.cos(a), cy + r * math.sin(a), 0))
        fr = wall_frame(c, (-math.sin(a), math.cos(a), 0), (math.cos(a), math.sin(a), 0))
        window(f"{tag}_win{ang}", fr, 0, glass[0], glass[1], glass[2], niche=niche, depth=0.55)
    zb = ze - 1.0 - fh    # arch frieze low enough to leave room for the sawtooth band under the cornice
    def ring(rr, z): return [(x, y, z) for x, y in arc_pts(X_E, cy, rr, -math.pi / 2, math.pi / 2, SEG * 2) + [(X_E - 0.6, cy + rr), (X_E - 0.6, cy - rr)]]
    extrude(f"{tag}_corbelchamfer", ring(r - 0.03, zb), ring(r + 0.12, zb + 0.15), M_STONE, C_PARTS)  # 45 deg underside
    extrude(f"{tag}_corbelband", ring(r + 0.12, zb + 0.15), ring(r + 0.12, ze - 0.3), M_STONE, C_PARTS)
    n = int(math.pi * r / (fw_ + 0.2))
    for i in range(n):
        a = -math.pi / 2 + math.pi * (i + 0.5) / n
        c = Vector((X_E + r * math.cos(a), cy + r * math.sin(a), 0))
        fr = wall_frame(c, (-math.sin(a), math.cos(a), 0), (math.cos(a), math.sin(a), 0))
        taper_cut(f"{tag}_fr{i}", fr, arch_loop(0, zb + 0.01, fw_, fh - 0.01), 0.01, 0.15)
    # sawtooth band (photos): triangular notches cut into the band face leave a row of wedge teeth;
    # notch ceilings rise 45 deg outward so nothing overhangs flat
    za, zt = ze - 0.82, ze - 0.58
    nt = min((SEG, SEG * 2), key=lambda q: abs(q - 2 * n))   # ~two teeth per frieze arch (photo), locked to the ring facets
    at = lambda ang, rad, z: (X_E + rad * math.cos(ang), cy + rad * math.sin(ang), z)
    for i in range(nt):
        a = -math.pi / 2 + math.pi * (i + 0.5) / nt; h_ = 0.97 * math.pi / nt / 2   # neighbours must not share an edge
        ro, ri = r + 0.15, r - 0.01
        vs = [at(a - h_, ro, za), at(a + h_, ro, za), at(a, ri, za), at(a - h_, ro, zt + ro - ri), at(a + h_, ro, zt + ro - ri), at(a, ri, zt)]
        obj(f"{tag}_saw{i}", vs, [[0, 1, 2], [3, 5, 4], [0, 3, 4, 1], [1, 4, 5, 2], [2, 5, 3, 0]], M_STONE, C_CUTS)

apse_details("apse", 0, APSE_R, APSE_EAVES, (-55, 0, 55), (5.65, 1.05, 3.2), (1.75, 4.0, 5.4), 0.62, 0.75)
for s in (-1, 1):
    dz = 0.5   # window moves up with the taller apse (not the full 0.85: its splay must stay clear of the frieze)
    apse_details(f"sapse{s}", s * SAPSE_Y, SAPSE_R, SAPSE_EAVES, (0,), (3.6 + dz, 0.5, 1.5), (1.05, 2.1, 3.4 + dz), 0.48, 0.55)

# --- printable plinth
if BASE:
    if SACRISTY:   # plinth under the sacristy too (it reaches beyond the church's)
        prism("base_sacristy", plan(0.8, 0.8, 0.8), "XY", -0.8, 0.02)   # follows the footprint, angled wall too
    for n_, (a, b, c, d) in {"nave": (X_W, X_TW, -AISLE_Y, AISLE_Y), "tr": (X_TW, X_TE, -TR_Y, TR_Y),
                             "east": (X_TE, X_E, -TOWER_Y1, TOWER_Y1)}.items():
        box(f"base_{n_}", a - 0.8, b + 0.8, c - 0.8, d + 0.8, -0.8, 0.02)
    for cy, r in ((0, APSE_R), (SAPSE_Y, SAPSE_R), (-SAPSE_Y, SAPSE_R)):
        prism(f"base_apse{cy}", arc_pts(X_E, cy, r + 0.8, -math.pi / 2, math.pi / 2, SEG * 2) +
              [(X_E - 1, cy + r + 0.8), (X_E - 1, cy - r - 0.8)], "XY", -0.8, 0.02)

# ---------------------------------------------------------------- combine: union parts, subtract cutters
parts = list(C_PARTS.objects)
me = bpy.data.meshes.new("KlosterkircheBiburg")
church = bpy.data.objects.new("KlosterkircheBiburg", me); root.objects.link(church)
for m in (M_STONE, M_ROOF, M_COPPER, M_DARK, M_GOLD): me.materials.append(m)
# seed with first part's geometry so the union has a base
church.data = parts[0].data.copy()
for m in (M_ROOF, M_COPPER, M_DARK, M_GOLD): church.data.materials.append(m)
u = church.modifiers.new("union", "BOOLEAN"); u.operation = "UNION"; u.operand_type = "COLLECTION"; u.collection = C_PARTS; u.solver = "EXACT"
d = church.modifiers.new("cut", "BOOLEAN"); d.operation = "DIFFERENCE"; d.operand_type = "COLLECTION"; d.collection = C_CUTS; d.solver = "EXACT"
a_ = church.modifiers.new("details", "BOOLEAN"); a_.operation = "UNION"; a_.operand_type = "COLLECTION"; a_.collection = C_ADD; a_.solver = "EXACT"
for m_ in (u, d, a_): m_.use_hole_tolerant = True  # exact solver is fragile with the many near-coincident cutters
for c in (C_PARTS, C_CUTS, C_ADD):
    c.hide_viewport = True; c.hide_render = True
result = {"parts": len(parts), "cutters": len(C_CUTS.objects)}
