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
    GMSHCompound3D,
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

    def test_gmshgeom2d_ripup(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom.add_rectangle((0, 2), (1, 3))
        geom.add_rectangle((2, 0), (3, 1))
        geom.add_rectangle((2, 2), (3, 3))
        gmsh.model.occ.synchronize()
        parts = geom.ripup()
        assert len(parts) == 4
        assert parts[0].geoms == [1]
        assert parts[1].geoms == [2]
        assert parts[2].geoms == [3]
        assert parts[3].geoms == [4]
        assert parts[0].name == "Unnamed_1"
        assert parts[1].name == "Unnamed_2"
        assert parts[2].name == "Unnamed_3"
        assert parts[3].name == "Unnamed_4"

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

    def test_gmshgeom3d_ripup(self):
        gmsh.clear()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom.add_rectangle((0, 2), (1, 3))
        geom.add_rectangle((2, 0), (3, 1))
        geom.add_rectangle((2, 2), (3, 3))
        gmsh.model.occ.synchronize()
        parts = geom.extrude(0.1).ripup()
        assert len(parts) == 4
        assert parts[0].geoms == [1]
        assert parts[1].geoms == [2]
        assert parts[2].geoms == [3]
        assert parts[3].geoms == [4]
        assert parts[0].name == "Unnamed_1"
        assert parts[1].name == "Unnamed_2"
        assert parts[2].name == "Unnamed_3"
        assert parts[3].name == "Unnamed_4"

    def test_gmshgeom3d_renumber_from_map(self):
        gmsh.clear()
        geom = (
            GMSHGeom2D.get_rectangle((0, 0), (1, 1))
            .add_rectangle((2, 2), (3, 3))
            .extrude(0.1)
        )
        assert geom.geoms == [1, 2]
        geom._renumber_from_map({1: 2, 2: 3})
        assert geom.geoms == [2, 3]

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

    # TODO: make test for fusion of disjunct objects

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

    def test_gmshgeom3d_fragment_two_parts_with_multiple_geoms(self):
        gmsh.clear()
        board = GMSHGeom2D.get_rectangle((0, 0), (5, 5)).extrude(0.1)
        part1 = (
            GMSHGeom2D.get_rectangle((1, 1), (2, 2))
            .add_rectangle((3, 1), (4, 2))
            .extrude(0.1, zpos=0.1)
        )
        part2 = (
            GMSHGeom2D.get_rectangle((1, 3), (2, 4))
            .add_rectangle((3, 3), (4, 4))
            .extrude(0.1, zpos=0.1)
        )
        part_mid = GMSHGeom2D.get_rectangle((1.5, 1.5), (3.5, 3.5)).extrude(
            0.1, zpos=0.1
        )
        assert part1.geoms == [2, 3]
        assert part2.geoms == [4, 5]
        assert part_mid.geoms == [6]
        # TODO: make it possible to use plain objects here
        # board.fragment(part1.dimtags() + part2.dimtags() + part_mid.dimtags())
        GMSHGeom3D.make_compound([board, part1, part2, part_mid])
        gmsh.model.occ.synchronize()
        assert sorted(part1.geoms) == [2, 3, 4, 5]
        assert sorted(part2.geoms) == [6, 7, 8, 9]
        assert sorted(part_mid.geoms) == [3, 5, 7, 8, 10]

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

    def test_gmshphysicalgroup_delete_uncommited(self):
        gmsh.clear()
        GMSHPhysicalGroup.delete_all()
        assert GMSHPhysicalGroup._groups == []
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        group = GMSHPhysicalGroup([geom])
        assert GMSHPhysicalGroup._groups == [group]
        group.delete()
        assert GMSHPhysicalGroup._groups == []

    def test_gmshphysicalgroup_delete_commited(self):
        gmsh.clear()
        GMSHPhysicalGroup.delete_all()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        group = GMSHPhysicalGroup([geom])
        GMSHPhysicalGroup.commit_all()
        assert GMSHPhysicalGroup._groups == [group]
        assert gmsh.model.get_physical_groups() == [(2, 1)]
        group.delete()
        assert GMSHPhysicalGroup._groups == []
        assert gmsh.model.get_physical_groups() == []

    def test_gmshphysicalgroup_delete_all(self):
        gmsh.clear()
        GMSHPhysicalGroup.delete_all()
        assert GMSHPhysicalGroup._groups == []
        assert gmsh.model.get_physical_groups() == []
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        GMSHPhysicalGroup([geom1])
        GMSHPhysicalGroup([geom2])
        assert gmsh.model.get_physical_groups() == []
        GMSHPhysicalGroup.commit_all()
        assert gmsh.model.get_physical_groups() == [(2, 1), (2, 2)]
        GMSHPhysicalGroup.delete_all()
        assert gmsh.model.get_physical_groups() == []
        assert GMSHPhysicalGroup._groups == []

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
        GMSHPhysicalGroup.delete_all()
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
        GMSHPhysicalGroup.delete_all()
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
        GMSHPhysicalGroup.delete_all()
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
        GMSHPhysicalGroup.delete_all()
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
        GMSHPhysicalGroup.delete_all()
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

    def test_gmshphysicalgroup_commit_all(self):
        gmsh.clear()
        GMSHPhysicalGroup.delete_all()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        gmsh.model.occ.synchronize()
        GMSHPhysicalGroup([geom1, geom2], name="Test1")
        GMSHPhysicalGroup([extrusion1, extrusion2], name="Test2")
        assert gmsh.model.get_physical_groups() == []
        GMSHPhysicalGroup.commit_all()
        assert gmsh.model.get_physical_groups() == [(2, 1), (3, 2)]
        assert gmsh.model.get_physical_name(2, 1) == "Test1"
        assert gmsh.model.get_physical_name(3, 2) == "Test2"
        gmsh.model.occ.synchronize()

    def test_gmshphysicalgroup_uncommit(self):
        gmsh.clear()
        GMSHPhysicalGroup.delete_all()
        geom = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        group = GMSHPhysicalGroup([geom], name="Test")
        group.commit()
        assert gmsh.model.get_physical_groups() == [(2, 1)]
        group.uncommit()
        assert gmsh.model.get_physical_groups() == []

    def test_gmshphysicalgroup_fetch_dimtags(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1))
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3))
        geom3 = GMSHGeom2D.get_rectangle((4, 4), (5, 5))
        extrusion1 = geom1.extrude(0.1)
        extrusion2 = geom2.extrude(0.1)
        extrusion3 = geom3.extrude(0.1)
        gmsh.model.occ.synchronize()
        group = GMSHPhysicalGroup([extrusion1, extrusion2, extrusion3])
        gmsh.model.occ.synchronize()
        group.commit()
        assert group.dimtags() == [(3, 1), (3, 2), (3, 3)]
        assert group.fetch_dimtags() == [(3, 1), (3, 2), (3, 3)]

    def test_gmshgeom3d_make_compound_disjunct(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 2), (1, 3)).extrude(0.1)
        geom3 = GMSHGeom2D.get_rectangle((0, 4), (1, 5)).extrude(0.1)
        compound = GMSHGeom3D.make_compound([geom1, geom2, geom3])
        gmsh.model.occ.synchronize()
        assert compound.geoms == [1, 2, 3]
        assert gmsh.model.occ.getEntities(3) == [(3, i) for i in range(1, 4)]
        assert geom1.geoms == [1]
        assert geom2.geoms == [2]
        assert geom3.geoms == [3]
        assert get_mass_rounded(3, 1) == 0.1
        assert get_mass_rounded(3, 2) == 0.1
        assert get_mass_rounded(3, 3) == 0.1
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 2) == [0, 2, 0, 1, 3, 0.1]
        assert get_bbox_rounded(3, 3) == [0, 4, 0, 1, 5, 0.1]

    def test_gmshgeom3d_make_compound_touching(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 1), (1, 2)).extrude(0.1)
        geom3 = GMSHGeom2D.get_rectangle((0, 2), (1, 3)).extrude(0.1)
        compound = GMSHGeom3D.make_compound([geom1, geom2, geom3])
        gmsh.model.occ.synchronize()
        assert compound.geoms == [1, 2, 3]
        assert gmsh.model.occ.getEntities(3) == [(3, i) for i in range(1, 4)]
        assert geom1.geoms == [1]
        assert geom2.geoms == [2]
        assert geom3.geoms == [3]
        assert get_mass_rounded(3, 1) == 0.1
        assert get_mass_rounded(3, 2) == 0.1
        assert get_mass_rounded(3, 3) == 0.1
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 2) == [0, 1, 0, 1, 2, 0.1]
        assert get_bbox_rounded(3, 3) == [0, 2, 0, 1, 3, 0.1]

    def test_gmshgeom3d_make_compound_overlapping_2_parts(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1.5)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 1), (1, 2)).extrude(0.1)
        geom3 = GMSHGeom2D.get_rectangle((0, 2), (1, 3)).extrude(0.1)
        compound = GMSHGeom3D.make_compound([geom1, geom2, geom3])
        gmsh.model.occ.synchronize()
        assert compound.geoms == [3, 4, 5, 6]
        assert gmsh.model.occ.getEntities(3) == [(3, i) for i in range(3, 7)]
        assert geom1.geoms == [4, 5]
        assert geom2.geoms == [5, 6]
        assert geom3.geoms == [3]
        assert get_mass_rounded(3, 3) == 0.1
        assert get_mass_rounded(3, 4) == 0.1
        assert get_mass_rounded(3, 5) == 0.05
        assert get_mass_rounded(3, 6) == 0.05
        assert get_bbox_rounded(3, 3) == [0, 2, 0, 1, 3, 0.1]
        assert get_bbox_rounded(3, 4) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 5) == [0, 1, 0, 1, 1.5, 0.1]
        assert get_bbox_rounded(3, 6) == [0, 1.5, 0, 1, 2, 0.1]

    def test_gmshgeom3d_make_compound_overlapping_3_parts(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (2, 2)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 1), (2, 3)).extrude(0.1)
        geom3 = GMSHGeom2D.get_rectangle((1, 0.5), (3, 2.5)).extrude(0.1)
        compound = GMSHGeom3D.make_compound([geom1, geom2, geom3])
        gmsh.model.occ.synchronize()

        assert sorted(compound.geoms) == [1, 2, 3, 4, 5, 6, 7]
        assert compound.parts == [geom1, geom2, geom3]
        assert sorted(compound.dimtags()) == [(3, i) for i in range(1, 8)]
        assert gmsh.model.occ.getEntities(3) == [(3, i) for i in range(1, 8)]
        assert sorted(geom1.geoms) == [1, 2, 3, 4]
        assert sorted(geom2.geoms) == [2, 4, 5, 6]
        assert sorted(geom3.geoms) == [3, 4, 6, 7]

        assert get_mass_rounded(3, 1) == 0.15
        assert get_mass_rounded(3, 2) == 0.1
        assert get_mass_rounded(3, 3) == 0.05
        assert get_mass_rounded(3, 4) == 0.1
        assert get_mass_rounded(3, 5) == 0.15
        assert get_mass_rounded(3, 6) == 0.05
        assert get_mass_rounded(3, 7) == 0.2

        assert get_bbox_rounded(3, 1) == [0, 0, 0, 2, 1, 0.1]
        assert get_bbox_rounded(3, 2) == [0, 1, 0, 1, 2, 0.1]
        assert get_bbox_rounded(3, 3) == [1, 0.5, 0, 2, 1, 0.1]
        assert get_bbox_rounded(3, 4) == [1, 1, 0, 2, 2, 0.1]
        assert get_bbox_rounded(3, 5) == [0, 2, 0, 2, 3, 0.1]
        assert get_bbox_rounded(3, 6) == [1, 2, 0, 2, 2.5, 0.1]
        assert get_bbox_rounded(3, 7) == [2, 0.5, 0, 3, 2.5, 0.1]

    def test_gmshgeom3d_make_compound_overlapping_2_parts_translate(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1.5)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 1), (1, 2)).extrude(0.1)
        geom3 = GMSHGeom2D.get_rectangle((0, 2), (1, 3)).extrude(0.1)
        compound = GMSHGeom3D.make_compound([geom1, geom2, geom3])
        gmsh.model.occ.synchronize()
        assert get_bbox_rounded(3, 3) == [0, 2, 0, 1, 3, 0.1]
        assert get_bbox_rounded(3, 4) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 5) == [0, 1, 0, 1, 1.5, 0.1]
        assert get_bbox_rounded(3, 6) == [0, 1.5, 0, 1, 2, 0.1]
        compound.translate(1, 2, 3)
        assert get_bbox_rounded(3, 3) == [1, 4, 3, 2, 5, 3.1]
        assert get_bbox_rounded(3, 4) == [1, 2, 3, 2, 3, 3.1]
        assert get_bbox_rounded(3, 5) == [1, 3, 3, 2, 3.5, 3.1]
        assert get_bbox_rounded(3, 6) == [1, 3.5, 3, 2, 4, 3.1]

    def test_gmshgeom3d_make_compound_overlapping_2_parts_translate_after_removing_end_part_rips_it_off_compound(
        self,
    ):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1.5)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 1), (1, 2)).extrude(0.1)
        geom3 = GMSHGeom2D.get_rectangle((0, 2), (1, 3)).extrude(0.1)
        compound = GMSHGeom3D.make_compound([geom1, geom2, geom3])
        gmsh.model.occ.synchronize()
        assert get_bbox_rounded(3, 3) == [0, 2, 0, 1, 3, 0.1]
        assert get_bbox_rounded(3, 4) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 5) == [0, 1, 0, 1, 1.5, 0.1]
        assert get_bbox_rounded(3, 6) == [0, 1.5, 0, 1, 2, 0.1]
        compound.remove(geom3)
        compound.translate(1, 2, 3)
        assert get_bbox_rounded(3, 3) == [0, 2, 0, 1, 3, 0.1]
        assert get_bbox_rounded(3, 4) == [1, 2, 3, 2, 3, 3.1]
        assert get_bbox_rounded(3, 5) == [1, 3, 3, 2, 3.5, 3.1]
        assert get_bbox_rounded(3, 6) == [1, 3.5, 3, 2, 4, 3.1]

    def test_gmshgeom3d_make_compound_overlapping_2_parts_translate_after_removing_middle_part_raises_error(
        self,
    ):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1.5)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 1), (1, 2)).extrude(0.1)
        geom3 = GMSHGeom2D.get_rectangle((0, 2), (1, 3)).extrude(0.1)
        compound = GMSHGeom3D.make_compound([geom1, geom2, geom3])
        gmsh.model.occ.synchronize()
        assert get_bbox_rounded(3, 3) == [0, 2, 0, 1, 3, 0.1]
        assert get_bbox_rounded(3, 4) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 5) == [0, 1, 0, 1, 1.5, 0.1]
        assert get_bbox_rounded(3, 6) == [0, 1.5, 0, 1, 2, 0.1]
        compound.remove(geom2)
        try:
            compound.translate(1, 2, 3)
            gmsh.model.occ.synchronize()
        except Exception:
            return
        assert False

    def test_gmshcompound_create_empty(self):
        gmsh.clear()
        compound = GMSHCompound3D()
        assert compound.geoms == []
        assert compound.dimtags() == []

    def test_gmshcompound_create_geoms(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3)).extrude(0.1)
        compound = GMSHCompound3D([geom1, geom2])
        assert compound.parts == [geom1, geom2]
        assert compound.geoms == [1, 2]
        assert compound.dimtags() == [(3, 1), (3, 2)]

    def test_gmshcompound_add_part(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3)).extrude(0.1)
        compound = GMSHCompound3D([geom1])
        assert compound.parts == [geom1]
        assert compound.geoms == [1]
        assert compound.dimtags() == [(3, 1)]
        compound.add(geom2)
        assert compound.parts == [geom1, geom2]
        assert compound.geoms == [1, 2]
        assert compound.dimtags() == [(3, 1), (3, 2)]

    def test_gmshcompound_add_parts(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3)).extrude(0.1)
        compound = GMSHCompound3D()
        assert compound.parts == []
        assert compound.geoms == []
        assert compound.dimtags() == []
        compound.add([geom1, geom2])
        assert compound.parts == [geom1, geom2]
        assert compound.geoms == [1, 2]
        assert compound.dimtags() == [(3, 1), (3, 2)]

    def test_gmshcompound_remove_part(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((2, 2), (3, 3)).extrude(0.1)
        compound = GMSHCompound3D([geom1, geom2])
        assert compound.parts == [geom1, geom2]
        assert compound.geoms == [1, 2]
        assert compound.dimtags() == [(3, 1), (3, 2)]
        compound.remove(geom1)
        assert compound.parts == [geom2]
        assert compound.geoms == [2]
        assert compound.dimtags() == [(3, 2)]

    def test_gmshcompound_remove_parts(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 1), (1, 2)).extrude(0.1)
        geom3 = GMSHGeom2D.get_rectangle((0, 2), (1, 3)).extrude(0.1)
        compound = GMSHCompound3D([geom1, geom2, geom3])
        assert compound.parts == [geom1, geom2, geom3]
        assert compound.geoms == [1, 2, 3]
        assert compound.dimtags() == [(3, 1), (3, 2), (3, 3)]
        compound.remove([geom1, geom3])
        assert compound.parts == [geom2]
        assert compound.geoms == [2]
        assert compound.dimtags() == [(3, 2)]

    def test_gmshcompound_translate_2_parts_touching_point(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((1, 1), (2, 2)).extrude(0.1)
        compound = GMSHCompound3D([geom1, geom2])
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 2) == [1, 1, 0, 2, 2, 0.1]
        compound.translate(1, 2, 3)
        assert get_bbox_rounded(3, 1) == [1, 2, 3, 2, 3, 3.1]
        assert get_bbox_rounded(3, 2) == [2, 3, 3, 3, 4, 3.1]

    def test_gmshcompound_do_not_translate_part_touching_point(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        GMSHGeom2D.get_rectangle((1, 1), (2, 2)).extrude(0.1)
        compound = GMSHCompound3D([geom1])
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 2) == [1, 1, 0, 2, 2, 0.1]
        compound.translate(1, 2, 3)
        assert get_bbox_rounded(3, 1) == [1, 2, 3, 2, 3, 3.1]
        assert get_bbox_rounded(3, 2) == [1, 1, 0, 2, 2, 0.1]

    def test_gmshcompound_translate_2_parts_touching_edge(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        geom2 = GMSHGeom2D.get_rectangle((0, 1), (1, 2)).extrude(0.1)
        compound = GMSHCompound3D([geom1, geom2])
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 2) == [0, 1, 0, 1, 2, 0.1]
        compound.translate(1, 2, 3)
        assert get_bbox_rounded(3, 1) == [1, 2, 3, 2, 3, 3.1]
        assert get_bbox_rounded(3, 2) == [1, 3, 3, 2, 4, 3.1]

    def test_gmshcompound_do_not_translate_part_touching_edge(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        GMSHGeom2D.get_rectangle((1, 1), (2, 2)).extrude(0.1)
        compound = GMSHCompound3D([geom1])
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]
        assert get_bbox_rounded(3, 2) == [1, 1, 0, 2, 2, 0.1]
        compound.translate(1, 2, 3)
        assert get_bbox_rounded(3, 1) == [1, 2, 3, 2, 3, 3.1]
        assert get_bbox_rounded(3, 2) == [1, 1, 0, 2, 2, 0.1]

    def test_gmshcompound_rotate(self):
        gmsh.clear()
        geom1 = GMSHGeom2D.get_rectangle((0, 0), (1, 1)).extrude(0.1)
        compound = GMSHCompound3D([geom1])
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]
        compound.rotate(90)
        assert get_bbox_rounded(3, 1) == [-1, 0, 0, 0, 1, 0.1]
        compound.rotate(90)
        assert get_bbox_rounded(3, 1) == [-1, -1, 0, 0, 0, 0.1]
        compound.rotate(90)
        assert get_bbox_rounded(3, 1) == [0, -1, 0, 1, 0, 0.1]
        compound.rotate(90)
        assert get_bbox_rounded(3, 1) == [0, 0, 0, 1, 1, 0.1]

    def test_gmshcompound3d_keep_physical_groups(self):
        gmsh.clear()
        pad1 = GMSHGeom2D.get_rectangle((-5, -2), (-1, 2)).extrude(0.1)
        pad2 = GMSHGeom2D.get_rectangle((1, -2), (5, 2)).extrude(0.1)
        trace = GMSHGeom2D.get_rectangle((-3, -0.5), (3, 0.5)).extrude(0.1)
        gPad1 = GMSHPhysicalGroup([pad1], name="Pad1")
        gPad2 = GMSHPhysicalGroup([pad2], name="Pad2")
        gTrace = GMSHPhysicalGroup([trace], name="Trace")
        GMSHGeom3D.make_compound([pad1, pad2, trace])
        gmsh.model.occ.synchronize()
        gPad1.commit()
        gPad2.commit()
        gTrace.commit()
        gmsh.model.occ.synchronize()
        print(gTrace.geoms[0].dimtags())
        print(gTrace.dimtags())
        assert gmsh.model.get_physical_groups() == [(3, 1), (3, 2), (3, 3)]
        assert gmsh.model.get_physical_name(3, 1) == "Pad1"
        assert gmsh.model.get_physical_name(3, 2) == "Pad2"
        assert gmsh.model.get_physical_name(3, 3) == "Trace"

        assert sorted(gmsh.model.get_entities_for_physical_group(3, 1)) == [
            1,
            2,
        ]
        assert sorted(gmsh.model.get_entities_for_physical_group(3, 2)) == [
            3,
            4,
        ]
        assert sorted(gmsh.model.get_entities_for_physical_group(3, 3)) == [
            2,
            4,
            5,
        ]

        assert sorted(gPad1.dimtags()) == [(3, 1), (3, 2)]
        assert sorted(gPad2.dimtags()) == [(3, 3), (3, 4)]
        assert sorted(gTrace.dimtags()) == [(3, 2), (3, 4), (3, 5)]

    """
    def test_gmshgeom2d_fix_list(self):
        geom = GMSHGeom2D()
        assert geom._fix_list([]) == []
        assert geom._fix_list([1, 2, 3, 4]) == [1, 2, 3, 4]
        assert geom._fix_list([1, 2, 3, 4, 1]) == [1, 2, 3, 4]
        assert geom._fix_list([(1, 2), (3, 4)]) == [(1, 2), (3, 4)]
        assert geom._fix_list([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4)]
        assert geom._fix_list([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4), (1, 2)]"""
