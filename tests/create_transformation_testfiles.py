from pathlib import Path
import sys
import numpy as np
import vedo as v
from shapely.geometry import box
from math import sin, cos, pi

sys.path.append(str(Path.cwd()))
import FTL


class ParentDummy:
    xmin = -100
    xmax = 100
    ymin = -100
    ymax = 100
    zmin = -1
    zmax = 1

    def update_progress(self, foo, bar):
        pass


data_dir = Path(__file__).parent.parent / "data"
test_data_dir = Path(__file__).parent / "data"


def compare_to_file(points, filename) -> bool:
    with open(test_data_dir / filename, "r") as f:
        if f.read() == np.round(points, 13).__repr__():
            return True
        else:
            return False


def write_to_file(points, filename) -> bool:
    with open(test_data_dir / filename, "w") as f:
        f.write(np.round(points, 13).__repr__())
        return True


def process_transformation(
    tr: FTL.Transformation, res: FTL.Transformation, points: np.ndarray
) -> bool:
    for pid, pt in enumerate(points):
        if tr.is_in_scope(pt):
            vec = np.array([pt[0], pt[1], pt[2], 1])
            vec = np.dot(tr.get_matrix_at(pt), vec)
            points[pid][0] = vec[0]
            points[pid][1] = vec[1]
            points[pid][2] = vec[2]
        elif tr.addResidual and res.is_in_scope(pt):
            vec = np.array([pt[0], pt[1], pt[2], 1])
            vec = np.dot(res.get_matrix_at(pt), vec)
            points[pid][0] = vec[0]
            points[pid][1] = vec[1]
            points[pid][2] = vec[2]
    return points


def process_all(input, filename):
    plt = v.Plotter(N=len(input))  # .user_mode(v.interactor_modes.MousePan())
    parent = ParentDummy()
    mesh = v.load(str(data_dir / filename)).clean()

    print("Testing...")
    for i, tr in enumerate(input):
        mesh2 = mesh.clone()
        points = mesh2.points()
        tr.parent = parent
        tr.name = tr.__class__.__name__
        if tr.addResidual:
            res = tr.get_residual_transformation()

        filename = tr.name + ".txt"

        if tr.transformWholeMesh:
            # Transformation implemented a method to  the whole transformation on its own
            points = tr.transformMesh(mesh.clone()).points()
        else:
            process_transformation(tr, res, points)
        print("Writing {} to '{}'".format(tr.name, filename))
        print("-> Write: {}".format(write_to_file(points, filename)))
        print("-> Compare: {}".format(compare_to_file(points, filename)))

        mesh2.points(points)
        plt.at(i).show(mesh2)
    plt.interactive().close()


input = []

json_db = {
    "points": [
        {"x": -20, "y": 10},
        {"x": 0, "y": -10},
        {"x": 60, "y": -10},
        {"x": 60, "y": 10},
    ],
    "angle": 90,
}
json_sp = {
    "points": [
        {"x": -40, "y": 10},
        {"x": -20, "y": -10},
    ],
    "length": 70,
    "dir": "POSX",
    "turns": 1,
}
angle = -pi / 6
mat = [
    [cos(angle), 0, sin(angle), 0],
    [0, 1, 0, 0],
    [-sin(angle), 0, cos(angle), 0],
]
bounds = box(-60, -10, 60, 10)
tr_zbend = FTL.ZBend(-20, 20, -10, 10, 90, FTL.DIR.POSX)
tr_dirbend = FTL.DirBend(json_db)
tr_lin = FTL.LinearTransformation(
    mat,
    bounds,
)
tr_spiral = FTL.Spiral(json_sp)
# res = tr.get_residual_transformation()

input.append(tr_zbend)
input.append(tr_dirbend)
input.append(tr_lin)
input.append(tr_spiral)

process_all(input, "Teststrip.stl")
