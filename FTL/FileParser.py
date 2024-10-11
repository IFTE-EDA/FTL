import json
import logging
import os

import vedo as v
from PyQt6 import QtCore
import shapely as sh

from .MatrixTransformer import MatrixTransformer
from .MeshLayer import MeshLayer

from .Transformations import (
    DirBend,
    LinearTransformation,
    Spiral,
    Transformation,
    ZBend,
    DIR,
)

# import .Transformations.ZBend


class FileParser(QtCore.QObject):
    def __init__(self, filename):
        super().__init__()
        self.transformations = []
        self.layers = []
        self.meshes = []
        self.transformer = None
        self.filename = filename
        logging.debug("Reading data from file '{}'".format(filename))
        with open(filename) as f:
            self.j_data = json.load(f)

        self.j_data["filename"] = filename
        self.mel = self.j_data["mel"]
        self.mel_trans = self.j_data["mel_trans"]
        self.mel_residual = self.j_data["mel_residual"]
        self.j_layers = self.j_data["layers"]
        self.j_transformations = self.j_data["transformations"]

        self.rcFP = None
        self.rcRender = None

    progress = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)

    # def updateParams(self):

    def parse(self):
        self.progress.emit(0)

        logging.debug(
            "Found {} layers and {} transformations. Global MEL: [{}/{}/{}]".format(
                len(self.j_layers),
                len(self.j_transformations),
                self.mel,
                self.mel_trans,
                self.mel_residual,
            )
        )
        self.transformer = MatrixTransformer()
        self.transformer.status.connect(self.status)
        self.transformer.progress.connect(self.progress)

        for i, layer in enumerate(self.j_layers):
            layerObj = MeshLayer.get_from_JSON(layer, self, i)
            mesh_file = os.path.join(
                os.path.dirname(self.filename), layer["file"]
            )
            layerObj.load_mesh(mesh_file)
            # mesh = v.load(layer["file"])
            # layerObj = MeshLayer(mesh, layer, self, i)
            self.layers.append(layerObj)
            self.transformer.add_layer(layerObj)
            logging.debug(
                "  Found layer #{} '{}' with MEL [{}/{}/{}] and color '{}', reading data from file '{}'".format(
                    i,
                    layer["name"],
                    layerObj.mel,
                    layerObj.mel_trans,
                    layerObj.mel_residual,
                    layerObj.color,
                    layer["file"],
                )
            )

        meshNumStr = "/".join(
            [str(layer.mesh.npoints) for layer in self.layers]
        )

        logging.debug(
            "Transformer created. Imported {} layers with {} points.".format(
                self.transformer.nlayers, meshNumStr
            )
        )

        logging.debug("\nAll layers imported. Reading transformations...")

        for i, tr in enumerate(self.j_transformations):
            if "color" in tr:
                color = tr["color"]
            else:
                color = None
            logging.debug(
                "  Found transformation #{} '{}' of type {} with priority {} and color '{}'".format(
                    len(self.transformer.transformations),
                    tr["name"],
                    tr["type"],
                    tr["priority"],
                    color,
                )
            )
            if tr["type"] == "ZBend":
                if tr["dir"] == "POSX":
                    logging.debug("Found POSX")
                    dir = DIR.POSX
                elif tr["dir"] == "NEGX":
                    dir = DIR.NEGX
                elif tr["dir"] == "POSY":
                    dir = DIR.POSY
                elif tr["dir"] == "NEGY":
                    dir = DIR.NEGY
                else:
                    raise ValueError(
                        "Direction of ZBend-Transformation not found: {}".format(
                            tr["dir"]
                        )
                    )
                trans = ZBend(
                    int(tr["xmin"]),
                    int(tr["xmax"]),
                    int(tr["ymin"]),
                    int(tr["ymax"]),
                    int(tr["angle"]),
                    dir,
                    name=tr["name"],
                )
                logging.debug(
                    "  -> dir={};  angle={};  x = {}...{};  y = {}...{};".format(
                        tr["dir"],
                        tr["angle"],
                        tr["xmin"],
                        tr["xmax"],
                        tr["ymin"],
                        tr["ymax"],
                    )
                )
            elif tr["type"] == "DirBend":
                trans = DirBend(tr, name=tr["name"])
                self.transformer.rcFP.add_debug(
                    "Debug_Trans", trans.debugShow(), True
                )

            elif tr["type"] == "Spiral":
                trans = Spiral(tr, name=tr["name"])
                self.transformer.rcFP.add_debug(
                    "Debug_Trans", trans.debugShow(), True
                )

            else:
                raise TypeError("Unknown transformation type.")
            trans.color = color
            logging.debug("  - Adding Transformation {}".format(trans))
            # self.transformations.append(trans)
            self.transformer.add_transformation(trans)

        logging.debug("\nDone parsing.\n\n")
        self.progress.emit(100)

    def __str__(self):
        pass

    def get_layer_id(self, name):
        idList = [e["name"] for e in self.j_layers]
        return idList.index(name)

    def calculate_assignments(self, onlybaselayer=False):
        self.transformer.calculate_assignments(onlybaselayer)

    def visualize(self):
        self.transformer.visualize()

    def render(self):
        logging.debug("\nRendering...")
        self.transformer.start_transformation()
        ret = self.transformer.get_result_mesh()
        return ret
