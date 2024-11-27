from __future__ import annotations

import sys
import os
import math

import shapely as sh
import gmsh


import numpy as np
import vedo as v
from FTL.core.GMSHGeometry import (
    GMSHGeom2D,
    GMSHGeom3D,
    GMSHPhysicalGroup,
    dimtags,
    dimtags2int,
    DimensionError,
)
import pytest

PRECISION_DIGITS = 2


def get_bbox_rounded(dim, tag):
    return [
        round(i, PRECISION_DIGITS)
        for i in gmsh.model.occ.getBoundingBox(dim, tag)
    ]


def get_mass_rounded(dim, tag):
    return round(gmsh.model.occ.getMass(dim, tag), PRECISION_DIGITS)


def round_array(arr):
    def round_list(lst):
        if isinstance(lst[0], (list, tuple, np.ndarray)):
            return [round_list(e) for e in lst]
        else:
            return [round(i, PRECISION_DIGITS) for i in lst]

    return round_list(arr)


def get_mutual_points(geoms1, geoms2):
    elms1 = gmsh.model.get_boundary(
        geoms1.dimtags(), oriented=False, recursive=True
    )
    elms2 = gmsh.model.get_boundary(
        geoms2.dimtags(), oriented=False, recursive=True
    )
    return [x for x in elms1 if x in elms2]


class Test_GMSHGeometry_Utilities:
    def setup_class(self):
        pass

    def test_gmshgeometry_utils_dimtags_default_2d(self):
        tags = [1, 2, 3, 4, 5]
        assert dimtags(tags) == [(2, 1), (2, 2), (2, 3), (2, 4), (2, 5)]

    def test_gmshgeometry_utils_dimtags_3d(self):
        tags = [1, 2, 3, 4, 5]
        assert dimtags(tags, 3) == [(3, 1), (3, 2), (3, 3), (3, 4), (3, 5)]

    def test_gmshgeometry_utils_dimtags2int(self):
        dimtags = [(2, 1), (2, 2), (2, 3), (2, 4), (2, 5)]
        assert dimtags2int(dimtags) == [1, 2, 3, 4, 5]


class Test_GMSHGeom2D:
    def setup_class(self):
        pass

    def test_gmshgeom2d_empty_by_default(self):
        geom = GMSHGeom2D()
        assert len(geom.geoms) == 0
        assert geom.is_empty()
        assert geom.geoms == []

    def test_gmshgeom2d_unnamed_by_default(self):
        geom = GMSHGeom2D()
        assert len(geom.geoms) == 0
        assert geom.is_empty()
        assert geom.name == "Unnamed"

    def test_gmshgeom2d_add_objects_not_empty_get_len(self):
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (1, 1))
        assert len(geom.geoms) == 1
        assert not geom.is_empty()
        geom.add_rectangle((2, 2), (3, 3))
        assert len(geom.geoms) == 2
        assert not geom.is_empty()

    def test_gmshgeom2d_copy(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (1, 1))
        geom.add_rectangle((2, 2), (3, 3))
        copy = geom.copy()
        assert isinstance(copy, GMSHGeom2D)
        assert geom.geoms == [1, 2]
        assert copy.geoms == [3, 4]
        assert round(gmsh.model.occ.getMass(2, 1), 5) == 1
        assert round(gmsh.model.occ.getMass(2, 2), 5) == 1
        assert all(
            [
                e in gmsh.model.occ.getEntities()
                for e in [(2, 1), (2, 2), (2, 3), (2, 4)]
            ]
        )
        bbox_rounded_1 = [
            round(i, 2) for i in gmsh.model.occ.getBoundingBox(2, 3)
        ]
        bbox_rounded_2 = [
            round(i, 2) for i in gmsh.model.occ.getBoundingBox(2, 4)
        ]
        assert bbox_rounded_1 == [0, 0, 0, 1, 1, 0]
        assert bbox_rounded_2 == [2, 2, 0, 3, 3, 0]

    def test_gmshgeom2d_add_objects_dimtags(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (1, 1))
        assert geom.dimtags() == [(2, 1)]
        geom.add_rectangle((2, 2), (3, 3))
        assert geom.dimtags() == [(2, 1), (2, 2)]

    def test_gmshgeom2d_add_polygon_from_list(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
        assert gmsh.model.occ.getEntities(0) == [
            (0, 1),
            (0, 2),
            (0, 3),
            (0, 4),
        ]
        assert gmsh.model.occ.getEntities(1) == [
            (1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
        ]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert gmsh.model.occ.getMass(2, 1) == 1
        assert gmsh.model.occ.getCenterOfMass(2, 1) == (0.5, 0.5, 0)
        assert geom.geoms == [1]

    def test_gmshgeom2d_add_polygon_from_list_bulged(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_polygon(
            [(0, 0, 0.2), (1, 0, 0.2), (1, 1, 0.2), (0, 1, 0.2), (0, 0, 0.2)],
            bulge=True,
        )
        assert gmsh.model.occ.getEntities(0) == [
            (0, 1),
            (0, 2),
            (0, 3),
            (0, 4),
            (0, 5),
            (0, 6),
            (0, 7),
            (0, 8),
        ]
        assert gmsh.model.occ.getEntities(1) == [
            (1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
        ]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 1.27
        assert get_bbox_rounded(2, 1) == [-0.1, -0.1, 0, 1.1, 1.1, 0]
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(0) == [
            (0, 1),
            (0, 2),
            (0, 3),
            (0, 4),
            (0, 5),
            (0, 6),
            (0, 7),
            (0, 8),
        ]

    # TODO: Change that. This test shall fail this way! The mass/area cannot be bigger than 1. Polys need to be reordered.
    def test_gmshgeom2d_add_polygon_with_holes_from_list_wrong_orientation(
        self,
    ):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_polygon(
            [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)],
            [[(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]],
        )
        # geom.render()
        # gmsh.fltk.run()
        # geom.cutout(sh.box(0.25, 0.25, 0.75, 0.75))
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert gmsh.model.occ.getMass(2, 1) == 1.36
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_add_polygon_with_holes_from_list_right_orientation(
        self,
    ):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_polygon(
            [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)],
            [[(0.2, 0.2), (0.2, 0.8), (0.8, 0.8), (0.8, 0.2)]],
        )
        # geom.render()
        # gmsh.fltk.run()
        # geom.cutout(sh.box(0.25, 0.25, 0.75, 0.75))
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert round(gmsh.model.occ.getMass(2, 1), 2) == 0.64
        assert geom.geoms == [1]
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]

    def test_gmshgeom2d_add_shapely_polygon(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_polygon(sh.Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]))
        print(gmsh.model.occ.getEntities())
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert round(gmsh.model.occ.getMass(2, 1), 5) == 1
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_add_shapely_polygon_holes(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_polygon(
            sh.Polygon(
                [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)],
                [
                    [(0.2, 0.2), (0.2, 0.4), (0.4, 0.4), (0.4, 0.2)],
                    [(0.6, 0.6), (0.6, 0.8), (0.8, 0.8), (0.8, 0.6)],
                    [(0.2, 0.6), (0.2, 0.8), (0.4, 0.8), (0.4, 0.6)],
                    [(0.6, 0.2), (0.6, 0.4), (0.8, 0.4), (0.8, 0.2)],
                ],
            )
        )
        print(gmsh.model.occ.getEntities())
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 21)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 21)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert round(gmsh.model.occ.getMass(2, 1), 5) == 0.84
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_add_shapely_polygons_disjunct(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        # geom.add_polygon(sh.Rectangle((0, 0), (1, 1)))
        box1 = sh.geometry.box(-2, -2, -1, -1)
        box2 = sh.geometry.box(1, 1, 2, 2)
        geom.add_polygon(box1)
        print(gmsh.model.occ.getEntities())
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 1.0
        assert get_bbox_rounded(2, 1) == [-2, -2, 0, -1, -1, 0]
        geom.add_polygon(box2)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2)]
        assert get_mass_rounded(2, 2) == 1.0
        assert get_bbox_rounded(2, 2) == [1, 1, 0, 2, 2, 0]
        assert geom.geoms == [1, 2]

    def test_gmshgeom2d_add_shapely_polygons_overlapping(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        # geom.add_polygon(sh.Rectangle((0, 0), (1, 1)))
        box1 = sh.geometry.box(-2, -2, 1, 1)
        box2 = sh.geometry.box(-1, -1, 2, 2)
        geom.add_polygon(box1)
        geom.add_polygon(box2)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2)]
        assert get_mass_rounded(2, 1) == 9.0
        assert get_bbox_rounded(2, 1) == [-2, -2, 0, 1, 1, 0]
        assert get_mass_rounded(2, 2) == 9.0
        assert get_bbox_rounded(2, 2) == [-1, -1, 0, 2, 2, 0]
        assert geom.geoms == [1, 2]

    def test_gmshgeom2d_add_shapely_polygon_rectangle(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_polygon(sh.geometry.box(0, 0, 1, 1))
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 1.0
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_add_rectangle(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (1, 1))
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 1.0
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_get_rectangle(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        tag = geom.geoms[0]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 5)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, tag) == 1.0
        assert get_bbox_rounded(2, tag) == [0, 0, 0, 1, 1, 0]
        assert geom.geoms == [tag]

    def test_gmshgeom2d_add_circle(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_circle((0, 0), 1)
        assert gmsh.model.occ.getEntities(0) == [(0, 1)]
        assert gmsh.model.occ.getEntities(1) == [(1, 1)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 3.14
        assert get_bbox_rounded(2, 1) == [-1.0, -1.0, 0.0, 1.0, 1.0, 0.0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_add_circle_1arg(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_circle(2)
        assert gmsh.model.occ.getEntities(0) == [(0, 1)]
        assert gmsh.model.occ.getEntities(1) == [(1, 1)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 12.57
        assert get_bbox_rounded(2, 1) == [-2.0, -2.0, 0.0, 2.0, 2.0, 0.0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_get_circle(self):
        gmsh.clear()
        c1 = GMSHGeom2D.get_circle(1)
        assert gmsh.model.occ.getEntities(0) == [(0, 1)]
        assert gmsh.model.occ.getEntities(1) == [(1, 1)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 3.14
        assert get_bbox_rounded(2, 1) == [-1.0, -1.0, 0.0, 1.0, 1.0, 0.0]
        assert c1.geoms == [1]

        c2 = GMSHGeom2D.get_circle((1, 1), 1)
        assert gmsh.model.occ.getEntities(0) == [(0, 1), (0, 2)]
        assert gmsh.model.occ.getEntities(1) == [(1, 1), (1, 2)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2)]
        assert round(gmsh.model.occ.getMass(2, 2), 2) == 3.14
        CoM_rounded = [
            round(i, 2) for i in gmsh.model.occ.getCenterOfMass(2, 2)
        ]
        assert CoM_rounded == [1.0, 1.0, 0.0]
        bounding_box_rounded = [
            round(i, 2) for i in gmsh.model.occ.getBoundingBox(2, 2)
        ]
        print(bounding_box_rounded)
        assert bounding_box_rounded == [0.0, 0.0, 0.0, 2.0, 2.0, 0.0]
        assert c2.geoms == [2]

    def test_gmshgeom2d_add_ellipse(self):
        gmsh.clear()
        geom1 = GMSHGeom2D()
        geom2 = GMSHGeom2D()
        geom1.add_ellipse((0, 0), (1, 2))
        geom2.add_ellipse((0, 0), (2, 1), 90)
        assert gmsh.model.occ.getEntities(0) == [(0, 1), (0, 2)]
        assert gmsh.model.occ.getEntities(1) == [(1, 1), (1, 2)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2)]
        assert get_mass_rounded(2, 1) == 6.28
        assert get_bbox_rounded(2, 1) == [-1.0, -2.0, 0.0, 1.0, 2.0, 0.0]
        assert geom1.geoms == [1]
        assert (2, 2) in gmsh.model.occ.getEntities()
        assert get_mass_rounded(2, 2) == 6.28
        assert get_bbox_rounded(2, 2) == [-1.0, -2.0, 0.0, 1.0, 2.0, 0.0]
        assert geom2.geoms == [2]
        # geom1.cutout(geom2)
        # assert geom1.polygons.area <= 0.0001
        # assert not geom2.polygons.equals(circle)

    def test_gmshgeom2d_get_ellipse(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_ellipse((0, 0), (1, 2))
        geom2 = GMSHGeom2D.get_ellipse((0, 0), (2, 1), 90)
        assert gmsh.model.occ.getEntities(0) == [(0, 1), (0, 2)]
        assert gmsh.model.occ.getEntities(1) == [(1, 1), (1, 2)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2)]
        assert get_mass_rounded(2, 1) == 6.28
        assert get_bbox_rounded(2, 1) == [-1.0, -2.0, 0.0, 1.0, 2.0, 0.0]
        assert geom1.geoms == [1]
        assert (2, 2) in gmsh.model.occ.getEntities()
        assert get_mass_rounded(2, 2) == 6.28
        assert get_bbox_rounded(2, 2) == [-1.0, -2.0, 0.0, 1.0, 2.0, 0.0]
        assert geom2.geoms == [2]
        # geom1.cutout(geom2)
        # assert geom1.polygons.area <= 0.0001
        # assert not geom2.polygons.equals(circle)

    def test_gmshgeom2d_add_roundrect(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_roundrect((0, 0), (1, 1), 0.1)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 0.99
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_add_roundrect_circle(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_roundrect((-1, -1), (1, 1), 0.999)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-1.0, -1.0, 0.0, 1.0, 1.0, 0.0]
        assert get_mass_rounded(2, 1) == 3.14
        assert geom.geoms == [1]

    def test_gmshgeom2d_get_roundrect(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_roundrect((0, 0), (1, 1), 0.1)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 0.99
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert geom.geoms == [1]

    # TODO: there is still the "skeleton" inside the offset curve. Maybe remove it in the future?
    def test_gmshgeom2d_add_line_3points(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_line([(0, 0), (1, 1), (2, 1)], 0.1)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 12)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 0.25
        assert get_bbox_rounded(2, 1) == [-0.05, -0.05, 0, 2.05, 1.05, 0]
        assert geom.geoms == [1]

    # TODO: weird middle-point on right outline segment. maybe fix?
    def test_gmshgeom2d_add_line_x(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_line([(-1, 0), (1, 0)], 0.1)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 12)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 11)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 0.21
        assert get_bbox_rounded(2, 1) == [-1.05, -0.05, 0, 1.05, 0.05, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_add_line_y(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_line([(0, -1), (0, 1)], 0.1)
        # geom.plot()
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 12)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 11)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 0.21
        assert get_bbox_rounded(2, 1) == [-0.05, -1.05, 0, 0.05, 1.05, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_get_line(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_line(((0, 0), (1, 1), (2, 1)), 0.1)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 12)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 0.25
        assert get_bbox_rounded(2, 1) == [-0.05, -0.05, 0, 2.05, 1.05, 0]
        assert geom.geoms == [1]

    # TODO: point 2 not attached to (skeleton) curve. Delete?
    def test_gmshgeom2d_add_half_arc(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_arc((1, 0), (0, 1), (-1, 0), 0.1)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 8)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 6)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 0.32
        assert get_bbox_rounded(2, 1) == [-1.05, -0.05, 0, 1.05, 1.05, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_add_quarter_arc(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_arc(
            (1, 0), (math.cos(math.pi / 4), math.sin(math.pi / 4)), (0, 1), 0.1
        )
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 10)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 8)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 0.16
        assert get_bbox_rounded(2, 1) == [-0.05, -0.05, 0, 1.05, 1.05, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_get_arc(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_arc((1, 0), (0, 1), (-1, 0), 0.1)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 8)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 6)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 0.32
        assert get_bbox_rounded(2, 1) == [-1.05, -0.05, 0, 1.05, 1.05, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_fuse_all_overlapping(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (2, 2))
        geom.add_rectangle((1, 1), (3, 3))
        geom.add_rectangle((2, 2), (4, 4))
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2), (2, 3)]
        geom._fuse_all()
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(10, 22)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(10, 22)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 10
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 4, 4, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_fuse_all_disjunct(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (1, 1))
        geom.add_rectangle((2, 2), (3, 3))
        geom.add_rectangle((4, 4), (5, 5))
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2), (2, 3)]
        geom._fuse_all()
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2), (2, 3)]
        assert geom.geoms == [1, 2, 3]

    def test_gmshgeom2d_fuse_all_touching_point(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (1, 1))
        geom.add_rectangle((1, 1), (2, 2))
        geom.add_rectangle((2, 2), (3, 3))
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2), (2, 3)]
        geom._fuse_all()
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 11)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2), (2, 3)]
        assert geom.geoms == [1, 2, 3]

    def test_gmshgeom2d_cutout_gmshgeom2d(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (2, 2))
        geom.cutout(GMSHGeom2D.get_rectangle((0.5, 0.5), (1.5, 1.5)))
        print(gmsh.model.occ.getEntities())
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(5, 13)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(5, 13)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 3.00
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 2, 2, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_cutout_tag_list(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (2, 2))
        assert geom.geoms == [1]
        holes = [
            GMSHGeom2D.get_rectangle((x - 0.3, y - 0.3), (x + 0.3, y + 0.3))
            for x, y in [(0.6, 0.6), (1.4, 0.6), (0.6, 1.4), (1.4, 1.4)]
        ]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 21)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 21)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 6)]
        assert get_mass_rounded(2, 1) == 4
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 2, 2, 0]
        geom.cutout([hole.geoms[0] for hole in holes])
        print(gmsh.model.occ.getEntities())
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(5, 25)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(5, 25)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 2.56
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 2, 2, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_cutout_geom_list(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (2, 2))
        assert geom.geoms == [1]
        holes = [
            GMSHGeom2D.get_rectangle((x - 0.3, y - 0.3), (x + 0.3, y + 0.3))
            for x, y in [(0.6, 0.6), (1.4, 0.6), (0.6, 1.4), (1.4, 1.4)]
        ]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 21)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 21)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 6)]
        assert get_mass_rounded(2, 1) == 4
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 2, 2, 0]
        geom.cutout(holes)
        print(gmsh.model.occ.getEntities())
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(5, 25)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(5, 25)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 2.56
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 2, 2, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_cutout_multiple_geoms(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((-2, -2), (1, 1))
        geom.add_rectangle((-1, -1), (2, 2))
        geom.add_rectangle((-2, -1), (1, 2))
        geom.add_rectangle((-1, -2), (2, 1))
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 17)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 17)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 5)]
        geom.cutout(GMSHGeom2D.get_rectangle((-0.5, -0.5), (0.5, 0.5)))
        # print("Fused: ", geom._fuse_all())
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(17, 25)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(17, 25)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 15
        assert get_bbox_rounded(2, 1) == [-2, -2, 0, 2, 2, 0]
        assert geom.geoms == [1]

    """
    #TODO: Currently unneccesssary. Maybe implement in the future?
    def test_gmshgeom2d_cutout_multigeom_list(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (2, 2))
        assert geom.geoms == [1]
        holes1 = [GMSHGeom2D.get_rectangle((x-0.3, y-0.3), (x+0.3, y+0.3)) for x, y in [(0.6, 0.6), (1.4, 0.6)]]
        holes2 = [GMSHGeom2D.get_rectangle((x - 0.3, y - 0.3), (x + 0.3, y + 0.3)) for x, y in [(0.6, 0.6), (1.4, 0.6)]]
        assert (2, 5) in gmsh.model.occ.getEntities() and (1, 20) in gmsh.model.occ.getEntities()
        assert holes1.geoms == [2, 3]
        assert holes2.geoms == [4, 5]
        geom.cutout([holes1, holes2])
        print(gmsh.model.occ.getEntities())
        assert (2, 1) in gmsh.model.occ.getEntities() and not (2, 2) in gmsh.model.occ.getEntities()
        assert round(gmsh.model.occ.getMass(2, 1)) == 3
        assert gmsh.model.occ.getCenterOfMass(2, 1) == (1, 1, 0)
        bbox_rounded = [
            round(i, 2) for i in gmsh.model.occ.getBoundingBox(2, 1)
        ]
        assert bbox_rounded == [0, 0, 0, 2, 2, 0]
        assert geom.geoms == [1]
    """

    def test_gmshgeom2d_translate(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (1, 1))
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert get_mass_rounded(2, 1) == 1.0
        assert geom.geoms == [1]
        geom.translate(1, 1)
        assert get_bbox_rounded(2, 1) == [1, 1, 0, 2, 2, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_rotate_origin(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_polygon(sh.geometry.box(-1, -1, 1, 1))
        geom.rotate(45)
        assert get_bbox_rounded(2, 1) == [-1.41, -1.41, 0, 1.41, 1.41, 0]
        assert geom.geoms == [1]
        geom.rotate(45)
        assert get_bbox_rounded(2, 1) == [-1, -1, 0, 1, 1, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_rotate_corner(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_polygon(sh.geometry.box(-1, -1, 1, 1))
        geom.rotate(90, (1, 1))
        assert get_bbox_rounded(2, 1) == [1, -1, 0, 3, 1, 0]
        assert geom.geoms == [1]

    def test_gmshgeom2d_extrude_rectangle(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        extrusion = geom.extrude(0.1)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 7)]
        assert gmsh.model.occ.getEntities(3) == [(3, 1)]
        assert get_mass_rounded(3, 1) == 0.1
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]
        assert extrusion.geoms == [1]

    # TODO: unextruded z shift test

    def test_gmshgeom2d_extrude_rectangle_z(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        extrusion = geom.extrude(0.1, zpos=0.2)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 7)]
        assert gmsh.model.occ.getEntities(3) == [(3, 1)]
        assert get_mass_rounded(3, 1) == 0.1
        assert get_bbox_rounded(3, 1) == [0, 0, 0.2, 1, 1, 0.3]
        assert extrusion.geoms == [1]

    def test_gmshgeom2d_make_fusion_disjunct(self):
        gmsh.clear()
        geom1 = GMSHGeom2D().get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D().get_rectangle((2, 2), (3, 3))
        assert geom1.geoms == [1]
        assert geom2.geoms == [2]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 3)]
        assert get_mass_rounded(2, 1) == 1
        assert get_mass_rounded(2, 2) == 1
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert get_bbox_rounded(2, 2) == [2, 2, 0, 3, 3, 0]
        fusion = GMSHGeom2D.make_fusion([geom1, geom2])
        assert isinstance(fusion, GMSHGeom2D)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 3)]
        assert fusion.geoms == [1, 2]

    def test_gmshgeom2d_make_fusion_touching_point(self):
        gmsh.clear()
        geom1 = GMSHGeom2D().get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D().get_rectangle((1, 1), (2, 2))
        assert geom1.geoms == [1]
        assert geom2.geoms == [2]
        fusion = GMSHGeom2D.make_fusion([geom1, geom2])
        assert isinstance(fusion, GMSHGeom2D)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 8)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 3)]
        assert get_mass_rounded(2, 1) == 1
        assert get_mass_rounded(2, 2) == 1
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 1, 1, 0]
        assert get_bbox_rounded(2, 2) == [1, 1, 0, 2, 2, 0]

    def test_gmshgeom2d_make_fusion_overlapping(self):
        gmsh.clear()
        geom1 = GMSHGeom2D().get_rectangle((0, 0), (2, 2))
        geom2 = GMSHGeom2D().get_rectangle((1, 1), (3, 3))
        assert geom1.geoms == [1]
        assert geom2.geoms == [2]
        # geom1.plot()
        fusion = GMSHGeom2D.make_fusion([geom1, geom2])
        # compound.plot()
        assert isinstance(fusion, GMSHGeom2D)
        print(gmsh.model.occ.getEntities())
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(6, 14)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(6, 14)]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_mass_rounded(2, 1) == 7
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 3, 3, 0]

    def test_gmshgeom2d_extrude_rectangles_disjunct(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (1, 1))
        geom.add_rectangle((2, 2), (3, 3))
        extrusion = geom.extrude(0.1)
        assert isinstance(extrusion, GMSHGeom3D)
        assert extrusion.geoms == [1, 2]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 17)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 25)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(3) == [(3, i) for i in range(1, 3)]
        assert get_mass_rounded(3, 1) == 0.1
        assert get_mass_rounded(3, 2) == 0.1
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 2) == [2, 2, 0, 3, 3, 0.1]

    def test_gmshgeom2d_extrude_rectangles_overlapping_unfused(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (2, 2))
        geom.add_rectangle((1, 1), (3, 3))
        assert gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2)]
        extrusion = geom.extrude(0.1, fuse=False)
        # extrusion.plot()
        assert isinstance(extrusion, GMSHGeom3D)
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 17)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 25)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 13)]
        assert gmsh.model.occ.getEntities(3) == [(3, i) for i in range(1, 3)]
        assert get_mass_rounded(3, 1) == 0.4
        assert get_mass_rounded(3, 2) == 0.4
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 2, 2, 0.1]
        assert get_bbox_rounded(3, 2) == [1, 1, 0, 3, 3, 0.1]

    def test_gmshgeom2d_extrude_rectangles_overlapping_fused_by_default(self):
        gmsh.clear()
        geom = GMSHGeom2D()
        geom.add_rectangle((0, 0), (2, 2))
        geom.add_rectangle((1, 1), (3, 3))
        print("Entities before extruding: ", gmsh.model.occ.getEntities())
        gmsh.model.occ.getEntities(2) == [(2, 1), (2, 2)]
        extrusion = geom.extrude(0.1)
        assert extrusion.geoms == [1]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(6, 22)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(6, 30)]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 11)]
        assert gmsh.model.occ.getEntities(3) == [(3, 1)]
        assert get_mass_rounded(3, 1) == 0.7
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 3, 3, 0.1]

    # TODO: test for empty objects/lists in make_fusion


class Test_GMSHGeom3D:
    def setup_class(self):
        pass

    def test_gmshgeom3d_empty_by_default(self):
        gmsh.clear()
        geom = GMSHGeom3D()
        assert geom.geoms == []
        assert geom.is_empty()

    def test_gmshgeom3d_empty_geom2d_throws_exception(self):
        gmsh.clear()
        geom = GMSHGeom3D()
        try:
            print(geom.geom2d)
        except AttributeError:
            return
        assert False

    def test_gmshgeom3d_add_object_gmshgeom2d_single(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        extrusion1 = geom1.extrude(0.1)
        assert extrusion1.geoms == [1]
        geom2 = GMSHGeom2D.get_rectangle((2, 3), (4, 4))
        extrusion2 = geom2.extrude(0.1)
        extrusion1.add_object(extrusion2)
        assert extrusion1.geoms == [1, 2]

    def test_gmshgeom3d_add_object_gmshgeom2d_multi(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        extrusion1 = geom1.extrude(0.1)
        assert extrusion1.geoms == [1]
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        geom2.add_rectangle((4, 4), (5, 5))
        extrusion2 = geom2.extrude(0.1)
        assert extrusion2.geoms == [2, 3]
        extrusion1.add_object(extrusion2)
        assert extrusion1.geoms == [1, 2, 3]

    def test_gmshgeom3d_add_object_int(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        extrusion1 = geom1.extrude(0.1)
        assert extrusion1.geoms == [1]
        geom2 = GMSHGeom2D.get_rectangle((2, 3), (4, 4))
        extrusion2 = geom2.extrude(0.1)
        extrusion1.add_object(extrusion2.geoms[0])
        assert extrusion1.geoms == [1, 2]

    def test_gmshgeom3d_add_objects_get_length(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom1.add_rectangle((2, 2), (3, 3))
        extrusion = geom1.extrude(0.1)
        assert len(extrusion) == 2
        geom2 = GMSHGeom2D.get_rectangle((2, 3), (4, 4))
        extrusion.add_object(geom2.extrude(0.1))
        assert len(extrusion) == 3

    def test_gmshgeom3d_dimtags(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        extrusion = geom1.extrude(0.1)
        assert extrusion._dimtags() == [(3, 1)]
        geom2 = GMSHGeom2D.get_rectangle((2, 3), (4, 4))
        extrusion.add_object(geom2.extrude(0.1))
        assert extrusion._dimtags() == [(3, 1), (3, 2)]

    # TODO: fuse_all() is not implemented in GMSHGeom3D

    def test_gmshgeom3d_geom2d_equal(self):
        gmsh.clear()
        geom2d = GMSHGeom2D()
        geom2d.add_polygon(sh.geometry.box(0, 0, 1, 1))
        geom3d = geom2d.extrude(0.1)
        assert geom3d.geom2d == geom2d

    def test_gmshgeom3d_geom2d_not_equal(self):
        geom2d_1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2d_2 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        # geom2d.add_polygon(sh.geometry.box(2, 2, 3, 3))
        geom3d = geom2d_1.to_3D(0.1)
        assert geom3d.geom2d != geom2d_2

    def test_gmshgeom3d_make_fusion_touching(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 1), (1, 2)).extrude(0.1)
        fusion = GMSHGeom3D.make_fusion([geom1, geom2])
        gmsh.model.occ.synchronize()
        print(gmsh.model.occ.getEntities())
        assert fusion.geoms == [1]
        assert (3, 1) in gmsh.model.occ.getEntities() and not (
            3,
            2,
        ) in gmsh.model.occ.getEntities()
        assert round(gmsh.model.occ.getMass(3, 1), 5) == 0.2
        bbox_rounded = [
            round(i, 2) for i in gmsh.model.occ.getBoundingBox(3, 1)
        ]
        assert bbox_rounded == [0, 0, 0, 1, 2, 0.1]

    def test_gmshgeom3d_make_fusion_disjunct(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3)).extrude(0.1)
        fusion = GMSHGeom3D.make_fusion([geom1, geom2])
        gmsh.model.occ.synchronize()
        print(gmsh.model.occ.getEntities())
        assert fusion.geoms == [1, 2]
        assert (3, 1) in gmsh.model.occ.getEntities() and (
            3,
            2,
        ) in gmsh.model.occ.getEntities()
        assert round(gmsh.model.occ.getMass(3, 1), 5) == 0.1
        assert round(gmsh.model.occ.getMass(3, 2), 5) == 0.1
        bbox_rounded = [
            round(i, 2) for i in gmsh.model.occ.getBoundingBox(3, 1)
        ]
        assert bbox_rounded == [0, 0, 0, 1, 1, 0.1]
        bbox_rounded = [
            round(i, 2) for i in gmsh.model.occ.getBoundingBox(3, 2)
        ]
        assert bbox_rounded == [2, 2, 0, 3, 3, 0.1]

    def test_gmshgeom3d_fragment_single_part(self):
        gmsh.clear()
        board = GMSHGeom2D.get_rectangle((0, 0), (10, 10)).extrude(0.1)
        part = GMSHGeom2D.get_rectangle((2, 2), (8, 8)).extrude(0.1, zpos=0.1)
        board.fragment(part)
        gmsh.model.occ.synchronize()
        assert get_mutual_points(board, part) == [
            (0, i) for i in [9, 10, 11, 12]
        ]

    def test_gmshgeom3d_fragment_two_parts_disjunct(self):
        gmsh.clear()
        board = GMSHGeom2D.get_rectangle((0, 0), (10, 5)).extrude(0.1)
        part1 = GMSHGeom2D.get_rectangle((2, 2), (4, 4)).extrude(0.1, zpos=0.1)
        part2 = GMSHGeom2D.get_rectangle((6, 2), (8, 4)).extrude(0.1, zpos=0.1)
        board.fragment(part1)
        board.fragment(part2)
        gmsh.model.occ.synchronize()
        assert get_mutual_points(board, part1) == [
            (0, i) for i in [9, 10, 11, 12]
        ]
        assert get_mutual_points(board, part2) == [
            (0, i) for i in [17, 18, 19, 20]
        ]
        assert get_mutual_points(part1, part2) == []

    def test_gmshgeom3d_fragment_two_parts_touching(self):
        gmsh.clear()
        board = GMSHGeom2D.get_rectangle((0, 0), (10, 5)).extrude(0.1)
        part1 = GMSHGeom2D.get_rectangle((1, 1), (5, 4)).extrude(0.1, zpos=0.1)
        part2 = GMSHGeom2D.get_rectangle((5, 1), (9, 4)).extrude(0.1, zpos=0.1)
        board.fragment(part1.dimtags() + part2.dimtags())
        gmsh.model.occ.synchronize()
        assert get_mutual_points(board, part1) == [
            (0, i) for i in [9, 10, 13, 14]
        ]
        assert get_mutual_points(board, part2) == [
            (0, i) for i in [10, 11, 12, 13]
        ]
        assert get_mutual_points(part1, part2) == [
            (0, i) for i in [10, 13, 16, 17]
        ]

    """
    def test_gmshgeom3d_fragment_two_parts_overlapping(self):
        gmsh.clear()
        board = GMSHGeom2D.get_rectangle((0, 0), (10, 5)).extrude(0.1)
        part1 = GMSHGeom2D.get_rectangle((1, 1), (5, 4)).extrude(0.1, zpos=0.1)
        part2 = GMSHGeom2D.get_rectangle((4, 1), (8, 4)).extrude(0.1, zpos=0.1)
        board.fragment(part1.dimtags() + part2.dimtags())
        gmsh.model.occ.synchronize()
        gmsh.fltk.run()
        assert get_mutual_points(board, part1) == [
            (0, i) for i in [9, 10, 13, 14]
        ]
        assert get_mutual_points(board, part2) == [
            (0, i) for i in [10, 11, 12, 13]
        ]
        assert get_mutual_points(part1, part2) == [
            (0, i) for i in [10, 13, 16, 17]
        ]
    """

    def test_gmshgeom3d_extrude_tops_single(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        extrusion = geom.extrude(0.1)
        assert extrusion.geoms == [1]
        assert extrusion.surface == [6]
        assert get_bbox_rounded(2, 6) == [0, 0, 0.1, 1, 1, 0.1]

    def test_gmshgeom3d_extrude_tops_double_disjunct(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom.add_rectangle((2, 2), (3, 3))
        extrusion = geom.extrude(0.1)
        gmsh.model.occ.synchronize()
        assert extrusion.geoms == [1, 2]
        assert extrusion.surface == [7, 12]
        assert get_bbox_rounded(2, 7) == [0, 0, 0.1, 1, 1, 0.1]
        assert get_bbox_rounded(2, 12) == [2, 2, 0.1, 3, 3, 0.1]

    def test_gmshgeom3d_extrude_tops_double_touching_point(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom.add_rectangle((1, 1), (2, 2))
        extrusion = geom.extrude(0.1, fuse=False)
        gmsh.model.occ.synchronize()
        assert extrusion.geoms == [1, 2]
        assert extrusion.surface == [7, 12]
        assert get_bbox_rounded(2, 7) == [0, 0, 0.1, 1, 1, 0.1]
        assert get_bbox_rounded(2, 12) == [1, 1, 0.1, 2, 2, 0.1]

    def test_gmshgeom3d_extrude_tops_double_touching_edge(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom.add_rectangle((1, 0), (2, 1))
        extrusion = geom.extrude(0.1, fuse=False)
        gmsh.model.occ.synchronize()
        assert extrusion.geoms == [1, 2]
        assert extrusion.surface == [7, 12]
        assert get_bbox_rounded(2, 7) == [0, 0, 0.1, 1, 1, 0.1]
        assert get_bbox_rounded(2, 12) == [1, 0, 0.1, 2, 1, 0.1]

    def test_gmshphysicalgroup_create_empty(self):
        gmsh.clear()
        group = GMSHPhysicalGroup()
        assert group.dim is None
        assert group.geoms == []
        assert group.dimtags() == []
        assert group.name == ""
        assert group.dimtag is None

    def test_gmshphysicalgroup_create_2d(self):
        gmsh.clear()
        group = GMSHPhysicalGroup(dim=2)
        assert group.dim == 2
        assert group.geoms == []
        assert group.dimtags() == []
        assert group.name == ""
        assert group.dimtag is None

    def test_gmshphysicalgroup_create_geoms_2d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        group = GMSHPhysicalGroup([geom1, geom2])
        assert group.dim == 2
        assert group.geoms == [geom1, geom2]
        assert group.dimtags() == [(2, 1), (2, 2)]

    def test_gmshphysicalgroup_create_geoms_3d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        group = GMSHPhysicalGroup([extrusion1, extrusion2])
        assert group.dim == 3
        assert group.geoms == [extrusion1, extrusion2]
        assert group.dimtags() == [(3, 1), (3, 2)]

    def test_gmshphysicalgroup_add_single_elements_2d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        group = GMSHPhysicalGroup()
        assert group.geoms == []
        assert group.dimtags() == []
        group.add(geom1)
        assert group.geoms == [geom1]
        assert group.dimtags() == [(2, 1)]
        group.add(geom2)
        assert group.geoms == [geom1, geom2]
        assert group.dimtags() == [(2, 1), (2, 2)]

    def test_gmshphysicalgroup_add_single_elements_3d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        group = GMSHPhysicalGroup()
        assert group.geoms == []
        assert group.dimtags() == []
        group.add(extrusion1)
        assert group.geoms == [extrusion1]
        assert group.dimtags() == [(3, 1)]
        group.add(extrusion2)
        assert group.geoms == [extrusion1, extrusion2]
        assert group.dimtags() == [(3, 1), (3, 2)]

    def test_gmshphysicalgroup_add_element_list_2d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        group = GMSHPhysicalGroup()
        print("Groups: ", group.geoms)
        assert group.geoms == []
        assert group.dimtags() == []
        group.add([geom1, geom2])
        assert group.geoms == [geom1, geom2]
        assert group.dimtags() == [(2, 1), (2, 2)]

    def test_gmshphysicalgroup_add_element_list_3d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        group = GMSHPhysicalGroup()
        print("Groups: ", group.geoms)
        assert group.geoms == []
        assert group.dimtags() == []
        group.add([extrusion1, extrusion2])
        assert group.geoms == [extrusion1, extrusion2]
        assert group.dimtags() == [(3, 1), (3, 2)]

    def test_gmshphysicalgroup_add_2d_element_to_3d_group(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        extrusion1 = geom1.extrude(0.1)
        group = GMSHPhysicalGroup()
        group.add(extrusion1)
        try:
            group.add(geom1)
        except DimensionError:
            return
        assert False

    def test_gmshphysicalgroup_add_3d_element_to_2d_group(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        extrusion1 = geom1.extrude(0.1)
        group = GMSHPhysicalGroup()
        group.add(geom1)
        try:
            group.add(extrusion1)
        except DimensionError:
            return
        assert False

    def test_gmshphysicalgroup_remove_element_from_geom_2d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        gmsh.model.occ.synchronize()
        group = GMSHPhysicalGroup([geom1, geom2])
        group.remove(geom1)
        assert group.geoms == [geom2]
        assert group.dimtags() == [(2, 2)]

    def test_gmshphysicalgroup_remove_element_from_geom_3d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        gmsh.model.occ.synchronize()
        group = GMSHPhysicalGroup([extrusion1, extrusion2])
        group.remove(extrusion1)
        assert group.geoms == [extrusion2]
        assert group.dimtags() == [(3, 2)]

    def test_gmshphysicalgroup_remove_element_from_geoms_2d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        geom3 = GMSHGeom2D.get_rectangle((4, 4), (5, 5))
        gmsh.model.occ.synchronize()
        group = GMSHPhysicalGroup([geom1, geom2, geom3])
        group.remove((geom1, geom2))
        assert group.geoms == [geom3]
        assert group.dimtags() == [(2, 3)]

    def test_gmshphysicalgroup_remove_element_from_geoms_3d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        geom3 = GMSHGeom2D.get_rectangle((4, 4), (5, 5))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        extrusion3 = geom3.extrude(0.1)
        gmsh.model.occ.synchronize()
        group = GMSHPhysicalGroup([extrusion1, extrusion2, extrusion3])
        group.remove((extrusion1, extrusion2))
        assert group.geoms == [extrusion3]
        assert group.dimtags() == [(3, 3)]

    def test_gmshphysicalgroup_remove_element_from_dimtag_2d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        gmsh.model.occ.synchronize()
        group = GMSHPhysicalGroup([geom1, geom2])
        group.remove_dimtags(geom1.dimtags())
        assert group.geoms == [geom2]
        assert group.dimtags() == [(2, 2)]

    def test_gmshphysicalgroup_remove_element_from_dimtag_3d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        gmsh.model.occ.synchronize()
        group = GMSHPhysicalGroup([extrusion1, extrusion2])
        group.remove_dimtags(extrusion1.dimtags())
        assert group.geoms == [extrusion2]
        assert group.dimtags() == [(3, 2)]

    def test_gmshphysicalgroup_commit_2d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        gmsh.model.occ.synchronize()
        group = GMSHPhysicalGroup([geom1, geom2], name="Test")
        assert gmsh.model.get_physical_groups() == []
        group.commit()
        assert gmsh.model.get_physical_groups() == [(2, 1)]
        assert gmsh.model.get_physical_name(2, 1) == "Test"

    def test_gmshphysicalgroup_commit_3d(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        gmsh.model.occ.synchronize()
        group = GMSHPhysicalGroup([extrusion1, extrusion2], name="Test")
        assert gmsh.model.get_physical_groups() == []
        group.commit()
        assert gmsh.model.get_physical_groups() == [(3, 1)]
        assert gmsh.model.get_physical_name(3, 1) == "Test"

    def test_gmshphysicalgroup_commit_coexistence_different_names(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        gmsh.model.occ.synchronize()
        group_2d = GMSHPhysicalGroup([geom1, geom2], name="Test_2D")
        group_3d = GMSHPhysicalGroup([extrusion1, extrusion2], name="Test_3D")
        assert gmsh.model.get_physical_groups() == []
        group_2d.commit()
        assert gmsh.model.get_physical_groups() == [(2, 1)]
        group_3d.commit()
        assert gmsh.model.get_physical_groups() == [(2, 1), (3, 2)]
        assert gmsh.model.get_physical_name(2, 1) == "Test_2D"
        assert gmsh.model.get_physical_name(3, 2) == "Test_3D"

    def test_gmshphysicalgroup_commit_coexistence_same_names(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        gmsh.model.occ.synchronize()
        group_2d = GMSHPhysicalGroup([geom1, geom2], name="Test")
        group_3d = GMSHPhysicalGroup([extrusion1, extrusion2], name="Test")
        assert gmsh.model.get_physical_groups() == []
        group_2d.commit()
        assert gmsh.model.get_physical_groups() == [(2, 1)]
        group_3d.commit()
        assert gmsh.model.get_physical_groups() == [(2, 1), (3, 2)]
        assert gmsh.model.get_physical_name(2, 1) == "Test"
        assert gmsh.model.get_physical_name(3, 2) == "Test"

    def test_gmshphysicalgroup_commit_coexistence_no_names(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        gmsh.model.occ.synchronize()
        group_2d = GMSHPhysicalGroup([geom1, geom2])
        group_3d = GMSHPhysicalGroup([extrusion1, extrusion2])
        assert gmsh.model.get_physical_groups() == []
        group_2d.commit()
        assert gmsh.model.get_physical_groups() == [(2, 1)]
        group_3d.commit()
        assert gmsh.model.get_physical_groups() == [(2, 1), (3, 2)]
        assert gmsh.model.get_physical_name(2, 1) == ""
        assert gmsh.model.get_physical_name(3, 2) == ""

    """
    def test_gmshgeom2d_fix_list(self):
        geom = GMSHGeom2D()
        assert geom._fix_list([]) == []
        assert geom._fix_list([1, 2, 3, 4]) == [1, 2, 3, 4]
        assert geom._fix_list([1, 2, 3, 4, 1]) == [1, 2, 3, 4]
        assert geom._fix_list([(1, 2), (3, 4)]) == [(1, 2), (3, 4)]
        assert geom._fix_list([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4)]
        assert geom._fix_list([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4), (1, 2)]"""
