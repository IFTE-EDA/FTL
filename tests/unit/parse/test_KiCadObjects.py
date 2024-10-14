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
    KiCADLayer,
    KiCADObject,
    KiCADEntity,
    KiCADFilledPolygon,
    KiCADRect,
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

PARAMS_POLYGON = {
    "pts": {
        "xy": [
            [0, 0],
            [0, 100],
            [100, 100],
            [100, 0],
        ]
    },
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
    "filled_polygon": {
        "pts": [
            [0, 0],
            [100, 0],
            [100, 100],
            [0, 100],
        ],
    },
    "fill": "solid",
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

    """
    def test_kicadzone_create(self):
        obj = KiCADZone(self.logger, PARAMS_ZONE)
        assert obj.params == PARAMS_ZONE
        assert obj.layer == PARAMS_ZONE["layer"]
        assert obj.layers == None

        assert obj.net == PARAMS_ZONE["net"]
        assert obj.net_name == PARAMS_ZONE["net_name"]
        assert obj.hatch == PARAMS_ZONE["hatch"]
        assert obj.connect_pads == PARAMS_ZONE["connect_pads"]
        assert obj.min_thickness == PARAMS_ZONE["min_thickness"]
        assert obj.polygon == PARAMS_ZONE["polygon"]
        assert obj.filled_polygon == PARAMS_ZONE["filled_polygon"]
        assert obj.fill == PARAMS_ZONE["fill"]
    """

    """
    def test_kicadobject_create_multilayer_obj(self):
        obj = KiCADObject(self.logger, 0, PARAMS_MULTILAYER)
        assert obj.params == PARAMS_MULTILAYER
        assert obj.layer == None
        assert obj.layers == PARAMS_MULTILAYER["layers"]
    """
