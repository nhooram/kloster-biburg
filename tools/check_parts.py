# List boolean operands that are not closed manifolds or have inward/zero volume.
import bpy, bmesh
bad = []
for cname in ("Biburg_parts", "Biburg_cutters"):
    for o in bpy.data.collections[cname].objects:
        bm = bmesh.new(); bm.from_mesh(o.data)
        nm = sum(1 for e in bm.edges if not e.is_manifold); v = bm.calc_volume(signed=True)
        if nm or v <= 1e-6: bad.append((o.name, nm, round(v, 4)))
        bm.free()
result = {"bad": bad}
