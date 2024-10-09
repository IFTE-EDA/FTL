from __future__ import annotations

import sys
import os
import math

import gmsh
import numpy as np

from FTL.parse.DXFParser import DXFParser

PRECISION_DIGITS = 2


def get_bbox_rounded(dim, tag):
    return [
        round(i, PRECISION_DIGITS)
        for i in gmsh.model.occ.getBoundingBox(dim, tag)
    ]


def round_array(arr):
    def round_list(lst):
        if isinstance(lst[0], (list, tuple, np.ndarray)):
            return [round_list(e) for e in lst]
        else:
            return [round(i, PRECISION_DIGITS) for i in lst]

    return round_list(arr)
    # return [round(i, PRECISION_DIGITS) for i in arr]


class Test_DXFParser:
    def setup_class(self):
        pass

    def test_dxfparser_open_non_existent_file(self):
        try:
            DXFParser("data/non_existent_file.dxf")
        except Exception as e:
            print("Exception type: ", type(e))
            print("Assertion: ", isinstance(e, FileNotFoundError))
            if isinstance(e, FileNotFoundError):
                return
        assert False

    def test_dxfparser_layers(self):
        parser = DXFParser("data/layers.dxf")
        print("Layers: ", parser.get_layer_names())
        assert parser.get_layer_names() == [
            "0",
            "Defpoints",
            "TestLayer1",
            "TestLayer2",
            "TestLayer3",
        ]

    def test_dxfparser_get_layer_not_existant(self):
        parser = DXFParser("data/layers.dxf")
        try:
            parser.get_layer("NonExistantLayer")
        except Exception as e:
            print("Exception type: ", type(e))
            print("Assertion: ", isinstance(e, KeyError))
            if isinstance(e, KeyError):
                return
        assert False

    def test_dxfparser_get_layer(self):
        parser = DXFParser("data/layers.dxf")
        print(parser.get_layer("TestLayer1").name)
        assert parser.get_layer("TestLayer1").name == "TestLayer1"
        assert parser.get_layer("TestLayer2").name == "TestLayer2"
        assert parser.get_layer("TestLayer3").name == "TestLayer3"

    def test_dxfparser_lines(self):
        parser = DXFParser("data/lines.dxf")
        print("Layers: ", parser.get_layer_names())
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 4
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LINE"
            print("Start: ", e.dxf.start)
            print("End: ", e.dxf.end)
            assert e.dxf.start in [(0, 0), (10, 0), (10, 10), (0, 10)]
            assert e.dxf.end in [(0, 0), (10, 0), (10, 10), (0, 10)]
            assert e.dxf.thickness == 1
        layer2 = parser.get_layer("width_2")
        assert len(layer2.get_entities()) == 1
        for e in layer2.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LINE"
            print("Start: ", e.dxf.start)
            print("End: ", e.dxf.end)
            assert e.dxf.start == (0, 0)
            assert e.dxf.end == (10, 10)
            assert e.dxf.thickness == 2

    def test_dxfparser_render_lines_unfused(self):
        gmsh.clear()
        parser = DXFParser("data/lines.dxf")
        layer = parser.get_layer("0")
        render = layer.render(fuse=False)
        assert len(render) == 4
        assert render.dimtags() == [(2, 1), (2, 2), (2, 3), (2, 4)]
        assert get_bbox_rounded(2, 1) == [-0.5, -0.5, 0.0, 10.5, 0.5, 0]
        assert get_bbox_rounded(2, 2) == [9.5, -0.5, 0.0, 10.5, 10.5, 0]
        assert get_bbox_rounded(2, 3) == [-0.5, 9.5, 0.0, 10.5, 10.5, 0]
        assert get_bbox_rounded(2, 4) == [-0.5, -0.5, 0.0, 0.5, 10.5, 0]
        layer = parser.get_layer("width_2")
        render = layer.render(fuse=False)
        assert len(render) == 1
        assert render.dimtags() == [(2, 5)]
        assert get_bbox_rounded(2, 5) == [-1, -1, 0.0, 11, 11, 0]

    """
    def test_dxfparser_render_lines_fused(self):
        parser = DXFParser("data/lines.dxf")
        layer = parser.get_layer("0")
        render = layer.render(fuse = True)
        assert len(render) == 1
        assert render.dimtags() == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-0.5, -0.5, 0.0, 10.5, 10.5, 0]
    """

    def test_dxfparser_arc(self):
        parser = DXFParser("data/arc.dxf")
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "ARC"
            assert e.dxf.center == (0, 0)
            assert e.dxf.radius == 5

    def test_dxfparser_render_arc(self):
        gmsh.clear()
        parser = DXFParser("data/arc.dxf")
        layer_0 = parser.get_layer("0")
        render_0 = layer_0.render(fuse=False)
        assert len(render_0) == 1
        assert render_0.dimtags() == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-0.5, -0.5, 0.0, 5.5, 5.5, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 1), 2) == 8.64
        layer_180 = parser.get_layer("180")
        render_180 = layer_180.render(fuse=False)
        assert len(render_180) == 1
        assert render_180.dimtags() == [(2, 2)]
        assert get_bbox_rounded(2, 2) == [-5.5, -0.5, 0.0, 5.5, 5.5, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 2), 2) == 16.49
        layer_270 = parser.get_layer("270")
        render_270 = layer_270.render(fuse=False)
        assert len(render_270) == 1
        assert render_270.dimtags() == [(2, 3)]
        assert get_bbox_rounded(2, 3) == [-5.5, -5.5, 0.0, 5.5, 5.5, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 3), 2) == 24.35
        layer_different_angles = parser.get_layer("different_angles")
        render_different_angles = layer_different_angles.render(fuse=False)
        assert len(render_different_angles) == 1
        assert render_different_angles.dimtags() == [(2, 4)]
        assert get_bbox_rounded(2, 4) == [-5.5, -5.5, 0.0, 5.5, 5.5, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 4), 2) == 24.35
        layer_different_center = parser.get_layer("different_center")
        render_different_center = layer_different_center.render(fuse=False)
        assert len(render_different_center) == 1
        assert render_different_center.dimtags() == [(2, 5)]
        assert get_bbox_rounded(2, 5) == [-0.5, -0.5, 0.0, 10.5, 10.5, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 5), 2) == 24.35

    def test_dxfparser_circle(self):
        parser = DXFParser("data/circle.dxf")
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "CIRCLE"
            assert e.dxf.center == (0, 0)
            assert e.dxf.radius == 5

    def test_dxfparser_render_circle(self):
        gmsh.clear()
        parser = DXFParser("data/circle.dxf")
        layer = parser.get_layer("0")
        render = layer.render(fuse=False)
        assert len(render) == 1
        assert render.dimtags() == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-5.0, -5.0, 0.0, 5.0, 5.0, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 1), 2) == 78.54

    def test_dxfparser_polyline(self):
        parser = DXFParser("data/polyline.dxf")
        layer = parser.get_layer("straight_cw3")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LWPOLYLINE"
            assert not e.is_closed
            assert e.dxf.const_width == 3
            print("Points: ", e.get_points())
            print("Checking points...")
            points_rounded = [(p[0], p[1]) for p in e.get_points()]
            assert points_rounded == [(0, 0), (10, 0), (10, 10), (0, 10)]
            widths = [(p[2], p[3]) for p in e.get_points()]
            assert widths == [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
        layer = parser.get_layer("straight_w2")
        assert len(layer.get_entities()) == 1
        e = layer.get_entities()[0]
        print("Entity: ", e)
        assert e.dxftype() == "LWPOLYLINE"
        assert not e.is_closed
        assert e.dxf.const_width == 0
        print("Points: ", e.get_points())
        print("Checking points...")
        points_rounded = [(p[0], p[1], p[2]) for p in e.get_points()]
        assert points_rounded == [(0, 0, 2), (10, 0, 2)]

    def test_dxfparser_render_polyline(self):
        gmsh.clear()
        parser = DXFParser("data/polyline.dxf")
        layer = parser.get_layer("straight_cw3")
        render = layer.render(fuse=False)
        assert len(render) == 1
        assert render.dimtags() == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-1.5, -1.5, 0.0, 11.5, 1.5, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 1), 2) == 37.07
        layer = parser.get_layer("straight_w2")
        render = layer.render(fuse=False)
        render.plot()
        assert len(render) == 1
        assert render.dimtags() == [(2, 2)]
        assert get_bbox_rounded(2, 2) == [-1.5, -1.5, 0.0, 11.5, 1.5, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 2), 2) == 0.0

    def test_dxfparser_poly(self):
        gmsh.clear()
        parser = DXFParser("data/poly.dxf")
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LWPOLYLINE"
            assert e.is_closed
            print("Points: ", e.get_points())
            print("Checking points...")
            points_rounded = [(p[0], p[1]) for p in e.get_points()]
            assert points_rounded == [(0, 0), (10, 0), (10, 10), (0, 10)]
            print("Checking bulges...")
            bulges = [p[4] for p in e.get_points()]
            assert bulges == [0.0, 0.0, 0.0, 0.0]
            widths = [(p[2], p[3]) for p in e.get_points()]
            assert widths == [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]

    def test_dxfparser_poly_bulge(self):
        parser = DXFParser("data/poly_bulge.dxf")
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LWPOLYLINE"
            print("Points: ", e.get_points())
            print("Checking points...")
            points_rounded = [(p[0], p[1]) for p in e.get_points()]
            assert points_rounded == [(0, 0), (10, 0), (10, 10), (0, 10)]
            print("Checking bulges...")
            bulges = [p[4] for p in e.get_points()]
            assert bulges == [0.5, 0.5, 0.5, 0.5]
            widths = [(p[2], p[3]) for p in e.get_points()]
            assert widths == [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]

    def test_dxfparser_render_poly(self):
        gmsh.clear()
        parser = DXFParser("data/poly.dxf")
        layer = parser.get_layer("0")
        render = layer.render(fuse=False)
        assert len(render) == 1
        assert render.dimtags() == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [0.0, 0.0, 0.0, 10.0, 10.0, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 1), 2) == 100.0

    def test_dxfparser_render_poly_bulge(self):
        gmsh.clear()
        parser = DXFParser("data/poly_bulge.dxf")
        layer = parser.get_layer("0")
        render = layer.render(fuse=False)
        print(parser.get_layer_names())
        assert len(render) == 1
        assert render.dimtags() == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-2.5, -2.5, 0.0, 12.5, 12.5, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 1), 2) == 169.89
        layer = parser.get_layer("1")
        assert len(layer.get_entities()) == 1
        render = layer.render(fuse=False)
        assert len(render) == 1
        assert render.dimtags() == [(2, 2)]
        assert get_bbox_rounded(2, 2) == [0.0, 0.0, 0.0, 10.0, 10.0, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 2), 2) == 73.12

    # def test_dxfparser_render_poly_bulge_fuse(self):
