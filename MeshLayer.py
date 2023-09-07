import numpy as np
import shapely.geometry
import shapely.geometry.polygon
import vedo as v

# from MatrixTransformer import MatrixTransformer, debug
from enum import Enum
import copy
from Transformation import *
import os


class MeshLayer:
    def __init__(self, mesh, data, parser, id=None):
        self.j_data = data
        self.parser = parser
        self.file = data["file"]
        self.name = data["name"]
        # self.color = data["color"] | "grey"
        self.color = data.get("color", "grey")
        if id is None:
            self.layer_id = parser.get_layer_id(self.name)
        self.layer_id = id
        self.mesh = mesh

        print(
            "Created layer '{}' with id #{}".format(self.name, self.layer_id)
        )

        if data["mel"] is None:
            if parser.j_data["mel"] is None:
                raise Exception("No MEL specified.")
            else:
                self.mel = parser.j_data["mel"]
        else:
            self.mel = data["mel"]
        if data["mel_trans"] is None:
            if parser.j_data["mel_trans"] is None:
                raise Exception("No MEL_TRANS specified.")
            else:
                self.mel_trans = parser.j_data["mel_trans"]
        else:
            self.mel_trans = data["mel_trans"]
        if data["mel_residual"] is None:
            if parser.j_data["mel_residual"] is None:
                raise Exception("No MEL_RESIDUAL specified.")
            else:
                self.mel_residual = parser.j_data["mel_residual"]
        else:
            self.mel_residual = data["mel_residual"]

        self.mel_residual = data["mel_residual"]

        print(
            "Layer done. MEL: {}/{}/{}".format(
                self.mel, self.mel_trans, self.mel_residual
            )
        )

    @classmethod
    def get_from_JSON(cls, data, parser=None, id=None):
        if not os.path.isfile(data["file"]):
            raise Exception("File not found:", data["file"])
        mesh = v.load(data["file"]).subdivide(0, 2, mel=2).clean()
        inst = cls(mesh, data, parser, id)
        return inst
