from __future__ import annotations
import sys
import os
import math
from pathlib import Path

import gmsh
import numpy as np

from FTL.Util.logging import Logger, Loggable
from FTL.parse.KiCADParser import KiCADParser

PRECISION_DIGITS = 2


def get_file(file_name: str):
    return Path(__file__).parent.parent.parent / "data" / file_name


class Test_KiCadStackupManager:
    def setup_class(self):
        self.logger = Logger(__name__)
        self.parser = KiCADParser(
            get_file("layers.kicad_pcb"), logger=self.logger
        )
        self.layers = self.parser.stackup

    def test_kicadstackupmanager_get_layer_empty(self):
        parser = KiCADParser(get_file("empty.kicad_pcb"), logger=self.logger)
        layers = parser.stackup
        layer = layers.get_layer("F.Cu")
        assert not layer.has_objects()
        assert not layers.layer_has_objects("F.Cu")

    def test_kicadstackupmanager_get_layer_not_existant(self):
        try:
            self.layers.get_layer("NonExistantLayer")
        except Exception as e:
            print("Exception type: ", type(e))
            print("Assertion: ", isinstance(e, KeyError))
            if isinstance(e, KeyError):
                return
        assert False

    def test_kicadparser_layer_has_objects(self):
        parser = KiCADParser(get_file("layers.kicad_pcb"))
        layer = parser.stackup.get_layer("F.Cu")
        assert layer.has_objects()
        assert self.layers.layer_has_objects("F.Cu")

    def test_kicadstackupmanager_list_layers(self):
        layers = list(self.layers.get_layer_names())
        print("Layers: ", "\n".join(layers))
        cmp = [
            "F.Cu",
            "B.Cu",
            "B.Adhes",
            "F.Adhes",
            "B.Paste",
            "F.Paste",
            "B.SilkS",
            "F.SilkS",
            "B.Mask",
            "F.Mask",
            "Dwgs.User",
            "Cmts.User",
            "Eco1.User",
            "Eco2.User",
            "Edge.Cuts",
            "Margin",
            "B.CrtYd",
            "F.CrtYd",
            "B.Fab",
            "F.Fab",
            "User.1",
            "User.2",
            "User.3",
            "User.4",
            "User.5",
            "User.6",
            "User.7",
            "User.8",
            "User.9",
        ]
        print("Comp: ", "\n".join(cmp))
        assert len(layers) == len(cmp)
        for i in range(len(layers)):
            assert layers[i] == cmp[i]

    def test_kicadstackupmanager_list_stackup_layers(self):
        layers = list(self.layers.get_stackup_layer_names())
        print("Stackup layers: ", "\n".join(layers))
        cmp = [
            "B.SilkS",
            "B.Paste",
            "B.Mask",
            "B.Cu",
            "Edge.Cuts",
            "F.Cu",
            "F.Mask",
            "F.Paste",
            "F.SilkS",
        ]
        print("Comp: ", "\n".join(cmp))
        assert len(layers) == len(cmp)
        for i in range(len(layers)):
            assert layers[i] == cmp[i]

    def test_kicadstackupmanager_num_layers(self):
        num_layers = len(list(self.layers.get_layer_names()))
        assert num_layers == 29
        assert len(self.layers.layers) == 29

    def test_kicadstackupmanager_layer_items(self):
        for name, layer in self.layers.layers.items():
            assert layer.name == name
            assert layer == self.layers.layers[name]

    def test_kicadstackupmanager_build_stackup(self):
        num_layers = len(list(self.layers.get_layer_names()))
        assert num_layers == 29
        last_h = 0
        for name, layer in self.layers.stackup.items():
            layer = self.layers.get_layer(name)
            print(
                "Layer: ",
                name,
                "T: ",
                layer.thickness,
                "zMin: ",
                layer.zmin,
                "zMax: ",
                layer.zmax,
            )
            if layer.name in ["F.SilkS", "B.SilkS"]:
                assert layer.thickness == 0
                assert layer.zmax == last_h
                assert layer.zmin == last_h
            else:
                assert layer.thickness == 0.1
                assert layer.zmax == round(last_h + 0.1, 4)
                assert layer.zmin == last_h
                last_h = layer.zmax

        for name, layer in self.layers.layers.items():
            if name in self.layers.stackup.keys():
                continue
            assert layer.thickness == 0

    def test_kicadstackupmanager_get_layers_from_single_pattern(self):
        layers = self.layers.get_layers_from_pattern("F&B.SilkS")
        assert len(layers) == 2
        for layer in layers:
            assert layer.name.endswith("SilkS")
        layers = self.layers.get_layers_from_pattern("*.Cu")
        assert len(layers) == 2
        for layer in layers:
            assert layer.name.endswith("Cu")

    def test_kicadstackupmanager_get_layers_from_pattern_list(self):
        layers = self.layers.get_layers_from_pattern(
            ["F&B.SilkS", "Edge.Cuts", "*.Cu"]
        )
        names = [layer.name for layer in layers].sort()
        print("Names: ", names)
        assert (
            names == ["F.SilkS", "B.SilkS", "Edge.Cuts", "B.Cu", "F.Cu"].sort()
        )

    def test_kicadstackupmanager_get_lowest_layer(self):
        layers = ["F.Cu", "B.Cu", "Edge.Cuts", "F.SilkS", "B.SilkS"]
        lowest = self.layers.get_lowest_layer(layers)
        print(lowest)
        assert lowest.name == "B.SilkS"

    def test_kicadstackupmanager_get_highest_layer(self):
        layers = ["F.Cu", "B.Cu", "Edge.Cuts", "F.SilkS", "B.SilkS"]
        lowest = self.layers.get_highest_layer(layers)
        print(lowest)
        assert lowest.name == "F.SilkS"
