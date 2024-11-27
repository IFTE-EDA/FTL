from __future__ import annotations

import sys
import os
import math

import shapely as sh


import numpy as np
import vedo as v
from FTL.core.FTLGeometry import FTLGeom2D, FTLGeom3D


class Test_FTLGeom2D:
    def setup_class(self):
        pass

    def test_ftlgeom2d_empty_by_default(self):
        geom = FTLGeom2D()
        assert len(geom.polygons.geoms) == 0
        assert geom.is_empty()

    def test_ftlgeom2d_add_polygon_from_list(self):
        geom = FTLGeom2D()
        geom.add_polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
        assert geom.polygons.equals(sh.geometry.box(0, 0, 1, 1))

    def test_ftlgeom2d_add_shapely_polygon(self):
        geom = FTLGeom2D()
        geom.add_polygon(sh.Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]))
        assert geom.polygons.equals(sh.geometry.box(0, 0, 1, 1))

    def test_ftlgeom2d_add_polygon_with_holes_from_list(self):
        geom = FTLGeom2D()
        geom.add_polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
        geom.cutout(sh.box(0.25, 0.25, 0.75, 0.75))
        assert geom.polygons.equals(
            sh.geometry.box(0, 0, 1, 1).difference(
                sh.box(0.25, 0.25, 0.75, 0.75)
            )
        )

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

    def test_ftlgeom2d_add_shapely_polygon_rectangle(self):
        geom = FTLGeom2D()
        geom.add_polygon(sh.geometry.box(0, 0, 1, 1))
        assert geom.polygons.equals(sh.geometry.box(0, 0, 1, 1))

    def test_ftlgeom2d_add_rectangle(self):
        geom = FTLGeom2D()
        geom.add_rectangle((0, 0), (1, 1))
        assert geom.polygons.equals(sh.geometry.box(0, 0, 1, 1))

    def test_ftlgeom2d_get_rectangle(self):
        assert FTLGeom2D.get_rectangle((0, 0), (1, 1)).polygons.equals(
            sh.geometry.box(0, 0, 1, 1)
        )

    def test_ftlgeom2d_add_circle(self):
        geom = FTLGeom2D()
        geom.add_circle((0, 0), 1)
        assert geom.polygons.equals(sh.geometry.Point(0, 0).buffer(1))

    def test_ftlgeom2d_add_circle_1arg(self):
        geom = FTLGeom2D()
        geom.add_circle(2)
        assert geom.polygons.equals(sh.geometry.Point(0, 0).buffer(2))

    def test_ftlgeom2d_get_circle(self):
        assert FTLGeom2D.get_circle(1).polygons.equals(
            sh.geometry.Point(0, 0).buffer(1)
        )
        assert FTLGeom2D.get_circle((1, 1), 1).polygons.equals(
            sh.geometry.Point(1, 1).buffer(1)
        )

    def test_ftlgeom2d_add_ellipse(self):
        circle = sh.geometry.Point(0, 0).buffer(1)
        geom1 = FTLGeom2D()
        geom2 = FTLGeom2D()
        geom1.add_ellipse((0, 0), (1, 2))
        geom2.add_ellipse((0, 0), (2, 1), 90)
        geom1.cutout(geom2)
        assert geom1.polygons.area <= 0.0001
        assert not geom2.polygons.equals(circle)

    def test_ftlgeom2d_get_ellipse(self):
        circle = sh.geometry.Point(0, 0).buffer(1)
        geom1 = FTLGeom2D.get_ellipse((0, 0), (1, 2))
        geom2 = FTLGeom2D.get_ellipse((0, 0), (2, 1), 90)
        geom1.cutout(geom2)
        assert geom1.polygons.area <= 0.0001
        assert not geom2.polygons.equals(circle)

    def test_ftlgeom2d_add_roundrect(self):
        geom = FTLGeom2D()
        geom.add_roundrect((0, 0), (1, 1), 0.1)
        bxmin, bymin, bxmax, bymax = geom.polygons.bounds
        bxmin = round(bxmin, 10)
        bymin = round(bymin, 10)
        bxmax = round(bxmax, 10)
        bymax = round(bymax, 10)
        assert (bxmin, bymin, bxmax, bymax) == (0, 0, 1, 1)
        assert geom.polygons.area < 1
        assert geom.polygons.area > 0.99
        assert geom.polygons.equals(
            sh.geometry.box(0.1, 0.1, 0.9, 0.9).buffer(0.1)
        )

    def test_ftlgeom2d_get_roundrect(self):
        geom = FTLGeom2D.get_roundrect((0, 0), (1, 1), 0.1)
        bxmin, bymin, bxmax, bymax = geom.polygons.bounds
        bxmin = round(bxmin, 10)
        bymin = round(bymin, 10)
        bxmax = round(bxmax, 10)
        bymax = round(bymax, 10)
        assert (bxmin, bymin, bxmax, bymax) == (0, 0, 1, 1)
        assert round(geom.polygons.area, 10) == 0.9913654849
        assert geom.polygons.equals(
            sh.geometry.box(0.1, 0.1, 0.9, 0.9).buffer(0.1)
        )

    def test_ftlgeom2d_add_line(self):
        geom = FTLGeom2D()
        geom.add_line(((0, 0), (1, 1), (2, 1)), 0.1)
        # geom.plot()
        assert round(geom.polygons.area, 10) == 0.249207365
        assert geom.polygons.equals(
            sh.geometry.LineString([(0, 0), (1, 1), (2, 1)]).buffer(0.05)
        )

    def test_ftlgeom2d_get_line(self):
        geom = FTLGeom2D.get_line(((0, 0), (1, 1)), 0.1)
        assert round(geom.polygons.area, 10) == 0.1492627275
        assert geom.polygons.equals(
            sh.geometry.LineString([(0, 0), (1, 1)]).buffer(0.05)
        )

    def test_ftlgeom2d_add_half_arc(self):
        geom = FTLGeom2D()
        geom.add_arc((1, 0), (0, 1), (-1, 0), 0.1)
        assert round(geom.polygons.area, 10) == 0.321909497
        # assure orientation
        clip_rect = sh.geometry.box(-1, -0.1, 1, -1)
        geom.cutout(clip_rect)
        assert round(geom.polygons.area, 10) == 0.321909497

    def test_ftlgeom2d_add_quarter_arc(self):
        geom = FTLGeom2D()
        geom.add_arc(
            (1, 0), (math.cos(math.pi / 4), math.sin(math.pi / 4)), (0, 1), 0.1
        )
        assert round(geom.polygons.area, 10) == 0.1648730949
        # assure orientation
        clip_rect = sh.geometry.box(-0.1, -0.1, 1.1, 1.1)
        geom.cutout(clip_rect)
        assert round(geom.polygons.area, 10) == 0

    def test_ftlgeom2d_get_arc(self):
        geom = FTLGeom2D.get_arc((1, 0), (0, 1), (-1, 0), 0.1)
        assert round(geom.polygons.area, 10) == 0.321909497

    def test__ftlgeom2d_cutout(self):
        geom = FTLGeom2D()
        geom.add_polygon(sh.geometry.box(0, 0, 2, 2))
        geom.cutout(sh.geometry.box(0.5, 0.5, 1.5, 1.5))
        assert geom.polygons.equals(
            sh.geometry.box(0, 0, 2, 2).difference(
                sh.geometry.box(0.5, 0.5, 1.5, 1.5)
            )
        )

    def test_ftlgeom2d_translate(self):
        geom = FTLGeom2D()
        geom.add_polygon(sh.geometry.box(0, 0, 1, 1))
        geom.translate(1, 1)
        assert geom.polygons.equals(sh.geometry.box(1, 1, 2, 2))

    def test_ftlgeom2d_rotate_origin(self):
        geom = FTLGeom2D()
        geom.add_polygon(sh.geometry.box(0, 0, 1, 1))
        geom.rotate(90)
        assert geom.polygons.equals(sh.geometry.box(-1, 1, 0, 0))

    def test_ftlgeom2d_rotate_corner(self):
        geom = FTLGeom2D()
        geom.add_polygon(sh.geometry.box(0, 0, 1, 1))
        geom.rotate(90, (1, 1))
        assert geom.polygons.equals(sh.geometry.box(1, 1, 2, 0))

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
                [1, 0, 0.1],
                [1, 1, 0.1],
                [0, 1, 0.1],
                [0, 0, 0.1],
            ]
        )
        # assert len(extrusion) == 1
        print(extrusion.vertices)
        print(comp)
        assert comp.__str__() == extrusion.vertices.__str__()

    def test_ftlgeom2d_extrude_rectangle_z(self):
        geom = FTLGeom2D()
        box1 = sh.geometry.box(0, 0, 1, 1)
        geom.add_polygon(box1)
        extrusion = geom.extrude(0.1, zpos=0.2)
        comp = np.array(
            [
                [1, 0, 0.2],
                [1, 1, 0.2],
                [0, 1, 0.2],
                [0, 0, 0.2],
                [1, 0, 0.3],
                [1, 1, 0.3],
                [0, 1, 0.3],
                [0, 0, 0.3],
            ]
        )
        # assert len(extrusion) == 1
        print(extrusion.vertices)
        print(comp)
        assert comp.__str__() == extrusion.vertices.__str__()

    def test_ftlgeom2d_make_compound(self):
        geom1 = FTLGeom2D()
        geom1.add_polygon(sh.geometry.box(0, 0, 1, 1))
        geom2 = FTLGeom2D()
        geom2.add_polygon(sh.geometry.box(2, 2, 3, 3))
        compound = FTLGeom2D.make_fusion([geom1, geom2])
        assert isinstance(compound, FTLGeom2D)
        assert len(compound.polygons.geoms) == 2
        assert compound.polygons.equals(
            sh.MultiPolygon([geom1.polygons, geom2.polygons])
        )

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
                [1.0, 0.0, 0.0],
                [1.0, 1.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0],
                [3.0, 2.0, 0.0],
                [3.0, 3.0, 0.0],
                [2.0, 3.0, 0.0],
                [2.0, 2.0, 0.0],
                [1.0, 0.0, 0.1],
                [1.0, 1.0, 0.1],
                [0.0, 1.0, 0.1],
                [0.0, 0.0, 0.1],
                [3.0, 2.0, 0.1],
                [3.0, 3.0, 0.1],
                [2.0, 3.0, 0.1],
                [2.0, 2.0, 0.1],
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
                [1.0, 0.0, 0.0],
                [1.0, 1.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.1],
                [1.0, 1.0, 0.1],
                [0.0, 1.0, 0.1],
                [0.0, 0.0, 0.1],
            ]
        )
        comp2 = np.array(
            [
                [3.0, 2.0, 0.0],
                [3.0, 3.0, 0.0],
                [2.0, 3.0, 0.0],
                [2.0, 2.0, 0.0],
                [3.0, 2.0, 0.1],
                [3.0, 3.0, 0.1],
                [2.0, 3.0, 0.1],
                [2.0, 2.0, 0.1],
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
                [2.0, 0.0, 0.0],
                [2.0, 1.0, 0.0],
                [3.0, 1.0, 0.0],
                [3.0, 3.0, 0.0],
                [1.0, 3.0, 0.0],
                [1.0, 2.0, 0.0],
                [0.0, 2.0, 0.0],
                [0.0, 0.0, 0.0],
                [2.0, 0.0, 0.1],
                [2.0, 1.0, 0.1],
                [3.0, 1.0, 0.1],
                [3.0, 3.0, 0.1],
                [1.0, 3.0, 0.1],
                [1.0, 2.0, 0.1],
                [0.0, 2.0, 0.1],
                [0.0, 0.0, 0.1],
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
                [1.0, 0.0, 0.0],
                [1.0, 1.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.1],
                [1.0, 1.0, 0.1],
                [0.0, 1.0, 0.1],
                [0.0, 0.0, 0.1],
            ]
        )
        comp2 = np.array(
            [
                [3.0, 2.0, 0.0],
                [3.0, 3.0, 0.0],
                [2.0, 3.0, 0.0],
                [2.0, 2.0, 0.0],
                [3.0, 2.0, 0.1],
                [3.0, 3.0, 0.1],
                [2.0, 3.0, 0.1],
                [2.0, 2.0, 0.1],
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
