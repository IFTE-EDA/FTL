import json
from ZBend import *
from MatrixTransformer import *
from MeshLayer import *
import vedo as v

class FileParser:
    def __init__(self, filename):
        self.filename = filename
        print("Reading data from file ''".format(filename))
        f = open(filename)
        self.j_data = json.load(f)

        self.mel = self.j_data["mel"]
        self.mel_trans = self.j_data["mel_trans"]
        self.mel_residual = self.j_data["mel_residual"]
        self.j_layers = self.j_data["layers"]
        self.j_transformations = self.j_data["transformations"]
        self.layers = []
        f.close()

    def parse(self):
        print("Found {} layers and {} transformations. Global MEL: [{}/{}/{}]".format(len(self.j_layers), len(self.j_transformations), self.mel, self.mel_trans, self.mel_residual))
        self.transformer = MatrixTransformer()
        self.meshes = []
        self.transformations = []
        for i, layer in enumerate(self.j_layers):
            layerObj = MeshLayer.get_from_JSON(layer, self, i)
            #mesh = v.load(layer["file"])
            #layerObj = MeshLayer(mesh, layer, self, i)
            self.layers.append(layerObj)
            self.transformer.add_layer(layerObj)
            print("  Found layer #{} '{}' with MEL [{}/{}/{}], reading data from file '{}'".format(i, layer["name"], layerObj.mel, layerObj.mel_trans, layerObj.mel_residual, layer["file"]))
            self.meshes.append(mesh)

        meshNumStr = "/".join([str(layer.mesh.npoints) for layer in self.transformer.layers])

        print("Transformer created. Imported {} layers with {} points.".format(self.transformer.nlayers, meshNumStr))

        print("\nAll layers imported. Reading transformations...")

        for i, tr in enumerate(self.j_transformations):
            if "color" in tr:
                color = tr["color"]
            else:
                color = None
            print("  Found transformation #{} '{}' of type {} with priority {} and color '{}'".format(len(self.transformer.transformations), tr["name"], tr["type"], tr["priority"], color))
            if (tr["type"] == "ZBend"):
                if (tr["dir"] == "POSX"):
                    dir = DIR.POSX
                elif (tr["dir"] == "NEGX"):
                    dir = DIR.NEGX
                elif (tr["dir"] == "POSY"):
                    dir = DIR.POSY
                elif (tr["dir"] == "NEGY"):
                    dir = DIR.NEGY
                else:
                    raise ValueError("Direction of ZBend-Transformation not found: {}".format(self.dir))

                trans = ZBend(tr["xmin"], tr["xmax"], tr["ymin"], tr["ymax"], tr["angle"], dir)
                print("  -> dir={};  angle={};  x = {}...{};  y = {}...{};".format(tr["dir"], tr["angle"], tr["xmin"], tr["xmax"], tr["ymin"], tr["ymax"]))
            else:
                raise TypeError("Unknown transformation type.")
            trans.color = color
            print("  - Adding Transformation {}".format(trans))
            #self.transformations.append(trans)
            self.transformer.add_transformation(trans)

        print("\nDone parsing.\n\n")

    def __str__(self):
        pass

    def get_layer_id(self, name):
        idList = self.j_layers[:]["name"]
        return idList.index(name)

    def calculate_assignments(self, onlybaselayer=False):
        self.transformer.calculate_assignments(onlybaselayer)

    def visualize(self, plt):
        self.transformer.visualize(plt)
        #plt.show(self.meshes[0].c("grey"), self.meshes[1].c("orange"), self.transformer.borderEdges, self.transformer.debugOutput)

    def render(self):
        print("\nRendering...")
        self.transformer.start_transformation()
        #newPoints = self.transformer.start_transformation()
        #for i, mesh in enumerate(newPoints):
        #    self.meshes[i].points(mesh)
        #    newFilename = "{}_{}.stl".format(self.filename[:-5], self.j_layers[i]["name"])
        #    print("Saving layer #{} in '{}'".format(i, newFilename))
         #   write(self.meshes[i], newFilename)
        ret = self.transformer.get_result_mesh()
        return ret
