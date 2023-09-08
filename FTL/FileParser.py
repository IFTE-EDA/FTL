import json
import vedo as v
from PyQt6 import QtCore

# from shapely import geometry
from shapely.geometry import Point, Polygon, LineString, GeometryCollection
import FTL


class FileParser(QtCore.QObject):
    def __init__(self, filename, rcFP=None, rcRender=None, showProgress=False):
        super().__init__()
        self.transformations = None
        self.meshes = None
        self.transformer = None
        self.filename = filename
        FTL.debug("Reading data from file '{}'".format(filename))
        f = open(filename)
        self.j_data = json.load(f)
        f.close()

        self.mel = self.j_data["mel"]
        self.mel_trans = self.j_data["mel_trans"]
        self.mel_residual = self.j_data["mel_residual"]
        self.j_layers = self.j_data["layers"]
        self.j_transformations = self.j_data["transformations"]
        self.layers = []

        self.rcFP = rcFP
        self.rcRender = rcRender
        self.showProgress = showProgress

    progress = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)

    # def updateParams(self):

    def parse(self):
        self.progress.emit(0)

        FTL.debug(
            "Found {} layers and {} transformations. Global MEL: [{}/{}/{}]".format(
                len(self.j_layers),
                len(self.j_transformations),
                self.mel,
                self.mel_trans,
                self.mel_residual,
            )
        )
        self.transformer = FTL.MatrixTransformer(self.rcFP, self.rcRender)
        self.transformer.status.connect(self.status)
        self.transformer.progress.connect(self.progress)
        self.meshes = []
        self.transformations = []

        for i, layer in enumerate(self.j_layers):
            layerObj = FTL.MeshLayer.get_from_JSON(layer, self, i)
            # mesh = v.load(layer["file"])
            # layerObj = MeshLayer(mesh, layer, self, i)
            self.layers.append(layerObj)
            self.transformer.add_layer(layerObj)
            FTL.debug(
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
            [str(layer.mesh.npoints) for layer in self.transformer.layers]
        )

        FTL.debug(
            "Transformer created. Imported {} layers with {} points.".format(
                self.transformer.nlayers, meshNumStr
            )
        )

        FTL.debug("\nAll layers imported. Reading transformations...")

        for i, tr in enumerate(self.j_transformations):
            if "color" in tr:
                color = tr["color"]
            else:
                color = None
            FTL.debug(
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
                    print("Found POSX")
                    dir = FTL.DIR.POSX
                elif tr["dir"] == "NEGX":
                    dir = FTL.DIR.NEGX
                elif tr["dir"] == "POSY":
                    dir = FTL.DIR.POSY
                elif tr["dir"] == "NEGY":
                    dir = FTL.DIR.NEGY
                else:
                    raise ValueError(
                        "Direction of ZBend-Transformation not found: {}".format(
                            tr["dir"]
                        )
                    )
                trans = FTL.ZBend(
                    int(tr["xmin"]),
                    int(tr["xmax"]),
                    int(tr["ymin"]),
                    int(tr["ymax"]),
                    int(tr["angle"]),
                    dir,
                    name=tr["name"],
                )
                FTL.debug(
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
                trans = FTL.DirBend(tr, name=tr["name"])
                self.transformer.rcFP.add_debug(
                    "Debug_Trans", trans.debugShow(), True
                )

            elif tr["type"] == "Spiral":
                trans = FTL.Spiral(tr, name=tr["name"])
                self.transformer.rcFP.add_debug(
                    "Debug_Trans", trans.debugShow(), True
                )

            else:
                raise TypeError("Unknown transformation type.")
            trans.color = color
            FTL.debug("  - Adding Transformation {}".format(trans))
            # self.transformations.append(trans)
            self.transformer.add_transformation(trans)

        FTL.debug("\nDone parsing.\n\n")
        self.progress.emit(100)

    def __str__(self):
        pass

    def get_layer_id(self, name):
        idList = self.j_layers[:]["name"]
        return idList.index(name)

    def calculate_assignments(self, onlybaselayer=False):
        self.transformer.calculate_assignments(onlybaselayer)

    def visualize(self):
        self.transformer.visualize()

    def render(self):
        FTL.debug("\nRendering...")
        self.transformer.start_transformation()
        ret = self.transformer.get_result_mesh()
        return ret
