import sys
import os.path


global MAX_EDGE_LENGTH
MAX_EDGE_LENGTH = 2

import numpy as np
from vedo import *
from MatrixTransformer import *
from Transformation import *
from ZBend import *
from LinearTransformation import *
from FileParser import FileParser

print("LISBeT 0.1")
plt = Plotter(interactive=False, axes=7)

if len(sys.argv) < 2:
    sys.exit("Please specify an input file")
if not os.path.isfile(sys.argv[1]):
    sys.exit("File not found: {}".format(sys.argv[1]))

#parser = FileParser("LTest_hook.json")
parser = FileParser(sys.argv[1])
parser.parse()
#plt.show(parser.meshes[0])
parser.calculate_assignments()
parser.render()
parser.meshes[0].c("grey")
parser.meshes[1].c("orange")
#parser.visualize(plt)

#pcb = load("LTest_hook.stl")
print("Refining mesh")

plt.show(parser.meshes)
parser.visualize(plt)

plt.render()
plt.interactive().close()
