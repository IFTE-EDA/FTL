from __future__ import annotations

import sys
import os

sys.path.append("../FTL")
sys.path.append(os.path.abspath(os.getcwd()))


import numpy as np
import vedo as v
from FTL.core.Geometry import FTLGeom2D, FTLGeom3D


class Test_FTLGeom2D:
    def setup_class(self):
        pass

    def test_ftlgeom2d_empty_by_default(self):
        geom = FTLGeom2D()
        assert geom.polygons == []

    def test_ftlgeom2d_add_polygons(self):
        geom = FTLGeom2D()
        geom.add_polygon(v.Rectangle((0, 0), (1, 1)))
        assert (
            geom.polygons[0].vertices.sort()
            == np.array([(0, 0), (1, 0), (1, 1), (0, 1)]).sort()
        )
        assert len(geom.polygons) == 1
        geom.add_polygon(v.Rectangle((2, 2), (3, 3)))
        assert (
            geom.polygons[0].vertices.sort()
            == np.array([(2, 2), (3, 2), (3, 3), (2, 3)]).sort()
        )
        assert len(geom.polygons) == 2

    def test_ftlgeom2d_extrude(self):
        geom = FTLGeom2D()
        geom.polygons = []
        geom.add_polygon(v.Rectangle((0, 0), (1, 1)))
        extrusion = geom.extrude(0.1)
        assert len(extrusion) == 1
        print(extrusion[0].vertices)
        assert np.array_equal(
            extrusion[0].vertices.sort(),
            np.array(
                [
                    [0, 0, 0],
                    [1, 0, 0],
                    [1, 1, 0],
                    [0, 1, 0],
                    [0, 0, 0.1],
                    [1, 0, 0.1],
                    [1, 1, 0.1],
                    [0, 1, 0.1],
                ]
            ).sort(),
        )

    def test_ftlgeom2d_to_3d(self):
        geom = FTLGeom2D()
        geom.polygons = []
        geom.add_polygon(v.Rectangle((0, 0), (1, 1)))
        geom.add_polygon(v.Rectangle((2, 2), (3, 3)))
        geom3d = geom.to_3D(0.1)
        assert len(geom3d.objects) == 2
        assert np.array_equal(
            geom3d.objects[0].vertices.sort(),
            np.array(
                [
                    [0, 0, 0],
                    [1, 0, 0],
                    [1, 1, 0],
                    [0, 1, 0],
                    [0, 0, 0.1],
                    [1, 0, 0.1],
                    [1, 1, 0.1],
                    [0, 1, 0.1],
                ]
            ).sort(),
        )
        assert np.array_equal(
            geom3d.objects[1].vertices.sort(),
            np.array(
                [
                    [2, 2, 0],
                    [3, 2, 0],
                    [3, 3, 0],
                    [2, 3, 0],
                    [2, 2, 0.1],
                    [3, 2, 0.1],
                    [3, 3, 0.1],
                    [2, 3, 0.1],
                ]
            ).sort(),
        )

    # def test_ftlgeom2d_extrude(self):


class Test_FTLGeom3D:
    def setup_class(self):
        pass

    def test_ftlgeom3d_empty_by_default(self):
        geom = FTLGeom3D()
        assert geom.objects == []

    # def test_ftlgeom3d_extrude(self):

    if __name__ == "__main__":
        import pytest
        import FTL

        pytest.main(["-v", "-s", "test_Geometry.py"])
