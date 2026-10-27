"""Original 3D COD parcel scene for Bakra News; Blender background renderer."""
import bpy, math, os
from mathutils import Vector
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version >= (4,2,0) else "BLENDER_EEVEE"
sc.render.resolution_x=540;sc.render.resolution_y=960;sc.render.resolution_percentage=100
sc.render.fps=24;sc.frame_start=1;sc.frame_end=120
sc.render.image_settings.file_format="FFMPEG";sc.render.ffmpeg.format="MPEG4";sc.render.ffmpeg.codec="H264"
sc.render.filepath=os.environ.get("BLENDER_OUTPUT","/tmp/bakra_cod_3d.mp4")
sc.world.color=(0.35,0.45,0.55)
def mat(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m
floor=mat("ground",(0.44,0.63,0.53)); cardboard=mat("parcel",(0.65,0.38,0.18)); blue=mat("tv",(0.06,0.12,0.22));glass=mat("screen",(0.12,0.58,0.77));red=mat("COD sticker",(0.88,0.1,0.1))
def cube(name,loc,scale,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
cube("courtyard",(0,0,-.12),(12,12,.2),floor)
cube("COD delivery parcel",(-4,0,1),(1.8,1.1,1.6),cardboard)
cube("parcel red seal",(-4,-.56,1),(1.2,.03,.36),red)
cube("television",(1.5,0,1.5),(2.5,.3,1.6),blue)
cube("television glass",(1.5,-.17,1.5),(2.24,.04,1.32),glass)
parcel=bpy.data.objects["COD delivery parcel"];seal=bpy.data.objects["parcel red seal"]
for f,x in [(1,-4),(60,-1.6),(95,-.5),(120,-.5)]:
 for ob in (parcel,seal):
  ob.location.x=x;ob.keyframe_insert(data_path="location",frame=f)
cam_data=bpy.data.cameras.new("camera");cam=bpy.data.objects.new("camera",cam_data);sc.collection.objects.link(cam);sc.camera=cam
cam.location=(7,-11,7);direction=Vector((0,0,1))-cam.location;cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler();cam_data.type="ORTHO";cam_data.ortho_scale=8
for f,z in [(1,8.6),(120,7.1)]:
 cam_data.ortho_scale=z;cam_data.keyframe_insert(data_path="ortho_scale",frame=f)
bpy.ops.object.light_add(type="AREA",location=(0,-4,8));bpy.context.object.data.energy=1300;bpy.context.object.data.shape="DISK";bpy.context.object.data.size=8
sc.render.film_transparent=False
bpy.ops.render.render(animation=True)
print("BAKRA_3D_COD_RENDER_COMPLETE",sc.render.filepath)
