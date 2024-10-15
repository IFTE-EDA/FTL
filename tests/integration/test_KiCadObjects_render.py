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


LAYER_PARAMS_TEST = ["Test Layer", "layer type", "Long Layer Name"]

"""PARAMS_MULTILAYER = {
    "start": [0, 0],
    "end": [100, 100],
    "stroke": {
        "width": 0.2,
        "type": "default"
    },
    "fill": "solid",
    "layers": [
        "Testlayer1",
        "Testlayer2",
        "Testlayer3",
    ],
    "tstamp": "TSTAMPTEST",
}"""

PARAMS_LINE = {
    "start": [0, 0],
    "end": [100, 100],
    "stroke": {"width": 0.2, "type": "default"},
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_RECT = {
    "start": [0, 0],
    "end": [100, 100],
    "stroke": {"width": 0.2, "type": "default"},
    "fill": "solid",
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_ARC = {
    "start": [-50, 0],
    "mid": [0, 50],
    "end": [50, 0],
    "stroke": {"width": 0.2, "type": "solid"},
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_POLYGON = {
    "pts": {
        "xy": [
            [0, 0],
            [0, 100],
            [100, 100],
            [100, 0],
        ]
    },
    "stroke": {"width": 0.2, "type": "default"},
    "width": 0.2,
    "fill": "no",
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_POLYGON_CCW = {
    "pts": {
        "xy": [
            [0, 0],
            [100, 0],
            [100, 100],
            [0, 100],
        ]
    },
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_ZONE = {
    "net": 0,
    "net_name": "MyNetName",
    "hatch": "solid",
    "connect_pads": "no",
    "min_thickness": 0.2,
    "polygon": {
        "pts": {
            "xy": [
                [0, 0],
                [100, 0],
                [100, 100],
                [0, 100],
            ]
        },
    },
    "filled_polygon": [
        {
            "pts": {
                "xy": [
                    [0, 0],
                    [100, 0],
                    [100, 100],
                    [0, 100],
                ]
            },
        }
    ],
    "fill": "solid",
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_VIA = {
    "at": [0, 0],
    "size": [3],
    "drill": [1],
    "layers": ["F.Cu", "B.Cu"],
    "net": [2],
}

PARAMS_PART = {
    0: "TestPart",
    # "ref": "U1",
    "descr": "TestDescription",
    "tags": ["TestTag1", "TestTag2"],
    "layer": "Testlayer",
    "path": "TestPath",
    "at": [0, 0, 0],
    "pads": [
        {
            0: "1",
            1: "smd",
            2: "roundrect",
            "at": [-30, 0],
            "size": [10, 14],
            "layers": ["Testlayer1", "Testlayer2"],
            "roundrect_rratio": 0.25,
            "net": [0, "GND"],
        },
        {
            0: "2",
            1: "smd",
            2: "roundrect",
            "at": [-30, 0],
            "size": [10, 14],
            "layers": ["Testlayer1", "Testlayer2"],
            "roundrect_rratio": 0.25,
            "net": [0, "GND"],
        },
    ],
    "property": [
        [
            '"Reference"',
            "T1",
        ]
    ],
    "footprint": "TestFootprint",
    "datasheet": "TestDatasheet",
    "tstamp": "TSTAMPTEST",
}

PARAMS_PART_DRILLED_PADS = {
    0: "TestPart",
    # "ref": "U1",
    "descr": "TestDescription",
    "tags": ["TestTag1", "TestTag2"],
    "layer": "Testlayer",
    "path": "TestPath",
    "at": [0, 0, 0],
    "pads": [
        {
            0: "1",
            1: "thru_hole",
            2: "oval",
            "at": [-30, 0],
            "size": [1.7, 1.7],
            "drill": [1],
            "layers": ["Testlayer1", "Testlayer2"],
            "roundrect_rratio": 0.25,
            "net": [0, "GND"],
        },
        {
            0: "2",
            1: "thru_hole",
            2: "oval",
            "at": [-30, 0],
            "size": [1.7, 1.7],
            "drill": [1],
            "layers": ["Testlayer1", "Testlayer2"],
            "roundrect_rratio": 0.25,
            "net": [0, "GND"],
        },
    ],
    "property": [
        [
            '"Reference"',
            "T1",
        ]
    ],
    "footprint": "TestFootprint",
    "datasheet": "TestDatasheet",
    "tstamp": "TSTAMPTEST",
}


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

    def test_kicadlayer_render_empty(self):
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
        assert get_bbox_rounded(2, 1) == [-0.1, -0.1, 0, 100.1, 100.1, 0]
        assert get_mass_rounded(2, 1) == 60.03

    """
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
