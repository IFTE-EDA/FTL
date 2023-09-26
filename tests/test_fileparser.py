import pytest
import sys
import os

# sys.path.append("../FTL")
sys.path.append(os.path.abspath(os.getcwd()))
import FTL
from FTL import FileParser

import os


class Test_FileParser:
    def setup_class(self):
        self.filename = os.path.join(
            os.path.abspath(os.getcwd()),
            "tests",
            "data",
            "Teststrip_DirBend.json",
        )
        self.parser = FileParser(self.filename)

    def test_attrs(self):
        assert self.parser.filename == self.filename
        assert self.parser.mel == 4
        assert self.parser.mel_residual == 4
        assert self.parser.mel_trans == 2
        assert self.parser.layers == []
        assert self.parser.meshes is None
        assert self.parser.rcFP is None
        assert self.parser.rcRender is None
        assert self.parser.transformations is None
        assert self.parser.transformer is None
        assert self.parser.j_data == {
            "version": 0.1,
            "mel": 4,
            "mel_trans": 2,
            "mel_residual": 4,
            "layers": [
                {
                    "name": "Teststrip",
                    "file": "Teststrip.stl",
                    "color": "green",
                    "mel": 3,
                    "mel_trans": 1,
                    "mel_residual": 3,
                }
            ],
            "transformations": [
                {
                    "name": "TR1_X",
                    "priority": 0,
                    "type": "DirBend",
                    "angle": 90,
                    "points": [
                        {"x": -20, "y": 10},
                        {"x": 0, "y": -10},
                        {"x": 60, "y": -10},
                        {"x": 60, "y": 10},
                    ],
                    "color": "blue",
                }
            ],
        }
        assert self.parser.j_layers[0] == {
            "color": "green",
            "file": "Teststrip.stl",
            "mel": 3,
            "mel_residual": 3,
            "mel_trans": 1,
            "name": "Teststrip",
        }

    def test_get_layer_id(self):
        assert self.parser.get_layer_id("Teststrip") == 0

    # def test_assignments(self):
    #    self.parser.calculate_assignments()
    #    print("Bla")
