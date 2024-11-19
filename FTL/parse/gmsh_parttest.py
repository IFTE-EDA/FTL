import gmsh


def dimtags(geoms: list[int], dim: int = 2) -> list[tuple[int, int]]:
    if not isinstance(geoms, list):
        return [(dim, geoms)]
    return [(dim, tag) for tag in geoms]


lcar = 2
gmsh.initialize()
gmsh.option.setNumber("General.Verbosity", 3)
gmsh.option.setNumber("Mesh.MshFileVersion", 2.0)
# gmsh.model.add("model")
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 1)
gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 0.4)
gmsh.option.setNumber("Mesh.Optimize", 0)
"""gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 0.1)
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.1)
gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", 0.1)
gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 3)
gmsh.option.setNumber("Mesh.RecombinationSplitQuads", 1)
gmsh.option.setNumber("Mesh.RecombinationSplitHexahedra", 1)
gmsh.option.setNumber("Mesh.RecombinationSplitPrisms", 1)
gmsh.option.setNumber("Mesh.RecombinationSplitTetrahedra", 1)
gmsh.option.setNumber("Mesh.RecombinationSplitPentaPrisms", 1)
gmsh.option.setNumber("Mesh.RecombinationSplitPyramids
"""


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


board1 = gmsh.model.occ.add_rectangle(-1, -1, 0, 50, 101)
board2 = gmsh.model.occ.add_rectangle(50.5, -1, 0, 51, 101)
board = gmsh.model.occ.fuse([(2, board1)], [(2, board2)])[0]
pads_geom = []
pad_tops = []
for y in range(2, 101, 5):
    for x in range(2, 101, 5):
        hole = gmsh.model.occ.add_rectangle(x - 1, y - 1, 1, 2, 2)
        pads_geom.append(hole)
        # pad_tops.append(hole[0])
gmsh.model.occ.synchronize()
# gmsh.fltk.run()
print(board)
# gmsh.model.occ.cut([(2, board)], [(2, pad)])

board_extr = gmsh.model.occ.extrude(board, 0, 0, 1)
print("\nBoard: ", board_extr)
pads, pad_tops = extrude_return_tops(pads_geom)
print("\nPads: ", pads)
print("\nPad-Tops: ", pad_tops)
gmsh.model.occ.synchronize()
# gmsh.model.add_physical_group(3, pads, name="Pads.extruded")
gmsh.model.occ.synchronize()
# gmsh.fltk.run()
# print("\nBefore Fragment: ", gmsh.model.occ.getEntities(3))
print("Pads_geom: ", pads_geom)
fragments = gmsh.model.occ.fragment(
    board_extr, dimtags(pads_geom, 2), removeObject=True, removeTool=True
)
gmsh.model.occ.synchronize()
# print("\nAfter Fragment: ", gmsh.model.occ.getEntities(3))
print("\nFragments: ", filter_volumes(fragments[0]))
board_filtered = filter_volumes(board_extr)
print("\nBoard Filtered: ", board_filtered)
print(
    gmsh.model.get_boundary(
        dimtags(board_filtered, 3), combined=True, oriented=False
    )
)
gmsh.model.add_physical_group(3, board_filtered, name="Board.extruded.body")
gmsh.model.add_physical_group(
    2,
    [
        b[1]
        for b in gmsh.model.get_boundary(
            dimtags(board_filtered, 3), combined=True, oriented=False
        )
    ],
    name="Board.extruded.boundary",
)
pads_filtered = filter_volumes(pads)
print("\nPads Filtered: ", pads_filtered)
pad_tops_filtered = filter_surfaces(pad_tops)
print("\nPad-Tops Filtered: ", pad_tops_filtered)
gmsh.model.add_physical_group(3, pads_filtered, name="Pads.extruded.body")
gmsh.model.add_physical_group(
    2,
    [
        b[1]
        for b in gmsh.model.get_boundary(
            dimtags(pads_filtered, 3), combined=True, oriented=False
        )
    ],
    name="Pads.extruded.boundary",
)
gmsh.model.add_physical_group(2, pad_tops_filtered, name="Pads.tops")
# print("\nFragments[1]: ", filter_volumes(fragments)[1])
gmsh.fltk.run()

gmsh.model.mesh.generate(3)
# gmsh.model.mesh.refine()
gmsh.write("model.msh")
gmsh.fltk.run()
gmsh.finalize()
