# Exploded preview of the colour split (Biburg_split collection from split_parts.py).
import bpy
from mathutils import Vector
sc = bpy.context.scene
split = bpy.data.collections["Biburg_split"]; master = bpy.data.objects["KlosterkircheBiburg"]
lift = {"roof_main": 14, "roof_aisle": 7, "roof_sidechoir": 10, "roof_sacristy": 7, "helm": 12, "apse": 6}
split.hide_viewport = split.hide_render = False; master.hide_render = True
for o in split.objects:
    o.location = (0, 0, next((v for k, v in lift.items() if o.name.startswith(k)), 0))
cam = bpy.data.objects["RenderCam"]; sc.camera = cam
loc, tgt = (Vector(v) for v in globals().get("CAM", ((-58, -62, 52), (-2, 0, 14))))
cam.location = loc; cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = globals().get("LENS", 28)
sc.render.filepath = globals().get("OUTPNG", "/home/hooram/code/cad-work/kloster-biburg/renders/split_exploded.png")
bpy.ops.render.render(write_still=True)
for o in split.objects: o.location = (0, 0, 0)
split.hide_viewport = split.hide_render = True; master.hide_render = False
result = {"ok": sc.render.filepath}
