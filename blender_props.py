"""Blender: पैसे वाली खबरों के लिए अपने 3D clips (एक बार बनते हैं, हर reel में दोबारा काम आते हैं).
  coins  — सिक्के खनखनाते हुए काउंटर पर गिरते (छुट्टा, पैसे, खुल्ले)
  toffee — छुट्टे की जगह टॉफी घूमती हुई काउंटर पर आती
  notes  — नोटों की गड्डी ऊपर तक चढ़ती (लाख, करोड़, बीमा, कमाई)
चलाना: blender -b -P blender_props.py -- coins     → assets/fx/props/coins.mp4 (1056x810, 4 सेकंड)
stock फ़ोटो एक जैसी ("same same") लगती थीं; ये हमारी अपनी हैं, हर बार नई हरकत, और बात से सीधे जुड़ी.
"""
import math
import os
import random
import sys

import bpy

ROOT = os.path.dirname(os.path.abspath(__file__))
WHICH = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "coins"
FPS, SECS = 25, 4
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 12                                  # denoise के साथ काफ़ी; 24 पर 60 मिनट की सीमा पार हुई
sc.cycles.max_bounces = 4
sc.cycles.use_adaptive_sampling = True
sc.render.use_persistent_data = True
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1056, 810
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, FPS * SECS
sc.render.use_motion_blur = True
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"


def mat(name, color=(1, 1, 1, 1), metal=0.0, rough=0.4, image=None, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = color
        b.inputs["Emission Strength"].default_value = emit
    if image:
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(ROOT, image))
        m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    return m


def light(loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new("l", "AREA")
    ld.energy, ld.size, ld.color = energy, size, color
    o = bpy.data.objects.new("l", ld)
    o.location = loc
    sc.collection.objects.link(o)
    o.rotation_euler = (0, 0, 0)
    tr = o.constraints.new("TRACK_TO")
    tr.target = target
    return o


# ---------------------------------------------------------------- मंच: लकड़ी का सरकारी काउंटर + धुंधली खिड़की
bpy.ops.object.empty_add(location=(0, 0, 0.3))
target = bpy.context.active_object
bpy.ops.mesh.primitive_plane_add(size=30)
floor = bpy.context.active_object
floor.data.materials.append(mat("wood", (0.33, 0.17, 0.07, 1), rough=0.35))
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 6, 4), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.data.materials.append(mat("wall", (0.08, 0.12, 0.25, 1), emit=0.4))
for x in (-4, 0, 4):                                    # पीछे काउंटर की खिड़कियों की रोशनी (bokeh)
    bpy.ops.mesh.primitive_plane_add(size=2.2, location=(x, 5.9, 3.2), rotation=(math.radians(90), 0, 0))
    bpy.context.active_object.data.materials.append(mat("win", (1.0, 0.75, 0.35, 1), emit=6))

cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 50
cam_d.dof.use_dof = True
cam_d.dof.focus_object = target
cam_d.dof.aperture_fstop = 2.2
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
tr = cam.constraints.new("TRACK_TO")
tr.target = target
for f, loc in ((1, (0, -7.5, 3.2)), (FPS * SECS, (1.4, -6.2, 2.6))):   # धीरे-धीरे पास और बग़ल (ज़िंदा कैमरा)
    cam.location = loc
    cam.keyframe_insert("location", frame=f)

light((-4, -4, 6), 1500, 5)
light((5, -2, 4), 600, 3, (1, 0.8, 0.6))
world = bpy.data.worlds.new("w")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (1.0, 0.86, 0.68, 1)   # गर्म रोशनी — धातु काली नहीं दिखे
world.node_tree.nodes["Background"].inputs[1].default_value = 1.1
sc.world = world


def drop(obj, x, y, z0, f0, rot, bounce=0.25):
    """ऊपर से गिरो, हल्का उछलो, टिक जाओ (keyframes — physics sim नहीं, ताकि हर बार एक जैसा और तेज़ render)."""
    fl = max(0.05, obj.dimensions.z / 2)
    for f, z, r in ((f0, z0, rot), (f0 + 10, fl, rot * 0.3), (f0 + 14, fl + bounce, rot * 0.15), (f0 + 18, fl, 0)):
        obj.location = (x, y, z)
        obj.rotation_euler = (r, r * 0.5, r * 0.8)
        obj.keyframe_insert("location", frame=f)
        obj.keyframe_insert("rotation_euler", frame=f)
    obj.location = (x, y, z0)


if WHICH == "coins":
    gold = mat("coin", (0.95, 0.76, 0.38, 1), metal=0.85, rough=0.32)
    silver = mat("coin2", (0.86, 0.86, 0.88, 1), metal=0.85, rough=0.35)
    for k in range(9):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.07, vertices=64)
        c = bpy.context.active_object
        bev = c.modifiers.new("b", "BEVEL")
        bev.width, bev.segments = 0.02, 3
        c.data.materials.append(gold if k % 3 else silver)
        drop(c, random.uniform(-1.6, 1.6), random.uniform(-0.8, 0.9), 3.2, -4 + k * 5, random.uniform(2, 5), 0.18)
elif WHICH == "toffee":
    wrap = mat("wrap", image="assets/fx/toffee_tex.png", rough=0.15)
    wrap.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 1.0
    for k, (x, y) in enumerate(((0, 0), (-1.5, 0.6), (1.6, 0.4))):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=48, ring_count=24)
        body = bpy.context.active_object
        body.scale = (1.5, 0.75, 0.75)
        bpy.ops.object.transform_apply(scale=True)
        body.data.materials.append(wrap)
        for side in (-1, 1):                              # दोनों तरफ़ मरोड़ा हुआ कागज़
            bpy.ops.mesh.primitive_cone_add(radius1=0.42, radius2=0.08, depth=0.6, vertices=16,
                                            location=(side * 0.95, 0, 0), rotation=(0, math.radians(-90 * side), 0))
            t = bpy.context.active_object
            t.data.materials.append(wrap)
            t.parent = body
            t.location = (side * 0.95, 0, 0)
        drop(body, x, y, 3.4, -4 + k * 14, random.uniform(3, 6), 0.3)
        body.keyframe_insert("rotation_euler", frame=1 + k * 18 + 30)
else:                                                     # notes: गड्डी ऊपर तक चढ़े
    note = mat("note", image="assets/fx/note_tex.png", rough=0.55)
    band = mat("band", (0.95, 0.85, 0.2, 1), rough=0.4)
    for k in range(14):
        bpy.ops.mesh.primitive_cube_add(size=1)
        n = bpy.context.active_object
        n.scale = (2.4, 1.12, 0.07)
        n.data.materials.append(note)
        z = 0.07 + k * 0.14
        f0 = -3 + k * 5
        for f, zz, rz in ((f0, 4, random.uniform(-1, 1)), (f0 + 9, z, random.uniform(-0.08, 0.08))):
            n.location = (random.uniform(-0.05, 0.05), 0, zz)
            n.rotation_euler = (0, 0, rz)
            n.keyframe_insert("location", frame=f)
            n.keyframe_insert("rotation_euler", frame=f)
        if k % 4 == 3:                                    # हर गड्डी पर पीली पट्टी
            bpy.ops.mesh.primitive_cube_add(size=1)
            b = bpy.context.active_object
            b.scale = (0.25, 0.78, 0.065)
            b.data.materials.append(band)
            b.parent = n
    target.location = (0, 0, 0.9)
    for f, loc in ((1, (0, -6.0, 2.8)), (FPS * SECS, (1.0, -4.8, 2.4))):    # गड्डी के पास कैमरा
        cam.location = loc
        cam.keyframe_insert("location", frame=f)

out_dir = os.path.join(ROOT, "assets", "fx", "props", WHICH + "_frames")
os.makedirs(out_dir, exist_ok=True)
sc.render.image_settings.file_format = "JPEG"
sc.render.image_settings.quality = 92
sc.render.filepath = os.path.join(out_dir, "")
bpy.ops.render.render(animation=True)
print("rendered", WHICH, len(os.listdir(out_dir)))
