"""Blender (एक बार चलता है, GitHub Actions पर): किरदार बदलने पर 0.48 सेकंड का 3D "बकरा न्यूज़" झटका (transition).
पारदर्शी PNG frames → assets/fx/wipe/0001.png… — reel_studio इन्हें हर बार video के ऊपर चिपकाता है (रोज़ Blender नहीं चलता).

चलाना: blender -b -P blender_fx.py
क्यों ऐसे: free GitHub runner पर हर reel के 900 frames Blender में बनाने में घंटों लगते; ये 12 frames एक बार बनते हैं.
Hindi अक्षर Blender ठीक नहीं जोड़ता (मात्राएँ टूटती हैं) — इसलिए label PIL से बनी तस्वीर (assets/fx/wipe_label.png) है.
"""
import math
import os

import bpy

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "fx", "wipe")
FRAMES = 12                      # 25 fps पर 0.48 सेकंड
RED, YEL = (0.85, 0.06, 0.09, 1), (1.0, 0.62, 0.0, 1)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 32
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.film_transparent = True
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.6
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.fps = 25
sc.view_settings.view_transform = "Standard"

cam_data = bpy.data.cameras.new("cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 16                               # ऊँचाई 16 इकाई, चौड़ाई 9
cam = bpy.data.objects.new("cam", cam_data)
cam.location = (0, 0, 20)
sc.collection.objects.link(cam)
sc.camera = cam

world = bpy.data.worlds.new("w")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.06, 0.1, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
sc.world = world

for loc, energy, size in (((-6, 6, 12), 2500, 8), ((7, -4, 10), 900, 6)):
    ld = bpy.data.lights.new("l", "AREA")
    ld.energy, ld.size = energy, size
    lo = bpy.data.objects.new("l", ld)
    lo.location = loc
    lo.rotation_euler = (math.radians(-20 if loc[1] > 0 else 20), math.radians(25 if loc[0] < 0 else -25), 0)
    sc.collection.objects.link(lo)


def mat(name, color, image=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Metallic"].default_value = 0.35
    bsdf.inputs["Roughness"].default_value = 0.22
    bsdf.inputs["Coat Weight"].default_value = 0.6
    if image:
        tex = m.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image)
        m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Metallic"].default_value = 0.1
    else:
        bsdf.inputs["Base Color"].default_value = color
    return m


def bar(name, w, h, y, color, delay, image=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = (w, h, 0.5)
    bev = o.modifiers.new("b", "BEVEL")
    bev.width, bev.segments = 0.12, 4
    o.data.materials.append(mat(name, color))
    o.rotation_euler = (0, 0, math.radians(-14))
    if image:                                             # label की पट्टी (PIL वाली Hindi तस्वीर) सामने वाले हिस्से पर
        bpy.ops.mesh.primitive_plane_add(size=1)
        p = bpy.context.active_object
        p.scale = (h * 0.92 * 2400 / 360 / w, 0.92, 1)  # label का अनुपात बना रहे
        p.location = (0, 0, 0.51)
        p.parent = o
        p.data.materials.append(mat(name + "_lbl", color, image))
    # बाएँ से दाएँ, तेज़ शुरुआत → बीच में धीमा → तेज़ निकलना (TV stinger जैसा)
    for f, x in ((1 + delay, -24), (5 + delay, -1.5), (8 + delay, 1.5), (FRAMES + delay, 24)):
        o.location = (x, y, 0)
        o.keyframe_insert("location", frame=f)
    return o


bar("red", 34, 3.2, 1.2, RED, 0)
bar("yel", 34, 2.3, -1.5, YEL, 1, os.path.join(ROOT, "assets", "fx", "wipe_label.png"))
bar("red2", 34, 0.5, 3.6, RED, 2)

os.makedirs(OUT, exist_ok=True)
sc.render.filepath = os.path.join(OUT, "")
bpy.ops.render.render(animation=True)
print("wipe frames:", sorted(os.listdir(OUT)))
