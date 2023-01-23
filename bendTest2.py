global MAX_EDGE_LENGTH
MAX_EDGE_LENGTH = 2

import numpy as np
from vedo import *
from MatrixTransformer import *
from Transformation import *
from ZBend import *
from LinearTransformation import *
from FileParser import FileParser

print("Hello!")
plt = Plotter(interactive=False, axes=7)

parser = FileParser("LTest_hook.json")
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
