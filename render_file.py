import sys
import os.path

import numpy as np
import vedo as v
from MatrixTransformer import MatrixTransformer, debug
from Transformation import *
from ZBend import ZBend
from LinearTransformation import LinearTransformation
from FileParser import FileParser

global MAX_EDGE_LENGTH
MAX_EDGE_LENGTH = 2

plt = v.Plotter(interactive=False, axes=7)

if len(sys.argv) < 2:
    sys.exit("Please specify an input file")
if not os.path.isfile(sys.argv[1]):
    sys.exit("File not found: {}".format(sys.argv[1]))

parser = FileParser(sys.argv[1])

parser.parse()
parser.transformer.plotter = plt
# plt.show(parser.meshes[0])
parser.visualize(plt)
parser.calculate_assignments(onlybaselayer=False)
result = parser.render()
# parser.meshes[0].c("grey")
# parser.meshes[1].c("orange")


# pcb = load("LTest_hook.stl")
debug("Refining mesh")

# plt.show(parser.meshes)
plt.show(parser.transformer.debugOutput)
plt.show(result.z(40).c("grey"))
# parser.visualize(plt)

plt.render()
plt.interactive().close()
