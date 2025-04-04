from pathlib import Path
import os.path
import sys
import numpy as np
import pytest
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


class Test_Transformations:
    data_dir = Path(__file__).parent.parent / "data"
    # test_data_dir = Path(__file__).parent / "data"
    test_data_dir = Path(__file__).parent.parent / "tests" / "data"

    def setup_class(self):
        self.parent = ParentDummy()
        print(self.data_dir)
        test_filename = str(self.data_dir / "Teststrip.stl")
        print("Loading {}".format(test_filename))
        self.mesh = v.load(test_filename).clean()

    def compare_to_file(self, points, filename) -> bool:
        with open(self.test_data_dir / filename, "r") as f:
            comp = f.read()
            if comp == np.round(points, 5).__repr__():
                print("Compare successful")
                return True
            else:
                print(
                    "\n\n{}\n\n===========================================\n\n{}\n".format(
                        comp, points.__repr__()
                    )
                )
                return False

    def process_transformation(self, tr: FTL.Transformation) -> bool:
        mesh2 = self.mesh.clone()
        points = mesh2.points()
        tr.parent = self.parent
        tr.name = tr.__class__.__name__
        if tr.addResidual:
            res = tr.get_residual_transformation()

        filename = tr.name + ".txt"

        if tr.transformWholeMesh:
            # Transformation implemented a method to  the whole transformation on its own
            mesh = tr.transform_mesh(self.mesh.clone())
            """axs = v.Axes(
                [mesh],
                xygrid=True,
                number_of_divisions=10,
                xrange=[-50, 65],
                yrange=[-55, 5],
                zrange=[0, 30],
            )"""
            # v.show(mesh.wireframe())#, axs, elevation=-70, zoom=1.8, size=(960*2, 535*2), screenshot="Render_out.jpg")#, axes=11)
            points = mesh.points()
        else:
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
            # return points
        # v.show(mesh.wireframe())
        ret = self.compare_to_file(points, filename)
        print(
            "-> Comparing {}: {}".format(
                tr.name,
                ret,
            )
        )
        assert ret

    def process_all(self):
        self.test_DirBend()
        self.test_LinearTransformation()
        self.test_Spiral()
        self.test_ZBend()

    def test_ZBend(self):
        tr_zbend = FTL.ZBend(-20, 20, -10, 10, 90, FTL.DIR.POSX)
        self.process_transformation(tr_zbend)

    # @pytest.mark.skip("Discarded for now")
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

    # @pytest.mark.skip("Discarded for now")
    def test_DirBendNew(self):
        json_db = {
            "points": [
                {"x": -15, "y": 5},
                {"x": -5, "y": -5},
                {"x": 60, "y": -5},
                {"x": 60, "y": 5},
            ],
            "angle": 90,
        }
        tr_dirbend = FTL.DirBendNew(json_db)
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

    # @pytest.mark.skip("Discarded for now")
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


if __name__ == "__main__":
    tester = Test_Transformations()
    tester.setup_class()
    tester.process_all()
