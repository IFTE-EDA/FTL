from vedo import *
import shapely
from shapely.geometry import Point, Polygon, LineString, GeometryCollection

class Transformation:

    def __init__(self, bounds, prio=0, addResidual=True, name=None):
        #debug("Transformation created")
        self.boundaries = bounds
        self.prio = prio
        self.addResidual = addResidual
        self.isResidual = False
        #self.color = None
        self.color = [255, 255, 0, 255]
        #self.points = []
        self.meshes = []
        self.mel = []
        self.scope = None
        self.parent = None
        self.name = name

    def __str__(self):
        debug("Transformation")

    def getOutline(self):
        #pts = self.boundaries.exterior.coords[:-1]
        #pts[:, 2] = self.parent.zmaxi
        x = self.boundaries.exterior.coords.xy[0][:-1]
        y = self.boundaries.exterior.coords.xy[1][:-1]
        #x, y = self.boundaries.exterior.coords.xy[:][:-1]
        z = [self.parent.zmax] * len(x)
        pts = np.zeros((len(x), 3))   #zip(x, y, z)
        #pts[:][0] = x
        #pts[:][1] = y
        #pts[:][2] = z
        pts = x, y, z

    def get_preprocessed_mesh(self, layerId):
        debug ("    Transformation {}\n     -> layer {}/{}".format(self, layerId, len(self.mel)))
        return self.meshes[layerId].clone().subdivide(1, 2, self.mel[layerId])

    def getAffectedPoints(self):
        raise NotImplementedError("Please implement the function in a new class.")

    def getMatrixAt(self):
        raise NotImplementedError("Please implement the function in a new class.")

    def isInScope(self, point):
        raise NotImplementedError("Please implement the function in a new class.")

    def getResidualTransformation(self):
        raise NotImplementedError("Please implement the function in a new class.")
    def getBorderline(self):
        raise NotImplementedError("Please implement the function in a new class.")

