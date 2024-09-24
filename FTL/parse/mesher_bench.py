from timeit import timeit
import pyvista as pv
import tetgen
import numpy as np

import gmsh
import vedo as v


def build_model_gmsh():
    lcar = 2
    gmsh.initialize()
    gmsh.model.add("model")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 50)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 6)
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
    board = gmsh.model.occ.add_rectangle(0, 0, 0, 101, 101)
    circles = []
    for y in range(2, 101, 5):
        for x in range(2, 101, 5):
            circle = gmsh.model.occ.addCircle(x, y, 0, 1, lcar, -1)
            circles.append(circle)
    # circle = gmsh.model.occ.addCircle(50, 50, 0, 30)
    # print(f"Circle: {circle}")
    # circlecl = gmsh.model.occ.addCurveLoop([circle])
    circlecl = [gmsh.model.occ.addCurveLoop([crcl]) for crcl in circles]
    surface_circle = [gmsh.model.occ.addPlaneSurface([cl]) for cl in circlecl]
    # print(f"Circlecl: {circlecl}")
    # print(f"Board: {board}")
    # surface_circle = gmsh.model.occ.addPlaneSurface([circlecl])
    # surface_board = gmsh.model.occ.addPlaneSurface([board])
    gmsh.model.occ.cut([(2, board)], [(2, surf) for surf in surface_circle])

    extrude = gmsh.model.occ.extrude([(2, board)], 0, 0, 1)
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(3)
    # gmsh.model.mesh.refine()
    gmsh.write("model.msh")
    gmsh.finalize()
    return extrude


def build_rects_gmsh():
    # lcar = 2
    gmsh.initialize()
    gmsh.model.add("model")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 50)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 6)
    gmsh.option.setNumber("Mesh.Optimize", 0)

    holes = []
    board = gmsh.model.occ.add_rectangle(0, 0, 0, 101, 101)
    for y in range(2, 101, 5):
        for x in range(2, 101, 5):
            hole = gmsh.model.occ.add_rectangle(x - 1, y - 1, 0, 2, 2)
            holes.append(hole)
    # circle = gmsh.model.occ.addCircle(50, 50, 0, 30)
    # print(f"Circle: {circle}")
    # circlecl = gmsh.model.occ.addCurveLoop([circle])
    # surface_circle = [gmsh.model.occ.addPlaneSurface([rect]) for rect in holes]
    # print(f"Circlecl: {circlecl}")
    # print(f"Board: {board}")
    # surface_circle = gmsh.model.occ.addPlaneSurface([circlecl])
    # surface_board = gmsh.model.occ.addPlaneSurface([board])
    gmsh.model.occ.cut([(2, board)], [(2, surf) for surf in holes])

    extrude = gmsh.model.occ.extrude([(2, board)], 0, 0, 1)
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(3)
    # gmsh.model.mesh.refine()
    gmsh.write("model.msh")
    gmsh.finalize()
    return extrude


def build_poly_gmsh():
    lcar = 2
    gmsh.initialize()
    gmsh.model.add("model")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 50)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 6)
    gmsh.option.setNumber("Mesh.Optimize", 0)

    holes = []
    outline_pts = [
        gmsh.model.occ.add_point(x, y, 0, lcar)
        for x, y in [(0, 0), (100, 0), (100, 100), (0, 100)]
    ]
    outline = gmsh.model.occ.add_curve_loop(
        [
            gmsh.model.occ.add_line(outline_pts[i], outline_pts[j])
            for i, j in [(0, 1), (1, 2), (2, 3), (3, 0)]
        ]
    )

    x = 10
    y = 10
    for y in range(2, 101, 5):
        for x in range(2, 101, 5):
            pts = [
                gmsh.model.occ.add_point(x, y, 0, lcar)
                for x, y in [
                    (x - 1, y - 1),
                    (x + 1, y - 1),
                    (x + 1, y + 1),
                    (x - 1, y + 1),
                ]
            ]
            lines = [
                gmsh.model.occ.add_line(pts[i], pts[j])
                for i, j in [(0, 1), (1, 2), (2, 3), (3, 0)]
            ]
            hole = gmsh.model.occ.add_curve_loop(lines)
            holes.append(hole)

    surface = gmsh.model.occ.add_plane_surface([outline, *holes])

    # circle = gmsh.model.occ.addCircle(50, 50, 0, 30)
    # print(f"Circle: {circle}")
    # circlecl = gmsh.model.occ.addCurveLoop([circle])
    # surface_circle = [gmsh.model.occ.addPlaneSurface([rect]) for rect in holes]
    # print(f"Circlecl: {circlecl}")
    # print(f"Board: {board}")
    # surface_circle = gmsh.model.occ.addPlaneSurface([circlecl])
    # surface_board = gmsh.model.occ.addPlaneSurface([board])

    # gmsh.model.occ.cut([(2, board)], [(2, surf) for surf in holes])

    extrude = gmsh.model.occ.extrude([(2, surface)], 0, 0, 1)
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(3)
    # gmsh.model.mesh.refine()
    gmsh.write("model.msh")
    gmsh.finalize()
    return extrude


def build_model_vedo():
    board = (
        v.Rectangle((0, 0), (101, 101))
        .triangulate()
        .triangulate()
        .c("blue")
        .extrude(1)
    )
    circles = []
    for y in range(2, 101, 5):
        for x in range(2, 101, 5):
            circle = v.Circle((x, y, 0), 1).triangulate()
            circles.append(circle)
    surface_circle = v.merge(circles).c("red").extrude(1)
    # v.show(surface_circle, board).close()
    # extr = board.boolean("intersect", surface_circle, method=1)
    board.cut_with_mesh(surface_circle)
    return board


"""
def build_poly_gmsh():
    lcar = 2
    gmsh.initialize()
    gmsh.model.add("model")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 50)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 6)
    gmsh.option.setNumber("Mesh.Optimize", 0)

    holes = []
    outline_pts = [
        gmsh.model.occ.add_point(x, y, 0, lcar)
        for x, y in [(0, 0), (100, 0), (100, 100), (0, 100)]
    ]
    outline = gmsh.model.occ.add_curve_loop(
        [
            gmsh.model.occ.add_line(outline_pts[i], outline_pts[j])
            for i, j in [(0, 1), (1, 2), (2, 3), (3, 0)]
        ]
    )

    for y in range(2, 101, 5):
        for x in range(2, 101, 5):
            pts = [
                gmsh.model.occ.add_point(x, y, 0, lcar)
                for x, y in [
                    (x - 1, y - 1),
                    (x + 1, y - 1),
                    (x + 1, y + 1),
                    (x - 1, y + 1),
                ]
            ]
            lines = [
                gmsh.model.occ.add_line(pts[i], pts[j])
                for i, j in [(0, 1), (1, 2), (2, 3), (3, 0)]
            ]
            hole = gmsh.model.occ.add_curve_loop(lines)
            holes.append(hole)

    surface = gmsh.model.occ.add_plane_surface([outline, *holes])

    # circle = gmsh.model.occ.addCircle(50, 50, 0, 30)
    # print(f"Circle: {circle}")
    # circlecl = gmsh.model.occ.addCurveLoop([circle])
    # surface_circle = [gmsh.model.occ.addPlaneSurface([rect]) for rect in holes]
    # print(f"Circlecl: {circlecl}")
    # print(f"Board: {board}")
    # surface_circle = gmsh.model.occ.addPlaneSurface([circlecl])
    # surface_board = gmsh.model.occ.addPlaneSurface([board])

    # gmsh.model.occ.cut([(2, board)], [(2, surf) for surf in holes])

    extrude = gmsh.model.occ.extrude([(2, surface)], 0, 0, 1)
    gmsh.model.occ.synchronize()
    print(gmsh.model.mesh.getElementTypes())
    gmsh.model.mesh.generate(3)
    print(gmsh.model.mesh.getElementTypes())
    # gmsh.model.mesh.refine()
    gmsh.write("model.msh")
    gmsh.finalize()
    return extrude
"""

if __name__ == "__main__":
    # print(timeit(build_model_gmsh))
    # time1 = timeit(build_rects_gmsh, number=5)
    build_poly_gmsh()

    #
    # extrude_vedo = build_model_vedo()
    # extrude_vedo.show().close()
    # build_model_tetgen()
