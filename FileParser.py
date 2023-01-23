import json
from ZBend import *
from MatrixTransformer import *
import vedo as v

class FileParser:
    def __init__(self, filename):
        self.filename = filename
        print("Reading data from file ''".format(filename))
        f = open(filename)
        self.j_data = json.load(f)

        self.mel_general = self.j_data["mel_general"]
        self.mel_trans = self.j_data["mel_trans"]
        self.mel_residual = self.j_data["mel_residual"]
        self.j_layers = self.j_data["layers"]
        self.j_transformations = self.j_data["transformations"]
        f.close()

    def parse(self):
        print("Found {} layers and {} transformations. Global MEL: [{}/{}/{}]".format(len(self.j_layers), len(self.j_transformations), self.mel_general, self.mel_trans, self.mel_residual))

        self.meshes = []
        self.transformations = []
        for i, layer in enumerate(self.j_layers):
            if "mel_general" in layer:
                mel_general = layer["mel_general"]
            else:
                mel_general = self.j_data["mel_general"]
            if "mel_trans" in layer:
                mel_trans = layer["mel_trans"]
            else:
                mel_trans = self.j_data["mel_trans"]
            if "mel_residual" in layer:
                mel_residual = layer["mel_residual"]
            else:
                mel_residual = self.j_data["mel_residual"]

            print("  Found layer #{} '{}' with MEL [{}/{}/{}], reading data from file '{}'".format(i, layer["name"], mel_general, mel_trans, mel_residual, layer["file"]))

            mesh = v.load(layer["file"]).subdivide(1, 2, mel_general).clean()
            self.meshes.append(mesh)

        self.transformer = MatrixTransformer(self.meshes, self.mel_general)

        print("\nAll layers imported. Reading transformations...")

        for i, tr in enumerate(self.j_transformations):
            if "color" in tr:
                color = tr["color"]
            else:
                color = None
            print("  Found transformation #{} '{}' of type {} with priority {} and color '{}'".format(i, tr["name"], tr["type"], tr["priority"], color))
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

        print("\nDone parsing.")

    def __str__(self):
        pass

    def calculate_assignments(self):
        self.transformer.calculate_assignments()

    def visualize(self, plt):
        self.transformer.visualize(plt)
        #plt.show(self.meshes[0].c("grey"), self.meshes[1].c("orange"), self.transformer.borderEdges, self.transformer.debugOutput)

    def render(self):
        print("\nRendering...")
        newPoints = self.transformer.start_transformation()
        for i, mesh in enumerate(newPoints):
            self.meshes[i].points(mesh)
            newFilename = "{}_{}.stl".format(self.filename[:-5], self.j_layers[i]["name"])
            print("Saving layer #{} in '{}'".format(i, newFilename))
            write(self.meshes[i], newFilename)
