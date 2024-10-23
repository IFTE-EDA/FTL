from __future__ import annotations
import sys
import os
import math
from pathlib import Path

import gmsh
import numpy as np

from FTL.parse.DXFParser import DXFParser


def get_file(file_name: str):
    return Path(__file__).parent.parent / "data" / file_name


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


class Test_DXFParser_Render:
    def setup_class(self):
        pass

    def test_dxfparser_render_lines_unfused(self):
        gmsh.clear()
        parser = DXFParser(get_file("lines.dxf"))
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

    def test_dxfparser_render_arc(self):
        gmsh.clear()
        parser = DXFParser(get_file("arc.dxf"))
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

    def test_dxfparser_render_circle(self):
        gmsh.clear()
        parser = DXFParser(get_file("circle.dxf"))
        layer = parser.get_layer("0")
        render = layer.render(fuse=False)
        assert len(render) == 1
        assert render.dimtags() == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-5.0, -5.0, 0.0, 5.0, 5.0, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 1), 2) == 78.54

    def test_dxfparser_render_polyline(self):
        gmsh.clear()
        parser = DXFParser(get_file("polyline.dxf"))
        layer = parser.get_layer("straight_cw3")
        render = layer.render(fuse=False)
        assert len(render) == 1
        assert render.dimtags() == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-1.5, -1.5, 0.0, 11.5, 1.5, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 1), 2) == 37.07

    def test_dxfparser_render_poly(self):
        gmsh.clear()
        parser = DXFParser(get_file("poly.dxf"))
        layer = parser.get_layer("0")
        render = layer.render(fuse=False)
        assert len(render.geoms) == 1
        assert render.dimtags() == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [0.0, 0.0, 0.0, 10.0, 10.0, 0.0]
        assert np.round(gmsh.model.occ.getMass(2, 1), 2) == 100.0

    def test_dxfparser_render_poly_bulge(self):
        gmsh.clear()
        parser = DXFParser(get_file("poly_bulge.dxf"))
        layer = parser.get_layer("0")
        render = layer.render(fuse=False)
        print(parser.get_layer_names())
        assert len(render) == 1
        assert render.dimtags() == [(2, 1)]
        # render.plot()
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
