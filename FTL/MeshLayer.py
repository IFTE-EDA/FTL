from enum import Enum
import copy
import os
import logging

import numpy as np
import shapely as sh
import vedo as v


class MeshLayer:
    def __init__(self, data, parser, id=None):
        self.j_data = data
        self.parser = parser
        self.file = data["file"]
        self.name = data["name"]
        self.color = data.get("color", "grey")
        if id is None:
            self.layer_id = parser.get_layer_id(self.name)
            print("LayerID: " + str(self.layer_id))
        self.layer_id = id
        # self.mesh = mesh

        logging.debug(
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

        logging.debug(
            "Layer done. MEL: {}/{}/{}".format(
                self.mel, self.mel_trans, self.mel_residual
            )
        )

    def load_mesh(self, file):
        if not os.path.isfile(file):
            raise Exception("File not found:", file)
        self.mesh = v.load(file).clean()

    @classmethod
    def get_from_JSON(cls, data, parser=None, id=None, input_file=None):
        logging.debug("Creating layer from JSON data:")
        logging.debug(data)
        inst = cls(data, parser, id)
        return inst
