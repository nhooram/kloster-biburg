# Render from a solved photo camera (analysis/*.json) for overlay comparison. Set CAMJSON, OUTPNG.
import bpy, json
from mathutils import Matrix, Vector
c = json.load(open(CAMJSON))
sc = bpy.context.scene
cam = bpy.data.objects.get("MatchCam") or bpy.data.objects.new("MatchCam", bpy.data.cameras.new("MatchCam"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
W, H = c["W"], c["H"]
cam.data.sensor_fit = "HORIZONTAL"; cam.data.sensor_width = 36.0
cam.data.lens = c["f"] * 36.0 / W
cam.data.shift_x = -(c["cx"] - W / 2) / W
cam.data.shift_y = (c["cy"] - H / 2) / W
cam.data.clip_end = 2000
cam.matrix_world = Matrix.Translation(Vector(c["C"])) @ Matrix(c["R"]).to_4x4()
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = True
sc.render.filepath = OUTPNG
bpy.ops.render.render(write_still=True)
sc.render.film_transparent = False
result = {"ok": OUTPNG}
