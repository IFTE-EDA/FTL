from __future__ import annotations
import logging
import sys
import os
import math
from pathlib import Path
import numpy as np
import pytest

from FTL.Util.logging import Logger
from FTL.parse.KiCADParser import KiCADLayer

LAYER_PARAMS_TEST = ["Test Layer", "layer type", "Long Layer Name"]

LAYER_PARAMS_TEST_NOLONGNAME = ["Test Layer", "layer type"]


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

    def test_kicadlayer_create_default_params(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        assert layer.name == LAYER_PARAMS_TEST[0]
        assert layer.type == LAYER_PARAMS_TEST[1]
        assert layer.name_long == LAYER_PARAMS_TEST[2]

    def test_kicadlayer_create_no_long_name(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST_NOLONGNAME)
        assert layer.name == LAYER_PARAMS_TEST_NOLONGNAME[0]
        assert layer.type == LAYER_PARAMS_TEST_NOLONGNAME[1]
        assert layer.name_long is None

    def test_kicadlayer_create_default_values(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        assert layer.geoms == []
        assert layer.segments == []
        assert layer.arcs == []
        assert layer.zones == []
        assert layer.footprints == []
        assert layer.drills == []
        assert layer.zmin == 0
        assert layer.zmax == 0
        assert layer.thickness == 0

    # layer empty by default
    def test_kicadlayer_default_empty(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        assert not layer.has_objects()

    def test_kicadlayer_add_geom_single(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock = Object_Mock("test")
        layer.add_geometry(mock)
        assert layer.has_objects()
        assert layer.geoms[0].name == "test"
        mock.name = "Test_new"
        assert layer.geoms[0].name == "Test_new"

    def test_kicadlayer_add_geom_list(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        layer.add_geometry([mock1, mock2])
        assert layer.has_objects()
        assert layer.geoms[0].name == "test1"
        assert layer.geoms[1].name == "test2"

    def test_kicadlayer_add_geom_multiple(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        mock3 = Object_Mock("test3")
        layer.add_geometry(mock1)
        layer.add_geometry([mock2, mock3])
        assert layer.has_objects()
        assert layer.geoms[0].name == "test1"
        assert layer.geoms[1].name == "test2"
        assert layer.geoms[2].name == "test3"

    def test_kicadlayer_add_segment_single(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock = Object_Mock("test")
        layer.add_segment(mock)
        assert layer.has_objects()
        assert layer.segments[0].name == "test"
        mock.name = "Test_new"
        assert layer.segments[0].name == "Test_new"

    def test_kicadlayer_add_segment_list(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        layer.add_segment([mock1, mock2])
        assert layer.has_objects()
        assert layer.segments[0].name == "test1"
        assert layer.segments[1].name == "test2"

    def test_kicadlayer_add_segment_multiple(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        mock3 = Object_Mock("test3")
        layer.add_segment(mock1)
        layer.add_segment([mock2, mock3])
        assert layer.has_objects()
        assert layer.segments[0].name == "test1"
        assert layer.segments[1].name == "test2"
        assert layer.segments[2].name == "test3"

    def test_kicadlayer_add_arc_single(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock = Object_Mock("test")
        layer.add_arc(mock)
        assert layer.has_objects()
        assert layer.arcs[0].name == "test"
        mock.name = "Test_new"
        assert layer.arcs[0].name == "Test_new"

    def test_kicadlayer_add_arc_list(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        layer.add_arc([mock1, mock2])
        assert layer.has_objects()
        assert layer.arcs[0].name == "test1"
        assert layer.arcs[1].name == "test2"

    def test_kicadlayer_add_arc_multiple(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        mock3 = Object_Mock("test3")
        layer.add_arc(mock1)
        layer.add_arc([mock2, mock3])
        assert layer.has_objects()
        assert layer.arcs[0].name == "test1"
        assert layer.arcs[1].name == "test2"
        assert layer.arcs[2].name == "test3"

    def test_kicadlayer_add_zone_single(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock = Object_Mock("test")
        layer.add_zone(mock)
        assert layer.has_objects()
        assert layer.zones[0].name == "test"
        mock.name = "Test_new"
        assert layer.zones[0].name == "Test_new"

    def test_kicadlayer_add_zone_list(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        layer.add_zone(["test", "test2"])
        assert layer.has_objects()
        assert layer.zones == ["test", "test2"]

    def test_kicadlayer_add_zone_multiple(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        layer.add_zone("test")
        layer.add_zone(["test2", "test3"])
        assert layer.has_objects()
        assert layer.zones == ["test", "test2", "test3"]

    def test_kicadlayer_add_footprint_single(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock = Object_Mock("test")
        layer.add_footprint(mock)
        assert layer.has_objects()
        assert layer.footprints[0].name == "test"
        mock.name = "Test_new"
        assert layer.footprints[0].name == "Test_new"

    def test_kicadlayer_add_footprint_list(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        layer.add_footprint([mock1, mock2])
        assert layer.has_objects()
        assert layer.footprints[0].name == "test1"
        assert layer.footprints[1].name == "test2"

    def test_kicadlayer_add_footprint_multiple(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        mock3 = Object_Mock("test3")
        layer.add_footprint(mock1)
        layer.add_footprint([mock2, mock3])
        assert layer.has_objects()
        assert layer.footprints[0].name == "test1"
        assert layer.footprints[1].name == "test2"
        assert layer.footprints[2].name == "test3"

    def test_kicadlayer_add_drill_single(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock = Object_Mock("test")
        layer.add_drill(mock)
        assert layer.drills[0].name == "test"
        mock.name = "Test_new"
        assert layer.drills[0].name == "Test_new"

    def test_kicadlayer_add_drill_list(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        layer.add_drill([mock1, mock2])
        assert layer.drills[0].name == "test1"
        assert layer.drills[1].name == "test2"

    def test_kicadlayer_add_drill_multiple(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test1")
        mock2 = Object_Mock("test2")
        mock3 = Object_Mock("test3")
        layer.add_drill(mock1)
        layer.add_drill([mock2, mock3])
        assert layer.drills[0].name == "test1"
        assert layer.drills[1].name == "test2"
        assert layer.drills[2].name == "test3"

    # TODO: Found a bug here. The layer should be listed as empty
    @pytest.mark.xfail
    def test_kicadlayer_layer_with_empty_geometries(self):
        layer = KiCADLayer(self.logger, 0, LAYER_PARAMS_TEST)
        mock1 = Object_Mock("test", empty=True)
        mock2 = Object_Mock("test2", empty=True)
        layer.add_geometry([mock1, mock2])
        assert not layer.has_objects()
