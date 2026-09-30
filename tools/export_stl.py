# Bake booleans into a copy, check it is watertight, export STL in mm at SCALE (1:SCALE). Set SCALE / OUTDIR before exec.
import bpy, bmesh, os, struct
SCALE = globals().get("SCALE", 250)  # SUFFIX="" optional variant tag in the file name
OUTDIR = globals().get("OUTDIR", "/home/hooram/code/cad-work/kloster-biburg/export")
src = bpy.data.objects["KlosterkircheBiburg"]
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(src.evaluated_get(dg))
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bmesh.ops.triangulate(bm, faces=bm.faces)
non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
bm.to_mesh(me)
vol = bm.calc_volume(signed=True); ntri = len(bm.faces)
bm.free()
name = f"KlosterkircheBiburg_1-{SCALE}" + globals().get("SUFFIX", "")
os.makedirs(OUTDIR, exist_ok=True)
path = os.path.join(OUTDIR, name + ".stl")
k = 1000.0 / SCALE  # metres -> mm at 1:SCALE
me.calc_loop_triangles()
with open(path, "wb") as fh:  # ponytail: plain binary STL writer; bpy's exporter skips unselectable temp objects
    tris = me.loop_triangles
    fh.write(name.encode().ljust(80, b" ") + struct.pack("<I", len(tris)))
    for t in tris:
        fh.write(struct.pack("<3f", *t.normal))
        for vi in t.vertices: fh.write(struct.pack("<3f", *(me.vertices[vi].co * k)))
        fh.write(b"\0\0")
bpy.data.meshes.remove(me)
dims = [round(d * 1000 / SCALE, 1) for d in src.dimensions]
result = {"stl": path, "non_manifold_edges": non_manifold, "volume_m3": round(vol, 1), "tris": ntri, "size_mm": dims}
