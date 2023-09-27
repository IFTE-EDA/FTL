import os.path
import sys
import numpy as np
import vedo as v
from shapely.geometry import box
from math import sin, cos, pi

sys.path.append(os.path.abspath(os.getcwd()))
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


class Test_Transformations:
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    def setup_class(self):
        self.parent = ParentDummy()
        self.mesh = v.load(
            os.path.join(self.data_dir, "Teststrip.stl")
        ).clean()

    def compare_to_file(self, points, filename) -> bool:
        with open(os.path.join(os.getcwd(), filename), "r") as f:
            if f.read() == points.__repr__():
                return True
            else:
                return False

    def process_transformation(self, tr: FTL.Transformation) -> bool:
        mesh2 = self.mesh.clone()
        points = mesh2.points()
        tr.parent = self.parent
        tr.name = tr.__class__.__name__
        if tr.addResidual:
            res = tr.getResidualTransformation()

        filename = tr.name + ".txt"

        if tr.transformWholeMesh:
            # Transformation implemented a method to  the whole transformation on its own
            points = tr.transformMesh(self.mesh.clone()).points()
        else:
            for pid, pt in enumerate(points):
                if tr.isInScope(pt):
                    vec = np.array([pt[0], pt[1], pt[2], 1])
                    vec = np.dot(tr.getMatrixAt(pt), vec)
                    points[pid][0] = vec[0]
                    points[pid][1] = vec[1]
                    points[pid][2] = vec[2]
                elif tr.addResidual and res.isInScope(pt):
                    vec = np.array([pt[0], pt[1], pt[2], 1])
                    vec = np.dot(res.getMatrixAt(pt), vec)
                    points[pid][0] = vec[0]
                    points[pid][1] = vec[1]
                    points[pid][2] = vec[2]
            return points
        print(
            "-> Comparing {}: {}".format(
                tr.name,
                self.compare_to_file(
                    points, os.path.join(self.data_dir, filename)
                ),
            )
        )

        mesh2.points(points)

    def process_all(self, input, filename):
        self.test_DirBend()
        self.test_LinearTransformation()
        self.test_Spiral()
        self.test_ZBend()

    def test_ZBend(self):
        tr_zbend = FTL.ZBend(-20, 20, -10, 10, 90, FTL.DIR.POSX)
        self.process_transformation(tr_zbend)

    def test_DirBend(self):
        json_db = {
            "points": [
                {"x": -20, "y": 10},
                {"x": 0, "y": -10},
                {"x": 60, "y": -10},
                {"x": 60, "y": 10},
            ],
            "angle": 90,
        }
        tr_dirbend = FTL.DirBend(json_db)
        self.process_transformation(tr_dirbend)

    def test_LinearTransformation(self):
        angle = -pi / 6
        mat = [
            [cos(angle), 0, sin(angle), 0],
            [0, 1, 0, 0],
            [-sin(angle), 0, cos(angle), 0],
        ]
        bounds = box(-60, -10, 60, 10)
        tr_lin = FTL.LinearTransformation(
            mat,
            bounds,
        )
        self.process_transformation(tr_lin)

    def test_Spiral(self):
        json_sp = {
            "points": [
                {"x": -40, "y": 10},
                {"x": -20, "y": -10},
            ],
            "length": 70,
            "dir": "POSX",
            "turns": 1,
        }
        tr_spiral = FTL.Spiral(json_sp)
        self.process_transformation(tr_spiral)

    """def test_(self):

        self.process_transformation(tr_dirbend, "data/Teststrip.stl")
    """
