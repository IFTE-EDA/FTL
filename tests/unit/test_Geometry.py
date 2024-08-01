from __future__ import annotations

import sys
import os

import shapely as sh


import numpy as np
import vedo as v
from FTL.core.Geometry import FTLGeom2D, FTLGeom3D


class Test_FTLGeom2D:
    def setup_class(self):
        pass

    def test_ftlgeom2d_empty_by_default(self):
        geom = FTLGeom2D()
        assert len(geom.polygons.geoms) == 0
        assert geom.is_empty()

    def test_ftlgeom2d_add_shapely_polygons_disjunct(self):
        geom = FTLGeom2D()
        # geom.add_polygon(sh.Rectangle((0, 0), (1, 1)))
        box1 = sh.geometry.box(0, 0, 1, 1)
        box2 = sh.geometry.box(2, 2, 3, 3)
        geom.add_polygon(box1)
        assert box1.equals(geom.polygons)
        geom.add_polygon(box2)
        # print(geom.polygons[1].exterior.coords.xy)
        assert box2.equals(geom.polygons.geoms[1])
        assert len(geom.polygons.geoms) == 2

    def test_ftlgeom2d_add_shapely_polygons_overlapping(self):
        geom = FTLGeom2D()
        # geom.add_polygon(sh.Rectangle((0, 0), (1, 1)))
        box1 = sh.geometry.box(0, 0, 2, 2)
        box2 = sh.geometry.box(1, 1, 3, 3)
        geom.add_polygon(box1)
        geom.add_polygon(box2)
        assert isinstance(geom.polygons, sh.Polygon)
        assert box2.union(box1).equals(geom.polygons)

    def test_ftlgeom2d_add_circle(self):
        geom = FTLGeom2D()
        geom.add_circle((0, 0), 1)
        assert geom.polygons.equals(sh.geometry.Point(0, 0).buffer(1))

    def test_ftlgeom2d_add__1arg(self):
        geom = FTLGeom2D()
        geom.add_circle(2)
        assert geom.polygons.equals(sh.geometry.Point(0, 0).buffer(2))

    def test_ftlgeom2d_translate(self):
        geom = FTLGeom2D()
        geom.add_polygon(sh.geometry.box(0, 0, 1, 1))
        geom.translate(1, 1)
        assert geom.polygons.equals(sh.geometry.box(1, 1, 2, 2))

    def test_ftlgeom2d_extrude_rectangle(self):
        geom = FTLGeom2D()
        box1 = sh.geometry.box(0, 0, 1, 1)
        geom.add_polygon(box1)
        extrusion = geom.extrude(0.1)
        comp = np.array(
            [
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 0],
                [1, 0, 0],
                [1, 0, 0.1],
                [1, 1, 0.1],
                [0, 1, 0.1],
                [0, 0, 0.1],
                [1, 0, 0.1],
            ]
        )
        # assert len(extrusion) == 1
        print(extrusion.vertices)
        print(comp)
        assert comp.__str__() == extrusion.vertices.__str__()

    def test_ftlgeom2d_extrude_rectangles_disjunct(self):
        geom = FTLGeom2D()
        box1 = sh.geometry.box(0, 0, 1, 1)
        box2 = sh.geometry.box(2, 2, 3, 3)
        geom.add_polygon(box1)
        geom.add_polygon(box2)
        extrusion = geom.extrude(0.1)
        assert isinstance(extrusion, v.Mesh)
        comp = np.array(
            [
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 0],
                [1, 0, 0],
                [3, 2, 0],
                [3, 3, 0],
                [2, 3, 0],
                [2, 2, 0],
                [3, 2, 0],
                [1, 0, 0.1],
                [1, 1, 0.1],
                [0, 1, 0.1],
                [0, 0, 0.1],
                [1, 0, 0.1],
                [3, 2, 0.1],
                [3, 3, 0.1],
                [2, 3, 0.1],
                [2, 2, 0.1],
                [3, 2, 0.1],
            ]
        )
        print(extrusion.vertices)
        print(comp)
        assert comp.__str__() == extrusion.vertices.__str__()

    def test_ftlgeom2d_extrude_rectangles_unfused(self):
        geom = FTLGeom2D()
        box1 = sh.geometry.box(0, 0, 1, 1)
        box2 = sh.geometry.box(2, 2, 3, 3)
        geom.add_polygon(box1)
        geom.add_polygon(box2)
        extrusion = geom.extrude(0.1, fuse=False)
        assert isinstance(extrusion, list)
        assert isinstance(extrusion[0], v.Mesh)
        assert len(extrusion) == 2
        comp1 = np.array(
            [
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 0],
                [1, 0, 0],
                [1, 0, 0.1],
                [1, 1, 0.1],
                [0, 1, 0.1],
                [0, 0, 0.1],
                [1, 0, 0.1],
            ]
        )
        comp2 = np.array(
            [
                [3, 2, 0],
                [3, 3, 0],
                [2, 3, 0],
                [2, 2, 0],
                [3, 2, 0],
                [3, 2, 0.1],
                [3, 3, 0.1],
                [2, 3, 0.1],
                [2, 2, 0.1],
                [3, 2, 0.1],
            ]
        )
        print(extrusion[0].vertices)
        print(extrusion[1].vertices)
        print(comp1)
        print(comp2)
        assert comp1.__str__() == extrusion[0].vertices.__str__()
        assert comp2.__str__() == extrusion[1].vertices.__str__()

    def test_ftlgeom2d_extrude_rectangles_overlapping(self):
        geom = FTLGeom2D()
        box1 = sh.geometry.box(0, 0, 2, 2)
        box2 = sh.geometry.box(1, 1, 3, 3)
        geom.add_polygon(box1)
        geom.add_polygon(box2)
        extrusion = geom.extrude(0.1)
        assert isinstance(extrusion, v.Mesh)
        comp = np.array(
            [
                [2, 0, 0],
                [0, 0, 0],
                [0, 2, 0],
                [1, 2, 0],
                [1, 3, 0],
                [3, 3, 0],
                [3, 1, 0],
                [2, 1, 0],
                [2, 0, 0],
                [2, 0, 0.1],
                [0, 0, 0.1],
                [0, 2, 0.1],
                [1, 2, 0.1],
                [1, 3, 0.1],
                [3, 3, 0.1],
                [3, 1, 0.1],
                [2, 1, 0.1],
                [2, 0, 0.1],
            ]
        )
        print(extrusion.vertices)
        print(comp)
        assert comp.__str__() == extrusion.vertices.__str__()

    def test_ftlgeom2d_to_3d(self):
        geom = FTLGeom2D()
        box1 = sh.geometry.box(0, 0, 1, 1)
        box2 = sh.geometry.box(2, 2, 3, 3)
        geom.add_polygon(box1)
        geom.add_polygon(box2)
        geom3d = geom.to_3D(0.1)
        assert isinstance(geom3d.objects, list)
        assert isinstance(geom3d.objects[0], v.Mesh)
        assert len(geom3d.objects) == 2
        comp1 = np.array(
            [
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 0],
                [1, 0, 0],
                [1, 0, 0.1],
                [1, 1, 0.1],
                [0, 1, 0.1],
                [0, 0, 0.1],
                [1, 0, 0.1],
            ]
        )
        comp2 = np.array(
            [
                [3, 2, 0],
                [3, 3, 0],
                [2, 3, 0],
                [2, 2, 0],
                [3, 2, 0],
                [3, 2, 0.1],
                [3, 3, 0.1],
                [2, 3, 0.1],
                [2, 2, 0.1],
                [3, 2, 0.1],
            ]
        )
        print(geom3d.objects[0].vertices)
        print(geom3d.objects[1].vertices)
        print(comp1)
        print(comp2)
        assert comp1.__str__() == geom3d.objects[0].vertices.__str__()
        assert comp2.__str__() == geom3d.objects[1].vertices.__str__()


class Test_FTLGeom3D:
    def setup_class(self):
        pass

    def test_ftlgeom3d_empty_by_default(self):
        geom = FTLGeom3D()
        assert geom.objects == []
        assert geom.is_empty()

    def test_ftlgeom3d_add_objects(self):
        geom = FTLGeom3D()
        geom.objects = []
        geom.add_object(v.Box())
        assert len(geom.objects) == 1
        geom.add_object(v.Box())
        assert len(geom.objects) == 2

    def test_ftlgeom3d_geom2d_equal(self):
        geom2d = FTLGeom2D()
        geom2d.add_polygon(sh.geometry.box(0, 0, 1, 1))
        geom2d.add_polygon(sh.geometry.box(2, 2, 3, 3))
        geom3d = geom2d.to_3D(0.1)
        assert geom3d.geom2d.polygons.equals(geom2d.polygons)

    def test_ftlgeom3d_geom2d_not_equal(self):
        geom2d = FTLGeom2D()
        geom2d.add_polygon(sh.geometry.box(0, 0, 1, 1))
        geom2d.add_polygon(sh.geometry.box(2, 2, 3, 3))
        geom3d = geom2d.to_3D(0.1)
        geom2d.add_polygon(sh.geometry.box(3, 3, 4, 4))
        assert not geom3d.geom2d.polygons.equals(geom2d.polygons)

    def test_ftlgeom3d_geom2d_none(self):
        geom3d = FTLGeom3D()
        try:
            geom3d.geom2d
        except AttributeError:
            assert True
        else:
            assert False
