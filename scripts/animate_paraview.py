#!/usr/bin/python
# -*- coding: utf8 -*-


################################################################
#
# Modified animate_paraview script for the output of .ply files.
# You need to specify the name of the source that should be exported
# and the variable that is used to colour the surface.
#
################################################################


import argparse
import os
import subprocess
import sys

parser = argparse.ArgumentParser(description='Animate Paraview data')
parser.add_argument('-l','--layout',  help='Paraview State file (.pvsm-file)')
parser.add_argument('-r','--reader',  help='Path to custom reader plugin')
parser.add_argument('-m','--mpi', type=int, default=1, help='Number of MPI procs for rendering')
parser.add_argument('-o','--output', default='',  help='Appendix for filenames')
parser.add_argument('-x','--outputmode', default='ply',  help='export ply or x3d, options: ply, x3d')
parser.add_argument('-s','--source', default='',  help='name of the pipeline object that should be saved')
parser.add_argument('-v','--variable', default='',  help='name of the variable that is used to colour the pipeline object')
parser.add_argument('-f','--folder', default='',  help='output folder')
parser.add_argument('plotfiles', nargs='+', help='Files to animate (.vtu/.pvtu/.h5-files)')


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
