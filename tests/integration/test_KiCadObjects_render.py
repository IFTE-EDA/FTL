from __future__ import annotations
import logging
import sys
import os
import math
from pathlib import Path
import numpy as np
import pytest
import gmsh

from FTL.Util.logging import Logger, Loggable
from FTL.core.GMSHGeometry import GMSHGeom2D, GMSHGeom3D, dimtags, dimtags2int
from FTL.parse.KiCADParser import KiCADParser
from FTL.parse.KiCADParser import (
    KiCADLayer,
    KiCADObject,
    KiCADEntity,
    KiCADLine,
    KiCADRect,
    KiCADArc,
    KiCADPolygon,
    KiCADFilledPolygon,
    KiCADZone,
    KiCADPad,
    KiCADVia,
    KiCADPart,
)
from tests.data.KiCadObjects_data import (
    LAYER_PARAMS_TEST,
    PARAMS_RECT,
    PARAMS_LINE,
    PARAMS_ARC,
    PARAMS_POLYGON,
    PARAMS_POLYGON_CCW,
    PARAMS_PAD_ROUNDRECT,
    PARAMS_PAD_ROUNDRECT_DRILLED,
    PARAMS_PART,
    PARAMS_PART_DRILLED_PADS,
    PARAMS_VIA,
    PARAMS_ZONE,
)

PRECISION_DIGITS = 2


def get_file(file_name: str):
    return Path(__file__).parent.parent / "data" / file_name


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


class Object_Mock:
    def __init__(self, name, empty=False):
        self.name = name
        self.empty = empty
        self.rendered = False

    def is_empty(self):
        return self.empty

    def render(self):
        self.rendered = True
        return 1


class Mock_Layer(Loggable):
    def __init__(self, parent):
        super().__init__(parent)
        self.ref = "T1"


class Test_KiCadObjects_Render:
    def setup_class(self):
        self.logger = Logger(__name__)
        self.parser = KiCADParser(
            get_file("empty.kicad_pcb"), logger=self.logger
        )
        self.layers = self.parser.stackup

    def test_kicadlayer_render_empty(self):
        gmsh.clear()
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        geom = layer.render()
        print("Geoms: ", geom.geoms)
        print("GMSH entities: ", gmsh.model.occ.getEntities())
        assert geom.geoms == []
        assert gmsh.model.occ.getEntities() == []

    def test_kicadzone_render_filled_polygon(self):
        gmsh.clear()
        obj = KiCADFilledPolygon(self.logger, PARAMS_POLYGON)
        geom = obj.render()
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 100, 100, 0]
        assert get_mass_rounded(2, 1) == 10000

    # TODO: get ...unfilled?... polygon

    def test_kicadrect_render(self):
        gmsh.clear()
        obj = KiCADRect(self.logger, PARAMS_RECT)
        geom = obj.render()
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert gmsh.model.occ.getEntities(1) == [
            (1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
        ]
        # assert get_bbox_rounded(2, 1) == [-0.1, -0.1, 0, 100.1, 100.1, 0]
        assert get_bbox_rounded(2, 1) == [0, 0, 0, 100, 100, 0]
        assert get_mass_rounded(2, 1) == 10000.00

    def test_kicadline_render(self):
        gmsh.clear()
        obj = KiCADLine(self.logger, PARAMS_LINE)
        geom = obj.render()
        # geom.plot()
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-0.1, -0.1, 0, 100.1, 100.1, 0]
        assert get_mass_rounded(2, 1) == 28.32

    def test_kicadarc_render(self):
        gmsh.clear()
        obj = KiCADArc(self.logger, PARAMS_ARC)
        geom = obj.render()
        # geom.plot()
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert get_bbox_rounded(2, 1) == [-50.1, -0.1, 0, 50.1, 50.1, 0]
        assert get_mass_rounded(2, 1) == 31.45

    def test_kicadpolygon_render(self):
        gmsh.clear()
        obj = KiCADPolygon(self.logger, PARAMS_POLYGON)
        geom = obj.render()
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert not (1, 13) in gmsh.model.occ.getEntities(1)
        assert get_bbox_rounded(2, 1) == [-0.1, -0.1, 0, 100.1, 100.1, 0]
        assert get_mass_rounded(2, 1) == 10040.03

    def test_kicadpad_render_direct_roundrect(self):
        gmsh.clear()
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PAD_ROUNDRECT)
        geom = obj.render()
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert get_bbox_rounded(2, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.0]
        assert get_mass_rounded(2, 1) == 134.63

    """
    def test_kicadpad_render_layers_roundrect(self):
        gmsh.clear()
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PAD_ROUNDRECT_DRILLED)
        obj.render(self.layers)
        geom = self.layers.get_layer("F.Cu").render()
        geom.plot()
        for name, layer in self.layers.layers.items():
            print(name, self.layers.render_layer(name).geoms)
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert get_bbox_rounded(2, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.0]
        assert get_mass_rounded(2, 1) == 134.63

    def test_kicadpad_render_drilled(self):
        gmsh.clear()
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PART_DRILLED_PADS["pads"][0])
        geom = obj.render(self.layers)
        r_fcu = self.layers.get_layer("F.Cu").render()
        r_fcu.plot()
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert get_bbox_rounded(2, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.0]
        assert get_mass_rounded(2, 1) == 134.63

    def test_kicadvia_create(self):
        obj = KiCADVia(self.logger, PARAMS_VIA)
        assert obj.params == PARAMS_VIA
        assert obj.layer is None
        assert obj.layers == PARAMS_VIA["layers"]
        assert obj.at == PARAMS_VIA["at"]
        assert obj.size == PARAMS_VIA["size"]
        assert obj.drill == PARAMS_VIA["drill"]
        # TODO: maybe add this to every object?
        # assert obj.net == PARAMS_VIA["net"]

    def test_kicadvia_get_layer_names(self):
        obj = KiCADVia(self.logger, PARAMS_VIA)
        assert obj.get_layer_names() == ["F.Cu", "B.Cu"]

    def test_kicadpart_has_drill(self):
        par = Mock_Layer(self.logger)
        obj1 = KiCADPad(par, PARAMS_PART["pads"][0])
        obj2 = KiCADPad(par, PARAMS_PART_DRILLED_PADS["pads"][0])
        assert obj1.has_drill() is False
        assert obj2.has_drill() is True

    # TODO: move to integration test
    """

    """
    def test_kicadpad_get_drill(self):
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PART_DRILLED_PADS["pads"][0])
        drill = obj.get_drill()
        self.logger.critical(drill.geoms[0])
        assert False
    """
    """

    def test_kicadpart_create(self):
        obj = KiCADPart(self.logger, PARAMS_PART)
        assert obj.params == PARAMS_PART
        assert obj.layer == PARAMS_PART["layer"]
        assert obj.layers is None
        assert obj.at == PARAMS_PART["at"]
        assert obj.angle == PARAMS_PART["at"][2]

        assert obj.name == PARAMS_PART[0]
        assert obj.descr == PARAMS_PART["descr"]
        assert obj.tags == PARAMS_PART["tags"]
        assert obj.path == PARAMS_PART["path"]

    def test_kicadpart_get_coordinates(self):
        obj = KiCADPart(self.logger, PARAMS_PART)
        assert obj.x == PARAMS_PART["at"][0]
        assert obj.y == PARAMS_PART["at"][1]

    """
    # TODO: not working. gotta change the main code.
    """
    def test_kicadpart_pads(self):
        obj = KiCADPart(self.logger, PARAMS_PART)
        assert len(obj.pads) == 2
        assert obj.pads[0].name == "1"
        assert obj.pads[0].type == "smd"
        assert obj.pads[0].shape == "roundrect"
        assert obj.pads[0].at == [-30, 0]
        assert obj.pads[0].size == [10, 14]
        assert obj.pads[0].layers == ["Testlayer1", "Testlayer2"]
        assert obj.pads[0].roundrect_rratio == 0.25
        assert obj.pads[0].net == [0, "GND"]
    """
    """

    def test_kicadpart_move_relative(self):
        obj = KiCADPart(self.logger, PARAMS_PART)
        obj.move_relative([100, 100])
        assert obj.x == PARAMS_PART["at"][0] + 100
        assert obj.y == PARAMS_PART["at"][1] + 100

    def test_kicadzone_create(self):
        obj = KiCADZone(self.logger, PARAMS_ZONE)
        assert obj.params == PARAMS_ZONE
        assert obj.layer == PARAMS_ZONE["layer"]
        assert obj.layers is None

        assert obj.net == PARAMS_ZONE["net"]
        assert obj.net_name == PARAMS_ZONE["net_name"]
        assert obj.hatch == PARAMS_ZONE["hatch"]
        assert obj.connect_pads == PARAMS_ZONE["connect_pads"]
        assert obj.min_thickness == PARAMS_ZONE["min_thickness"]
        assert obj.polygon == PARAMS_ZONE["polygon"]
        filled_polygon = obj.filled_polygon[0]
        print(filled_polygon.points)
        # TODO - this checks if the last point is the same as the first point. Is that correct?
        assert (
            filled_polygon.points[0:4]
            == PARAMS_ZONE["filled_polygon"][0]["pts"]["xy"]
        )
        assert (
            filled_polygon.points[4]
            == PARAMS_ZONE["filled_polygon"][0]["pts"]["xy"][0]
        )
        assert obj.fill == PARAMS_ZONE["fill"]
"""
