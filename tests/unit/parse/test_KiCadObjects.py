from __future__ import annotations
import logging
import sys
import os
import math
from pathlib import Path
import numpy as np
import pytest

from FTL.Util.logging import Logger
from FTL.parse.KiCADParser import (
    KiCADObject,
    KiCADEntity,
    KiCADLine,
    KiCADRect,
    KiCADArc,
    KiCADPolygon,
    KiCADFilledPolygon,
    KiCADZone,
    KiCADPart,
)

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
            "name": "TestPad1",
            "shape": "rect",
            "pos": [0, 0],
            "size": [100, 100],
            "drill": 50,
            "layers": ["Testlayer1", "Testlayer2"],
        },
        {
            "name": "TestPad2",
            "shape": "circle",
            "pos": [100, 100],
            "size": [100, 100],
            "drill": 50,
            "layers": ["Testlayer1", "Testlayer2"],
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

PARAMS_PAD = {
    "at": [0, 0, 0],
    "size": [10, 14],
    "drill": 1,
    "layers": ["Testlayer1", "Testlayer2"],
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


class Test_KiCadLayer:
    def setup_class(self):
        self.logger = Logger(__name__)

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
        assert obj.points[0:4] == PARAMS_POLYGON["pts"]["xy"]
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
