from __future__ import annotations
import sys
import os
import math
from pathlib import Path

import gmsh
import numpy as np

from FTL.parse.KiCADParser import KiCADParser


def get_file(file_name: str):
    return Path(__file__).parent.parent.parent / "data" / file_name


PRECISION_DIGITS = 2


class Test_KiCadStackupManager:
    def setup_class(self):
        pass

    def test_kicadparser_list_layers(self):
        parser = KiCADParser(get_file("layers.kicad_pcb"))
        layers = list(parser.stackup.get_layer_names())
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

    def test_kicadparser_layer_has_objects(self):
        parser = KiCADParser(get_file("layers.kicad_pcb"))
        layer = parser.stackup.get_layer("F.Cu")
        assert layer.has_objects()
