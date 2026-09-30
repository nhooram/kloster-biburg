# Render comparison views of the church. Set VIEWS / OUT before exec, or use defaults.
import bpy, math, os
from mathutils import Vector

OUT = globals().get("OUT", "/home/hooram/code/cad-work/kloster-biburg/renders")
os.makedirs(OUT, exist_ok=True)
# name: (camera location, look-at target, lens mm)
VIEWS = globals().get("VIEWS", {
    "sw_photo2020": ((-48, -38, 2.0), (-8, 0, 14), 35),     # like 2020_St_Maria_Biburg.jpg
    "south": ((0, -75, 12), (0, 0, 14), 40),
    "west_level": ((-150, 0, 23), (0, 0, 20), 120),          # like winter drone frame w_21
    "east_apse": ((50, 18, 6), (14, 0, 12), 35),
    "se_high": ((55, -55, 45), (0, 0, 10), 35),
    "nw_high": ((-50, 45, 40), (0, 0, 10), 35),
    "top": ((0, 0, 140), (0, 0, 0), 50),
})
sc = bpy.context.scene
ch = bpy.data.objects["KlosterkircheBiburg"]
dg = bpy.context.evaluated_depsgraph_get()
ev = ch.evaluated_get(dg).data
stats = {"verts": len(ev.vertices), "faces": len(ev.polygons)}

sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.cavity_type = "BOTH"
sh.show_shadows = True; sh.show_object_outline = False
sc.display.shadow_focus = 0.2
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
sc.render.film_transparent = False
if sc.world is None: sc.world = bpy.data.worlds.new("World")
cam = bpy.data.objects.get("RenderCam") or bpy.data.objects.new("RenderCam", bpy.data.cameras.new("RenderCam"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam
cam.data.clip_end = 2000
for name, (loc, tgt, lens) in VIEWS.items():
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
result = {"stats": stats, "out": OUT, "views": list(VIEWS)}
