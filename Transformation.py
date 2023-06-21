import vedo as v
import shapely
from shapely.geometry import Point, Polygon, LineString, GeometryCollection


class Transformation:

    def __init__(self, bounds, prio=0, addResidual=True, name=None):
        # debug("Transformation created")
        self.boundaries = bounds
        self.prio = prio
        self.addResidual = addResidual
        self.isResidual = False
        # self.color = None
        self.color = [255, 255, 0, 255]
        # self.points = []
        self.meshes = []
        self.mel = []
        self.scope = None
        self.parent = None
        self.name = name
        self.transformWholeMesh = False

    def __str__(self):
        print("Transformation")

    def getOutline(self):
        x = self.boundaries.exterior.coords.xy[0][:-1]
        y = self.boundaries.exterior.coords.xy[1][:-1]
        z = [self.parent.zmax] * len(x)
        #pts = np.zeros((len(x), 3))  # zip(x, y, z)
        pts = list(zip(x, y, z))
        return pts

    def get_preprocessed_mesh(self, layerId):
        print("    Transformation {}\n     -> layer {}/{}".format(self, layerId, len(self.mel)))
        return self.meshes[layerId].clone().subdivide(1, 2, self.mel[layerId])

    def getArea(self):
        return self.getOutline().triangulate().lw(0)

    def getAffectedPoints(self):
        raise NotImplementedError("Please implement the function in a new class.")

    def getMatrixAt(self, pt):
        raise NotImplementedError("Please implement the function in a new class.")

    def isInScope(self, point):
        raise NotImplementedError("Please implement the function in a new class.")

    def getResidualTransformation(self):
        raise NotImplementedError("Please implement the function in a new class.")

    def getBorderline(self):
        raise NotImplementedError("Please implement the function in a new class.")
