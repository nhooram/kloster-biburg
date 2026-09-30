# Report where non-manifold edges of the evaluated church are (clustered), to debug booleans.
import bpy, bmesh
src = bpy.data.objects["KlosterkircheBiburg"]
me = bpy.data.meshes.new_from_object(src.evaluated_get(bpy.context.evaluated_depsgraph_get()))
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
pts = [tuple(round(c, 0) for c in (e.verts[0].co + e.verts[1].co) / 2) for e in bm.edges if not e.is_manifold]
from collections import Counter
result = {"n": len(pts), "clusters": Counter(pts).most_common(25)}
bm.free(); bpy.data.meshes.remove(me)
