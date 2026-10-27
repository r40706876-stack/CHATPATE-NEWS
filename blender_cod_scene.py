"""Original stylized 3D COD comedy reconstruction, rendered in Blender.
No third-party footage or copyrighted character model is used.
The MP4 is a silent visual insert; final Hindi dialogue comes from talk-episode.
"""
import bpy
import math
import os
from mathutils import Vector

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
# Fast original 3D geometry render on CPU-only GitHub runners.
# Eevee was taking ~39 seconds per frame and timed out before 96 frames.
# Workbench keeps genuine animated 3D geometry, material colors and camera.
sc.render.engine="BLENDER_WORKBENCH"
sc.display.shading.light="STUDIO"
sc.display.shading.color_type="MATERIAL"
sc.display.shading.show_shadows=True
sc.display.shading.show_cavity=True
sc.display.shading.cavity_type="BOTH"
sc.render.image_settings.color_mode="RGB"
sc.render.resolution_x=540
sc.render.resolution_y=960
sc.render.resolution_percentage=100
sc.render.fps=24
sc.frame_start=1
sc.frame_end=96
sc.render.image_settings.file_format="FFMPEG"
sc.render.ffmpeg.format="MPEG4"
sc.render.ffmpeg.codec="H264"
sc.render.filepath=os.environ.get("BLENDER_OUTPUT","/tmp/bakra_cod_3d.mp4")
sc.render.film_transparent=False
sc.world.color=(0.48,0.58,0.70)

def mat(name, rgb, roughness=0.8):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    shader=m.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value=(*rgb,1)
        shader.inputs["Roughness"].default_value=roughness
    return m

cream=mat("warm courtyard",(0.84,0.81,0.69))
wall=mat("sunlit wall",(0.83,0.72,0.55))
wood=mat("village door",(0.46,0.25,0.14))
card=mat("parcel cardboard",(0.65,0.39,0.19))
tape=mat("parcel tape",(0.96,0.78,0.44))
red=mat("COD red",(0.86,0.12,0.13))
blue=mat("courier uniform",(0.10,0.37,0.70))
white=mat("Chacha kurta",(0.92,0.89,0.77))
skin=mat("cartoon skin",(0.78,0.49,0.31))
hair=mat("silver hair",(0.70,0.72,0.74))
dark=mat("outline and eyes",(0.055,0.08,0.13))
tvmat=mat("TV housing",(0.10,0.17,0.28))
glass=mat("TV glass",(0.21,0.63,0.80),0.25)
green=mat("green trim",(0.19,0.43,0.33))

def cube(name,loc,dims,material,bevel=0.035,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    ob=bpy.context.object
    ob.name=name
    ob.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(material)
    if bevel:
        mod=ob.modifiers.new("rounded edges","BEVEL")
        mod.width=bevel
        mod.segments=2
        ob.modifiers.new("weighted normals","WEIGHTED_NORMAL")
    if parent:
        ob.parent=parent
    return ob

def sphere(name,loc,radius,material,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=radius,location=loc)
    ob=bpy.context.object
    ob.name=name
    ob.data.materials.append(material)
    for face in ob.data.polygons:
        face.use_smooth=True
    if parent:
        ob.parent=parent
    return ob

def cylinder(name,loc,radius,depth,material,parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=depth,location=loc)
    ob=bpy.context.object
    ob.name=name
    ob.data.materials.append(material)
    if parent:
        ob.parent=parent
    return ob

def group(name):
    ob=bpy.data.objects.new(name,None)
    sc.collection.objects.link(ob)
    return ob

def lettering(text,loc,size,material,name):
    cv=bpy.data.curves.new(name,"FONT")
    cv.body=text
    cv.size=size
    cv.align_x="CENTER"
    cv.extrude=0.006
    ob=bpy.data.objects.new(name,cv)
    sc.collection.objects.link(ob)
    ob.location=loc
    ob.rotation_euler[0]=math.pi/2
    ob.data.materials.append(material)
    return ob

cube("courtyard ground",(0,0,-.12),(8,8,.22),cream)
cube("sunny house wall",(0,2.0,2.0),(8,.18,4.2),wall)
cube("wooden front door",(2.0,1.87,1.35),(1.5,.13,2.7),wood)
cube("doorframe top",(2.0,1.72,2.76),(1.8,.17,.18),green)
cube("door handle",(2.58,1.71,1.35),(.10,.11,.17),tape)

parcel=group("animated COD parcel")
cube("cardboard box",(-.3,-1.2,.62),(1.35,.98,1.18),card,parent=parcel)
cube("cross tape",(-.3,-1.70,.62),(.24,.055,1.17),tape,parent=parcel)
cube("COD red label",(-.3,-1.745,.77),(.95,.05,.35),red,parent=parcel)
cube("box top tape",(-.3,-1.2,1.22),(.25,.9,.025),tape,parent=parcel)

tv=group("animated television")
cube("TV housing",(.28,.45,1.45),(2.0,.25,1.4),tvmat,parent=tv)
cube("TV glowing screen",(.28,.292,1.45),(1.78,.06,1.18),glass,parent=tv)
cube("TV stand",(.28,.48,.65),(.20,.38,.28),dark,parent=tv)
cube("TV foot",(.28,.43,.52),(.9,.48,.08),dark,parent=tv)

def person(name,x,shirt,elder=False):
    root=group(name+" animated rig")
    cylinder(name+" torso",(0,.25,1.45),.35,1.12,shirt,parent=root)
    sphere(name+" head",(0,.12,2.40),.33,skin,parent=root)
    sphere(name+" left eye",(-.13,-.16,2.45),.044,dark,parent=root)
    sphere(name+" right eye",(.13,-.16,2.45),.044,dark,parent=root)
    # Eyes and expressive mouth must remain readable in a portrait phone crop.
    cube(name+" left eyebrow",(-.13,-.21,2.57),(.18,.055,.055),dark,parent=root)
    cube(name+" right eyebrow",(.13,-.21,2.57),(.18,.055,.055),dark,parent=root)
    cube(name+" surprised mouth",(0,-.205,2.17),(.15,.055,.11),dark,parent=root)
    for side in (-1,1):
        cube(name+" arm "+str(side),(.48*side,.20,1.52),(.20,.30,.90),shirt,parent=root)
        cube(name+" leg "+str(side),(.18*side,.23,.50),(.23,.33,.95),dark,parent=root)
    if elder:
        sphere(name+" silver hair",(0,.16,2.66),.30,hair,parent=root)
        cube(name+" moustache", (0,-.19,2.27),(.27,.075,.075),dark,parent=root)
        cube(name+" red scarf",(0,-.08,1.70),(.17,.10,.90),red,parent=root)
    else:
        cube(name+" blue cap",(0,.08,2.76),(.73,.54,.17),blue,parent=root)
        cube(name+" cap brim",(0,-.24,2.72),(.63,.25,.07),blue,parent=root)
    root.location.x=x
    return root

courier=person("courier",-1.85,blue)
chacha=person("Chacha",1.78,white,elder=True)
lettering("PAY COD",(.28,.185,1.46),.22,red,"TV payment demand")
lettering("COD",(-.30,-1.79,.73),.27,white,"COD parcel text")
lettering("1.69 LAKH",(0,-.25,3.30),.43,red,"large COD amount")
lettering("TV DELIVERY",(0,-.25,3.76),.28,dark,"delivery headline")

for frame,px,cx,rx,tz in [
    (1,-1.70,-2.05,1.60,.0),
    (30,-1.05,-1.72,1.70,.05),
    (57,-.35,-1.32,2.00,.12),
    (78,.02,-1.30,2.27,.08),
    (96,.02,-1.30,2.35,.04),
]:
    parcel.location.x=px
    courier.location.x=cx
    chacha.location.x=rx
    chacha.rotation_euler[1]=tz
    for ob in (parcel,courier,chacha):
        ob.keyframe_insert(data_path="location",frame=frame)
    chacha.keyframe_insert(data_path="rotation_euler",frame=frame)

# Physical acting timed to the four-second delivery gag: the courier
# presents the box, Chacha throws up both arms, and the parcel wobbles.
for frame, gesture, panic, wobble in [
    (1,0.0,0.0,0.0),
    (22,-0.45,0.25,-0.04),
    (45,-0.80,0.75,0.08),
    (70,-0.20,1.10,-0.06),
    (96,-0.65,0.85,0.0),
]:
    courier_arm=bpy.data.objects["courier arm 1"]
    courier_arm.rotation_euler[1]=gesture
    courier_arm.keyframe_insert(data_path="rotation_euler",frame=frame)
    for side in (-1,1):
        chacha_arm=bpy.data.objects["Chacha arm "+str(side)]
        chacha_arm.rotation_euler[1]=panic * side
        chacha_arm.keyframe_insert(data_path="rotation_euler",frame=frame)
    parcel.rotation_euler[1]=wobble
    parcel.keyframe_insert(data_path="rotation_euler",frame=frame)

for frame,z in [(1,0),(48,.14),(96,.04)]:
    tv.rotation_euler[2]=z
    tv.keyframe_insert(data_path="rotation_euler",frame=frame)

cam_data=bpy.data.cameras.new("portrait cartoon camera")
cam=bpy.data.objects.new("portrait cartoon camera",cam_data)
sc.collection.objects.link(cam)
sc.camera=cam
cam.location=(0,-10,5.2)
cam.rotation_euler=(Vector((0,0,1.65))-cam.location).to_track_quat("-Z","Y").to_euler()
cam_data.type="ORTHO"
for frame,scale in [(1,7.7),(96,7.1)]:
    cam_data.ortho_scale=scale
    cam_data.keyframe_insert(data_path="ortho_scale",frame=frame)

bpy.ops.object.light_add(type="AREA",location=(-3,-4,8))
bpy.context.object.data.energy=1700
bpy.context.object.data.size=7
bpy.ops.object.light_add(type="AREA",location=(4,1,6))
bpy.context.object.data.energy=850
bpy.context.object.data.size=5

bpy.ops.render.render(animation=True)
print("BAKRA_3D_COD_RENDER_COMPLETE",sc.render.filepath)
