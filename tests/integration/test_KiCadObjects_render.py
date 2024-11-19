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

    def test_kicadpad_render_direct_roundrect_nodrill(self):
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

    def test_kicadpad_render_direct_roundrect_drill(self):
        gmsh.clear()
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PAD_ROUNDRECT_DRILLED)
        geom = obj.render()
        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(9, 18)]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(9, 18)]
        assert get_bbox_rounded(2, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.0]
        assert get_mass_rounded(2, 1) == 133.85

    def test_kicadpad_render_layers_roundrect_nodrill(self):
        gmsh.clear()
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PAD_ROUNDRECT)
        geom = obj.render(self.layers)
        # layer_render = self.layers.get_layer("F.Cu").render()
        for name, layer in self.layers.layers.items():
            print(layer.name, layer.has_objects())
            if layer.name in ["F.Cu", "B.Cu"]:
                assert layer.has_objects()
            else:
                assert not layer.has_objects()
            assert len(layer.drills) == 0
        assert len(self.layers.metalizations) == 0
        assert geom is None
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert gmsh.model.occ.getEntities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.occ.getEntities(0) == [(0, i) for i in range(1, 9)]
        assert get_bbox_rounded(2, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.0]
        assert get_mass_rounded(2, 1) == 134.63

        pad = self.layers.get_layer("F.Cu").render()
        assert get_bbox_rounded(2, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.0]
        assert get_mass_rounded(2, 1) == 134.63

        pad.extrude(0.5)
        assert pad.geoms == [1]
        assert get_bbox_rounded(3, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.5]
        assert get_mass_rounded(3, 1) == 67.32

    # TODO: Add drill rendering to unit test
    def test_kicadpad_render_layers_roundrect_drill(self):
        gmsh.clear()
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PAD_ROUNDRECT_DRILLED)
        for name, layer in self.layers.layers.items():
            print(layer.name, layer.has_objects())
            if layer.name in ["F.Cu", "B.Cu"]:
                assert layer.has_objects()
            else:
                assert not layer.has_objects()
            assert len(layer.drills) == 0
        geom = obj.render(self.layers)
        assert len(self.layers.metalizations) == 1
        obj.make_drills(self.layers)
        for name, layer in self.layers.layers.items():
            assert len(layer.drills) == (
                1 if layer.name in ["F.Cu", "B.Cu", "Edge.Cuts"] else 0
            )
        assert (
            self.layers.get_layer("F.Cu").drills[0]
            != self.layers.get_layer("B.Cu").drills[0]
        )
        assert (
            self.layers.get_layer("F.Cu").drills[0]
            != self.layers.get_layer("Edge.Cuts").drills[0]
        )
        assert (
            self.layers.get_layer("B.Cu").drills[0]
            != self.layers.get_layer("Edge.Cuts").drills[0]
        )
        assert geom is None
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 6)]
        assert gmsh.model.occ.getEntities(1) == [
            (1, i) for i in range(1, 15) if i != 9
        ]
        assert gmsh.model.occ.getEntities(0) == [
            (0, i) for i in range(1, 15) if i != 9
        ]
        assert get_bbox_rounded(2, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.0]
        assert get_mass_rounded(2, 1) == 134.63

        # Render test on F.Cu layer:
        pad = self.layers.get_layer("F.Cu").render()
        assert get_bbox_rounded(2, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.0]
        assert get_mass_rounded(2, 1) == 133.85

        pad.extrude(0.5)
        assert pad.geoms == [1]
        assert get_bbox_rounded(3, 1) == [-35.0, -7.0, 0.0, -25.0, 7.0, 0.5]
        assert get_mass_rounded(3, 1) == 66.92

    def test_kicadvia_render_2D(self):
        gmsh.clear()
        par = Mock_Layer(self.logger)
        via = KiCADVia(par, PARAMS_VIA)
        geom = via.render()
        # self.layers.add_via_metalization(obj)

        assert geom.geoms == [1]
        assert gmsh.model.occ.getEntities(2) == [(2, 1)]
        assert gmsh.model.occ.getEntities(1) == [(1, 1)]
        assert gmsh.model.occ.getEntities(0) == [(0, 1)]
        assert get_bbox_rounded(2, 1) == [-0.5, -0.5, 0.0, 2.5, 2.5, 0.0]
        assert get_mass_rounded(2, 1) == 7.07

        metal = via.get_metalization()
        # metal.plot()
        assert metal.geoms == [2]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 3)]
        assert gmsh.model.occ.getEntities(1) == [
            (1, i) for i in range(1, 5) if i not in [2]
        ]
        assert gmsh.model.occ.getEntities(0) == [
            (0, i) for i in range(1, 5) if i not in [2]
        ]
        assert get_bbox_rounded(2, 2) == [0.5, 0.5, 0.0, 1.5, 1.5, 0.0]
        assert get_mass_rounded(2, 2) == 0.05

        drill = via.get_drill()
        # drill.plot()
        assert drill.geoms == [3]
        assert gmsh.model.occ.getEntities(2) == [(2, i) for i in range(1, 4)]
        assert gmsh.model.occ.getEntities(1) == [
            (1, i) for i in range(1, 6) if i not in [2]
        ]
        assert gmsh.model.occ.getEntities(0) == [
            (0, i) for i in range(1, 6) if i not in [2]
        ]
        assert get_bbox_rounded(2, 3) == [0.5, 0.5, 0.0, 1.5, 1.5, 0.0]
        assert get_mass_rounded(2, 3) == 0.79

    # def test_kicadpart_create(self):
    #    obj = KiCADPart(self.logger, PARAMS_PART)
    #    assert obj.params == PARAMS_PART


"""



    # TODO: not working. gotta change the main code.
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
