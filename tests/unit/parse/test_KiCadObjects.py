from __future__ import annotations
import logging
import sys
import os
import math
from pathlib import Path
import numpy as np
import pytest

from FTL.Util.logging import Logger, Loggable
from FTL.parse.KiCADParser import (
    KiCADParser,
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


def get_file(file_name: str):
    return Path(__file__).parent.parent.parent / "data" / file_name


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


class Test_KiCadObjects:
    def setup_class(self):
        self.logger = Logger(__name__)
        self.parser = KiCADParser(
            get_file("empty.kicad_pcb"), logger=self.logger
        )
        self.layers = self.parser.stackup

    def test_kicadobject_init_fails(self):
        try:
            KiCADObject(self.logger, 0, PARAMS_RECT)
        except Exception as e:
            print("Exception type: ", type(e))
            if isinstance(e, TypeError):
                return
        assert False

    def test_kicadentity_init_fails(self):
        try:
            KiCADEntity(self.logger, 0, PARAMS_RECT)
        except Exception as e:
            print("Exception type: ", type(e))
            if isinstance(e, TypeError):
                return
        assert False

    def test_kicadzone_filled_polygon(self):
        obj = KiCADFilledPolygon(self.logger, PARAMS_POLYGON)
        assert obj.params == PARAMS_POLYGON
        assert obj.layer == PARAMS_POLYGON["layer"]
        assert obj.layers is None
        print(obj.points)
        # TODO - beginning point is added here again. correct?
        assert obj.points == PARAMS_POLYGON["pts"]["xy"]
        assert obj.points[4] == PARAMS_POLYGON["pts"]["xy"][0]

    def test_kicadzone_filled_polygon_is_clockwise(self):
        obj = KiCADFilledPolygon(self.logger, PARAMS_POLYGON)
        assert obj.is_clockwise() is True

    def test_kicadzone_filled_polygon_is_counterclockwise(self):
        obj = KiCADFilledPolygon(self.logger, PARAMS_POLYGON_CCW)
        assert obj.is_clockwise() is False

    def test_kicadzone_filled_polygon_curve_is_clockwise(self):
        obj = KiCADFilledPolygon(self.logger, PARAMS_POLYGON)
        assert obj.curve_is_clockwise(PARAMS_POLYGON["pts"]["xy"]) is True
        assert obj.curve_is_clockwise(PARAMS_POLYGON_CCW["pts"]["xy"]) is False

    def test_kicadrect_create(self):
        obj = KiCADRect(self.logger, PARAMS_RECT)
        assert obj.params == PARAMS_RECT
        assert obj.layer == PARAMS_RECT["layer"]
        assert obj.layers is None

        assert obj.fill == PARAMS_RECT["fill"]
        print(obj.points)
        # TODO - correct orientation?
        assert obj.points == [
            [0, 0],
            [100, 0],
            [100, 100],
            [0, 100],
            [0, 0],
        ]

    def test_kicadline_create(self):
        obj = KiCADLine(self.logger, PARAMS_LINE)
        # TODO - why no params?
        assert obj.params == PARAMS_LINE
        assert obj.layer == PARAMS_LINE["layer"]
        assert obj.layers is None

        assert obj.start == PARAMS_LINE["start"]
        assert obj.end == PARAMS_LINE["end"]
        assert obj.width == PARAMS_LINE["stroke"]["width"]

    def test_kicadarc_create(self):
        obj = KiCADArc(self.logger, PARAMS_ARC)
        assert obj.params == PARAMS_ARC
        assert obj.layer == PARAMS_ARC["layer"]
        assert obj.layers is None

        assert obj.start == PARAMS_ARC["start"]
        assert obj.end == PARAMS_ARC["end"]
        assert obj.width == PARAMS_ARC["stroke"]["width"]

    def test_kicadpolygon_create(self):
        obj = KiCADPolygon(self.logger, PARAMS_POLYGON)
        assert obj.params == PARAMS_POLYGON
        assert obj.layer == PARAMS_POLYGON["layer"]
        assert obj.layers is None

        assert obj.points == PARAMS_POLYGON["pts"]["xy"]

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

    def test_kicadpad_create(self):
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PART["pads"][0])
        assert obj.params == PARAMS_PART["pads"][0]
        assert (
            obj.name
            == PARAMS_PART["property"][0][1]
            + ".Pads."
            + PARAMS_PART["pads"][0][0]
        )
        assert obj.type == PARAMS_PART["pads"][0][1]
        assert obj.shape == PARAMS_PART["pads"][0][2]
        assert obj.at == PARAMS_PART["pads"][0]["at"]
        assert obj.size == PARAMS_PART["pads"][0]["size"]
        assert obj.layers == PARAMS_PART["pads"][0]["layers"]
        # assert obj.roundrect_rratio == PARAMS_PART["pads"][0]["roundrect_rratio"]
        assert obj.net == PARAMS_PART["pads"][0]["net"]

    def test_kicadpad_create_drilled(self):
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PART_DRILLED_PADS["pads"][0])
        assert obj.params == PARAMS_PART_DRILLED_PADS["pads"][0]
        assert (
            obj.name
            == PARAMS_PART_DRILLED_PADS["property"][0][1]
            + ".Pads."
            + PARAMS_PART_DRILLED_PADS["pads"][0][0]
        )
        assert obj.type == PARAMS_PART_DRILLED_PADS["pads"][0][1]
        assert obj.shape == PARAMS_PART_DRILLED_PADS["pads"][0][2]
        assert obj.at == PARAMS_PART_DRILLED_PADS["pads"][0]["at"]
        assert obj.size == PARAMS_PART_DRILLED_PADS["pads"][0]["size"]
        assert obj.layers == PARAMS_PART_DRILLED_PADS["pads"][0]["layers"]
        assert obj.net == PARAMS_PART_DRILLED_PADS["pads"][0]["net"]
        assert obj.drill == PARAMS_PART_DRILLED_PADS["pads"][0]["drill"]

    """
    def test_kicadpad_get_layers(self):
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PART["pads"][0])
        assert obj.layers == ["F.*"]
    """

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

    def test_kicadpart_move_relative(self):
        obj = KiCADPart(self.logger, PARAMS_PART)
        obj.move_relative([100, 100])
        assert obj.x == PARAMS_PART["at"][0] + 100
        assert obj.y == PARAMS_PART["at"][1] + 100

    def test_kicadpart_has_drill(self):
        par = Mock_Layer(self.logger)
        obj1 = KiCADPad(par, PARAMS_PART["pads"][0])
        obj2 = KiCADPad(par, PARAMS_PART_DRILLED_PADS["pads"][0])
        assert obj1.has_drill() is False
        assert obj2.has_drill() is True

    # TODO: move to integration test
    """
    def test_kicadpad_get_drill(self):
        par = Mock_Layer(self.logger)
        obj = KiCADPad(par, PARAMS_PART_DRILLED_PADS["pads"][0])
        drill = obj.get_drill()
        self.logger.critical(drill.geoms[0])
        assert False
    """
