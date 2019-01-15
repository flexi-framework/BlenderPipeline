#!/usr/bin/python
# -*- coding: utf8 -*-
#=================================================================================================================================
# Copyright (c) 2018  Andrea Beck, Nico Krais
# This file is part of the FLEXI Blender pipeline, for more information see https://www.flexi-project.org.
#
# This script is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License 
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This script is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License v3.0 for more details.
#
# You should have received a copy of the GNU General Public License along with this script.
# If not, see <http://www.gnu.org/licenses/>.
#=================================================================================================================================


##################################################################################################################################
#
#                                                        ANIMATE PARAVIEW SCRIPT
#
# Python script which can be used to automatically apply a ParaView state to a list of input files (CFD solutions) and perform
# output of the results in either .x3d or .ply file format.
#
# Based on the animate_paraview.py script of the FLEXI software package, https://www.flexi-project.org.
#
# You will always need to specify the path to the ParaView layout file (.pvsm), which needs to be created beforehand using
# a single sample of the CFD solution files.
# Default output is done in .ply file format. In that case you need to specify the source of the output, since only a single
# pipeline object can be exported using the .ply export. Additionally, the name of the variable used to color the pipeline
# object needs to be supplied. You can also switch to .x3d output, which will export the whole scene.
# The resulting output will be saved in a subfolder and the name of the files is given by the time stamp and the  appendix.
#
##################################################################################################################################


import argparse
import os
import subprocess
import sys

parser = argparse.ArgumentParser(description='Animate Paraview data')
parser.add_argument('-l','--layout',                       help='ParaView State file (.pvsm-file)')
parser.add_argument('-r','--reader',                       help='Path to custom reader plugin (optional)')
parser.add_argument('-m','--mpi', type=int, default=1,     help='Number of MPI procs for rendering (defaults to single execution)')
parser.add_argument('-o','--output',        default='',    help='Appendix for filenames')
parser.add_argument('-x','--outputmode',    default='ply', help='export ply or x3d, options: ply, x3d')
parser.add_argument('-s','--source',        default='',    help='name of the pipeline object that should be saved (ply output)')
parser.add_argument('-v','--variable',      default='',    help='name of the variable that is used to colour the pipeline object (ply output)')
parser.add_argument('-f','--folder',        default='',    help='output folder')
parser.add_argument('plotfiles',nargs='+',                 help='Files to animate (.vtu/.pvtu/.h5-files)')


args = parser.parse_args()

# if output folder not exists, create it 
cwd = os.getcwd()
fp=os.path.join(os.getcwd(), args.folder)
if not os.path.exists(fp):
    os.makedirs(fp)

plotfiles = [f for f in args.plotfiles if (os.path.splitext(f)[1] in ['.pvtu', '.vtu', '.plt', '.vtm', '.h5', '.h5group']) ]

i = 0
for p in plotfiles :
    i = i+1
    sys.stdout.write('\r%05.2f %% Animate: %s' % (100.0 * i / len(plotfiles), p))
    sys.stdout.flush()
    fn = os.path.splitext(p)[0]+ args.output + '.py'
    f = open(fn, 'w')
    # get filename
    mode=args.outputmode
    if mode=="ply":
       of = os.path.splitext(p)[0] + args.output + '.ply'
    else: 
       of = os.path.splitext(p)[0] + args.output + '.x3d'
    of2=os.path.basename(of)
    # create output filename
    of=os.path.join(os.getcwd(), args.folder, of2)
    if mode=="ply":
      print("\nExporting PLY data")
      f.write("""from paraview.simple import * 
import os

paraview.simple._DisableFirstRenderCameraReset()
""")
      if args.reader :
        f.write("servermanager.LoadPlugin('%s')\n" % (args.reader))

      f.write("""servermanager.LoadState('%s')
statefilename = GetSources() 
plotfilename = None
for k in statefilename.keys() :
    if os.path.splitext(k[0])[1] in ['.pvtu', '.vtu', '.plt', '.vtm', '.h5', '.h5group'] :
        plotfilename = k[0]
        break

if not plotfilename : exit(1)

reader = FindSource(plotfilename)
reader.FileName = ['%s'] 
reader.FileNameChanged() 
RenderView1 = GetRenderView()
if RenderView1.InteractionMode == "2D" :
    RenderView1.CameraParallelProjection=1 
SetActiveView(RenderView1)
Render()

# find source
source = FindSource('%s')

# set active source
SetActiveSource(source)

# get color transfer function/color map
LUT = GetColorTransferFunction('%s')

# save data
SaveData('%s', proxy=source, EnableColoring=1,
    ColorArrayName=['POINTS', '%s'],
    LookupTable=LUT)
""" % (args.layout,p,args.source,args.variable,of,args.variable))
      f.close()
    else:
      print("\nExporting X3D data")
      f.write("""from paraview.simple import * 
import os

paraview.simple._DisableFirstRenderCameraReset()
""")
      if args.reader :
          f.write("servermanager.LoadPlugin('%s')\n" % (args.reader))

      f.write("""servermanager.LoadState('%s')
statefilename = GetSources() 
plotfilename = None
for k in statefilename.keys() :
    if os.path.splitext(k[0])[1] in ['.pvtu', '.vtu', '.plt', '.vtm', '.h5', '.h5group'] :
        plotfilename = k[0]
        break

if not plotfilename : exit(1)

reader = FindSource(plotfilename)
reader.FileName = ['%s'] 
reader.FileNameChanged() 
RenderView1 = GetRenderView()
if RenderView1.InteractionMode == "2D" :
    RenderView1.CameraParallelProjection=1 
SetActiveView(RenderView1)
Render()

view = GetActiveView()
exporters=servermanager.createModule('exporters')
x3dExporter=exporters.X3DExporter(FileName='%s')
x3dExporter.SetView(view)
x3dExporter.Write()

""" % (args.layout,p,of))
      f.close()
    if args.mpi > 1 :
        cmd = ['mpirun', '-n', str(args.mpi), 'pvbatch', '--use-offscreen-rendering', fn]
    else :
        cmd = ['pvbatch', '--use-offscreen-rendering', fn]
    p = subprocess.Popen(cmd)
    p.wait()
    os.remove(fn)
sys.stdout.write('\n')
