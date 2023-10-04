from pathlib import Path
import sys
import os

# sys.path.append("../FTL")
sys.path.append(os.path.abspath(os.getcwd()))
import FTL
from FTL import FileParser
import pytest

import os


class Test_FileParser:
    def setup_class(self):
        self.filename = (
            Path(__file__).parent / "data" / "Teststrip_DirBend.json"
        )
        self.parser = FileParser(self.filename)
        self.parser.parse()

    @pytest.mark.order(0)
    def test_attrs(self):
        assert self.parser.filename == self.filename
        assert self.parser.mel == 4
        assert self.parser.mel_residual == 4
        assert self.parser.mel_trans == 2
        assert len(self.parser.layers) == 1
        assert self.parser.meshes == []
        assert self.parser.rcFP is None
        assert self.parser.rcRender is None
        assert self.parser.transformations == []
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

    @pytest.mark.order(-1)
    def test_assignments(self):
        transformer = self.parser.transformer
        assert len(transformer.debugOutput) == 0
        assert len(transformer.fixed_mesh) == 0
        assert len(transformer.layers) == 1
        self.parser.calculate_assignments()
        assert type(self.parser.transformer.transformations[0]) is FTL.DirBend
        assert transformer.transformations[0].boundaries.bounds == (
            -20.0,
            -10.0,
            60.0,
            10.0,
        )
        assert transformer.transformations[0].addResidual
        assert transformer.transformations[0].isResidual is False
        assert transformer.transformations[0].pivot == [-20.0, 10.0, 0]
        assert transformer.transformations[0].prio == 0
        assert transformer.transformations[0].parent == transformer
        assert type(transformer.transformations[1]) is FTL.LinearTransformation
        assert transformer.transformations[1].boundaries.bounds == (
            -20.0,
            10.0,
            80.0,
            110.0,
        )
        assert transformer.transformations[1].addResidual is False
        assert transformer.transformations[1].isResidual
        assert transformer.transformations[1].prio == 0
        assert transformer.transformations[1].parent == transformer

        assert len(transformer.fixed_mesh) == 1
        assert get_mesh_extent(transformer.fixed_mesh[0]) == (
            (-50.0, -5.0),
            (-5.0, 5.0),
            (-0.5, 0.5),
        )
        assert get_mesh_extent(transformer.transformations[0].meshes[0]) == (
            (-50.0, 50.0),
            (-5.0, 5.0),
            (-0.5, 0.5),
        )


def get_mesh_extent(mesh):
    pts = mesh.points()
    xpts = pts[:, 0]
    ypts = pts[:, 1]
    zpts = pts[:, 2]
    return (
        (min(xpts), max(xpts)),
        (min(ypts), max(ypts)),
        (min(zpts), max(zpts)),
    )


if __name__ == "__main__":
    tester = Test_FileParser()
    tester.setup_class()
    tester.test_attrs()
