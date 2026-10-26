"""Headless Blender 3.x/4.x low-cost animated prop scene."""
import bpy, math, os
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version[0]>=4 else 'BLENDER_EEVEE'
scene.render.resolution_x=360
scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.render.fps=25
scene.frame_end=25
bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))
box=bpy.context.object
box.name='Comedy Parcel'
box.scale=(1.4,0.9,0.65)
box.keyframe_insert(data_path='rotation_euler',frame=1)
box.rotation_euler.z=math.radians(18)
box.keyframe_insert(data_path='rotation_euler',frame=13)
box.rotation_euler.z=0
box.keyframe_insert(data_path='rotation_euler',frame=25)
bpy.ops.object.camera_add(location=(0,-8,4))
cam=bpy.context.object
direction=box.location-cam.location
cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(2,-4,6))
bpy.context.object.data.energy=1200
scene.world.color=(0.3,0.3,0.3)
scene.render.image_settings.file_format='PNG'
scene.render.filepath=os.environ.get('BLENDER_OUT','/tmp/bakra_blender_')
bpy.ops.render.render(animation=True)
