#!/usr/bin/python
# -*- coding: utf8 -*-
import bpy
import os
import sys
from mathutils import Vector

##################################################################################################
#
# Blender python script used to render images from a pre-defined blender layout, with a
# changing object in each frame. The object is imported as .ply or .x3d files.
#
# Usage: blender -b layout.blend --python animate_blender.py
#
##################################################################################################

#--------------------------------------------------------------------------#
# USER-DEFINED PARAMETERS

# Relative path to a folder that contains the files that should be imported,
# each file is assigned to a single frame in blender.
importFolder = "output"
# If the imported geometry should be scaled, set a scaling factor here. The scaling
# is done in all directions.
scale        = None          # scale = 50
# If the imported geometry should be duplicated and displaced (e.g. to visualize a
# periodic problem), then set one or several displacement vectors here.
displacement = []            # displacement = [Vector((0,10,0)),Vector((0,-10,0))]
# The name of the material that should be assigned to the imported geometry. This material
# must exist in the .blend file. Alternatively, you can create a new material in the script.
matName      = "Mat"
# The folder where the rendered images should be saved.
outputFolder = "renderings"
# An affix that is added to each rendered image. The files will be named e.g. "affix_CameraName_001.png".
affix        = "render"
# Cameras to be omitted from rendering, names according to the .blend file
omit_cameras     = []
# resolution in percent for rendering. The resolution itself (e.g. 1920x1080) is set in .blend
renderresolution = 100
# rendering samples: number of samples per image 
rendersamples = 128
#--------------------------------------------------------------------------#
# Fixed parameters
geoName = "imported_geometry1"
blenderVersion = bpy.app.version
if blenderVersion[1] >= 79:
  x3dImportString = 'Shape_IndexedFaceSet'
else:
  x3dImportString = 'ShapeIndexedFaceSet'
#--------------------------------------------------------------------------#

# Turn relative into absolute paths
importFolder=os.path.join(os.getcwd(), importFolder)
outputFolder=os.path.join(os.getcwd(), outputFolder)

# Get a list of all files in this directory - these are going to be the files we import and visualize
importFiles = os.listdir(importFolder)
importFiles.sort()

bpy.data.scenes["Scene"].cycles.samples=rendersamples

# Start the rendering loop over all import files
for frame in range(len(importFiles)):
    importFile = os.path.join(importFolder,importFiles[frame])
    print("Processing frame ",frame+1," importing ",importFile)

    bpy.context.scene.frame_set(frame+1)

    # Import the current object, either supplied as a .ply or a .x3d file
    # The geometry will always be renamed so it can be easily used later on
    if os.path.splitext(importFile)[1] == ".ply":
        bpy.ops.import_mesh.ply(filepath=importFile)
        # rename geometry
        bpy.data.objects[os.path.splitext(os.path.basename(importFile))[0]].name=geoName+"0"
        nImportedGeo = 1
    else:
        bpy.ops.import_scene.x3d(filepath=importFile, filter_glob="*.x3d;*.wrl", axis_forward='Z', axis_up='Y')
        # check for geometries / meshes, lamps and cameras
        imported_geo_exists = [item.name for item in bpy.data.objects if x3dImportString in item.name]
        nImportedGeo = len(imported_geo_exists)
        imported_lights_exists = [item.name for item in bpy.data.objects if ("TODO" in item.name or "DirectLight" in item.name)]
        imported_cameras_exists = [item.name for item in bpy.data.objects if "Viewpoint" in item.name]
        # rename geometry
        if imported_geo_exists:
            for i in range(0,nImportedGeo):
                bpy.data.objects[imported_geo_exists[i]].name=geoName+str(i)
            bpy.ops.object.select_all(action='DESELECT')
        # delete lights and cameras that blender creates after import
        if imported_lights_exists:
            #bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_pattern(pattern="TODO*")
            bpy.ops.object.delete(use_global=False)
            bpy.ops.object.select_pattern(pattern="DirectLight*")
            bpy.ops.object.delete(use_global=False)
        if imported_cameras_exists:
            #bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_pattern(pattern="Viewpoint*")
            bpy.ops.object.delete(use_global=False)

    #--------------------------------------------------------------------------#
    # if required, scale geometry after import
    if scale:
        for i in range(0,nImportedGeo):
            bpy.data.objects[geoName+str(i)].scale=(scale,scale,scale)

    #--------------------------------------------------------------------------#
    # Assign the material to the imported geometry
    for i in range(0,nImportedGeo):
        bpy.context.scene.objects.active = bpy.data.objects[geoName+str(i)]
        ob = bpy.context.active_object
        mat = bpy.data.materials.get(matName)
        if ob.data.materials:
            # assign to 1st material slot if other materials exist
            ob.data.materials[0] = mat
        else:
            # if no slots are present, add to first
            ob.data.materials.append(mat)

    #--------------------------------------------------------------------------#
    # if required, copy geometry and move it (e.g for making view nicer / fuller / periodic stuff)
    if len(displacement) > 0:
        for dispVec in displacement:
            for i in range(0,nImportedGeo):
                src_obj = bpy.data.objects[geoName+str(i)]
                src_obj.select = True
                scn = bpy.context.scene
                new_obj = src_obj.copy()
                new_obj.data = src_obj.data.copy()
                new_obj.animation_data_clear()
                scn.objects.link(new_obj)
                new_obj.location += dispVec

    #--------------------------------------------------------------------------#
    # render all cameras to image files
    for obj in bpy.data.objects:
       # Find cameras from object type
       if  obj.type =='CAMERA' and obj.name not in omit_cameras:
           print("rendering image for camera ",obj.name)
           # Set Scenes camera and output filename
           bpy.data.scenes['Scene'].camera = obj
           bpy.data.scenes['Scene'].render.resolution_percentage=renderresolution
           camera_name=bpy.data.scenes['Scene'].camera.name
           filepath=outputFolder+'/'+affix+'_'+str(camera_name)+'_'+str(frame+1).zfill(3)+'.png'
           bpy.context.scene.render.filepath = filepath
           bpy.ops.render.render(write_still=True)

    #--------------------------------------------------------------------------#
    # Delete the imported geometry, get ready for new import
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_pattern(pattern=geoName+'*')
    bpy.ops.object.delete(use_global=False)

bpy.ops.wm.quit_blender()
