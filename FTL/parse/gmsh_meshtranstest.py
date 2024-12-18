import gmsh
import sys
import numpy as np
import time
import subprocess

sys.path.append(r"../..")
from FTL.core.GMSHGeometry import (
    GMSHConfig,
    GMSHGeom2D,
    GMSHGeom3D,
    GMSHPhysicalGroup,
    dimtags,
)

lcar = 2
gmsh.initialize()
gmsh.option.setNumber("General.Verbosity", 3)
gmsh.option.setNumber("Mesh.MshFileVersion", 2.0)
# gmsh.model.add("model")
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 1)
gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 0.4)
gmsh.option.setNumber("Mesh.Optimize", 0)
gmsh.option.setNumber("General.NumThreads", 8)

GMSHConfig.lcar = 0.1


def filter_volumes(elems):
    return [e[1] for e in filter(volume_filter, elems)]


def filter_surfaces(elems):
    return [e[1] for e in filter(surface_filter, elems)]


def volume_filter(elem):
    return elem[0] == 3


def surface_filter(elem):
    return elem[0] == 2


def extrude_return_tops(geoms):
    ret = []
    tops = []
    for geom in geoms:
        extr = gmsh.model.occ.extrude([(2, geom)], 0, 0, 1)
        print("\nExtrude: ", extr)
        tops.append(extr[0])
        ret.append(extr[1])
    return ret, tops


gmsh.initialize()
gmsh.model.add("model")
# board = GMSHGeom2D().add_rectangle((0, 0), (9, 5)).extrude(0.1)
board = GMSHGeom2D().add_rectangle((0, 0), (98, 98)).extrude(0.1)
print("Board: ", board.dimtags())
# pad1 = GMSHGeom2D.get_rectangle((1, 1), (4, 4)).extrude(0.1, zpos=0.1)
# pad2 = GMSHGeom2D.get_rectangle((5, 1), (8, 4)).extrude(0.1, zpos=0.1)
parts = []
start_global = time.time()
start_creation = time.time()
for y in range(2, 101, 5):
    for x in range(2, 101, 5):
        pad = GMSHGeom2D.get_rectangle((x - 1, y - 1), (x, y))
        ext = pad.extrude(0.1, zpos=0.1)
        parts.append(ext)
pads = GMSHGeom3D.make_fusion(parts)
gmsh.model.occ.synchronize()
end_creation = time.time()
# gmsh.fltk.run()
start_frag = time.time()
board.fragment([dimtag for part in parts for dimtag in part.dimtags()])
end_frag = time.time()

gmsh.model.occ.synchronize()
group_board = board.create_elmer_body("Board")
# group_parts = GMSHPhysicalGroup(parts, "Pads")
group_parts = pads.create_elmer_body("Pads")
group_pads = pads.create_group_surface("Pads_top")
gmsh.model.occ.synchronize()
GMSHPhysicalGroup.commit_all()
gmsh.model.occ.synchronize()
# gmsh.fltk.run()
start_gen = time.time()
gmsh.model.mesh.generate(3)
end_gen = time.time()
# print("Group_Board entities: ", group_board.fetch_dimtags())
# gmsh.fltk.run()
# gmsh.model.mesh.refine()
print("Mesh created.")
m = {}
for e in gmsh.model.getEntities():
    m[e] = (
        gmsh.model.getBoundary([e]),
        gmsh.model.mesh.getNodes(e[0], e[1]),
        gmsh.model.mesh.getElements(e[0], e[1]),
    )
print("Creating new model.....")
# gmsh.model.add('model_transformed')
gmsh.model.mesh.clear()
print("Copying entities...")
for e in sorted(m):
    # gmsh.model.addDiscreteEntity(e[0], e[1], [b[1] for b in m[e][0]])
    # print("--------------------")
    pts = np.array(m[e][1][1])
    # print(e[0], e[1], len(m[e][1][0]))
    # print(pts)
    nodes = []
    if len(m[e][1][0]) > 0:
        # print("Adding nodes...")
        for x, y, z in np.asarray(pts).reshape(-1, 3):
            nodes.append(x)
            nodes.append(y)
            nodes.append(z + x**2 / 200)
    gmsh.model.mesh.addNodes(e[0], e[1], m[e][1][0], nodes, m[e][1][2])
    gmsh.model.mesh.addElements(e[0], e[1], m[e][2][0], m[e][2][1], m[e][2][2])
print("Done")
"""for i in range(len(points)):
    x, y, z = points[i]
    z += x/2
    points[i] = x, y, z
points = points.reshape(-1)
print("---------------------")
print("Points: ", points[0:10])
gmsh.mesh.addNodes(1, points)
"""
gmsh.write("model.msh")
end_global = time.time()
print("\n\n-----------------------------")
process = subprocess.Popen(
    ["git", "branch", "--show-current"], stdout=subprocess.PIPE
)
branch_name, branch_error = process.communicate()
print(str(branch_name)[2:-3])
print("\nCreation Time: ", end_creation - start_creation)
print("Fragmentation Time: ", end_frag - start_frag)
print("Mesh Generation Time: ", end_gen - start_gen)
print("\nTotal Time: ", end_global - start_global)
# gmsh.fltk.run()
gmsh.finalize()
