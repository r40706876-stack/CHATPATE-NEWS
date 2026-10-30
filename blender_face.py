"""Blender: एक photo से चेहरे के भाव (30 Oct, मालिक: "Blender से realistic सब emotion").
photo एक बारीक mesh पर (हर ~5 pixel पर vertex), हर भाव एक shape key — face_rig.HANDLES के हिसाब से भौंह/पलक/
होंठ के कोने/गाल के vertex खिसकते हैं; camera सीधा (orthographic), रोशनी नहीं (emission) — इसलिए photo की असली
बनावट जैसी की तैसी रहती है, सिर्फ़ भाव बदलता है.

    blender -b -P blender_face.py -- assets/real/ramesh.png assets/real/ramesh
      → assets/real/ramesh_{hasi,hairan,gussa,udaas,tanz}.png
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face_rig  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
STEP = 5

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
img = bpy.data.images.load(SRC)
W, H = img.size

# mesh: (x, y) pixel → (x/100, -y/100)
nx, ny = W // STEP + 1, H // STEP + 1
verts, faces, uvs = [], [], []
for j in range(ny):
    for i in range(nx):
        x, y = min(i * STEP, W), min(j * STEP, H)
        verts.append((x / 100, -y / 100, 0))
for j in range(ny - 1):
    for i in range(nx - 1):
        a = j * nx + i
        faces.append((a, a + 1, a + nx + 1, a + nx))
me = bpy.data.meshes.new("photo")
me.from_pydata(verts, [], faces)
uv = me.uv_layers.new(name="UV")
for poly in me.polygons:
    for li in poly.loop_indices:
        vx, vy, _ = verts[me.loops[li].vertex_index]
        uv.data[li].uv = (vx * 100 / W, 1 - (-vy * 100) / H)
ob = bpy.data.objects.new("photo", me)
sc.collection.objects.link(ob)

mat = bpy.data.materials.new("photo")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = "Cubic"
tex.extension = "EXTEND"
em = nt.nodes.new("ShaderNodeEmission")
outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tex.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs["Emission"], outn.inputs["Surface"])
me.materials.append(mat)

ob.shape_key_add(name="Basis")
for expr in face_rig.HANDLES:
    sk = ob.shape_key_add(name=expr)
    for k, (vx, vy, _) in enumerate(verts):
        dx, dy = face_rig.disp(expr, vx * 100, -vy * 100)
        if dx or dy:
            sk.data[k].co = (vx + dx / 100, vy - dy / 100, 0)

cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cam_d.ortho_scale = max(W, H) / 100
cam = bpy.data.objects.new("cam", cam_d)
cam.location = (W / 200, -H / 200, 10)
sc.collection.objects.link(cam)
sc.camera = cam

sc.render.engine = "CYCLES"
sc.cycles.samples = 16
sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.render.image_settings.file_format = "PNG"
w = bpy.data.worlds.new("w")
w.color = (0, 0, 0)
sc.world = w

for expr in face_rig.HANDLES:
    for kb in ob.data.shape_keys.key_blocks[1:]:
        kb.value = 1.0 if kb.name == expr else 0.0
    sc.render.filepath = f"{OUT}_{expr}.png"
    bpy.ops.render.render(write_still=True)
    print("rendered", expr, sc.render.filepath)
