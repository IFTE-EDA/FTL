# generate pytest testcases for KicadStackupManager
# test_StackupManager.py
import pytest
from FTL.Util.logging import Logger
from FTL.parse.KiCADParser import KiCADStackupManager
from FTL.core.FPC import Material


class Test_StackupManager:
    def setup_class(self):
        self.logger = Logger("Test_StackupManager")
        layer_params = {
            0: {0: "F.Cu", 1: "signal"},
            31: {0: "B.Cu", 1: "signal"},
            32: {0: "B.Adhes", 1: "user", 2: "B.Adhesive"},
            33: {0: "F.Adhes", 1: "user", 2: "F.Adhesive"},
            34: {0: "B.Paste", 1: "user"},
            35: {0: "F.Paste", 1: "user"},
            36: {0: "B.SilkS", 1: "user"},
            37: {0: "F.SilkS", 1: "user"},
            38: {0: "B.Mask", 1: "user"},
            39: {0: "F.Mask", 1: "user"},
            44: {0: "Edge.Cuts", 1: "user"},
        }
        stackup_params = {
            "layer": [
                {
                    0: "F.SilkS",
                    "type": "Top Silk Screen",
                    "material": "Liquid Photo",
                },
                {0: "F.Paste", "type": "Top Solder Paste"},
                {
                    0: "F.Mask",
                    "type": "Top Solder Mask",
                    "thickness": 0.01,
                    "material": "Liquid Ink",
                },
                {0: "F.Cu", "type": "copper", "thickness": 0.035},
                {0: "dielectric 1", "type": "core", "thickness": 0.1},
                {0: "B.Cu", "type": "copper", "thickness": 0.035},
                {
                    0: "B.Mask",
                    "type": "Bottom Solder Mask",
                    "thickness": 0.01,
                    "material": "Dry Film",
                },
                {0: "B.Paste", "type": "Bottom Solder Paste"},
                {
                    0: "B.SilkS",
                    "type": "Bottom Silk Screen",
                    "material": "Liquid Photo",
                },
            ]
        }
        self.stackup = KiCADStackupManager(
            self.logger, layer_params, stackup_params
        )

    def test_stackupmanager_build_stackup(self):
        assert len(self.stackup.layers) == 11

    def test_stackupmanager_get_layer_names(self):
        assert list(self.stackup.get_layer_names()) == [
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
            "Edge.Cuts",
        ]

    def test_stackupmanager_get_layer(self):
        assert self.stackup.get_layer("F.Cu").name == "F.Cu"

    def test_stackupmanager_get_layer_type(self):
        assert self.stackup.get_layer("F.Cu").type == "signal"

    def test_stackupmanager_get_layers_from_pattern(self):
        # assert len(self.stackup.get_layers_from_pattern("F.Cu")) == 1
        top_copper = self.stackup.get_layers_from_pattern(["F.Cu"])
        for lay in top_copper:
            print(lay.name)
        assert len(top_copper) == 1
        assert len(self.stackup.get_layers_from_pattern(["*.Cu"])) == 2
        assert len(self.stackup.get_layers_from_pattern(["*.Cu", "B.Cu"])) == 2
        assert (
            len(self.stackup.get_layers_from_pattern(["*.Cu", "*.Mask"])) == 4
        )

    def test_stackupmanager_get_lowest_layer(self):
        assert (
            self.stackup.get_lowest_layer(["F.Cu", "B.Cu", "Edge.Cuts"]).name
            == "B.Cu"
        )
        assert (
            self.stackup.get_lowest_layer(
                list(self.stackup.get_layer_names())
            ).name
            == "B.SilkS"
        )

    def test_stackupmanager_get_highest_layer(self):
        assert (
            self.stackup.get_highest_layer(["F.Cu", "B.Cu", "Edge.Cuts"]).name
            == "F.Cu"
        )
        assert (
            self.stackup.get_highest_layer(
                list(self.stackup.get_layer_names())
            ).name
            == "F.SilkS"
        )

    def test_stackupmanager_get_stackup_layer_names(self):
        assert list(self.stackup.get_stackup_layer_names()) == [
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
