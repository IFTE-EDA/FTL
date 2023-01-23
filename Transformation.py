from vedo import *
import shapely
from shapely.geometry import Point, Polygon, LineString, GeometryCollection

class Transformation:

    def __init__(self, bounds, prio=0, addResidual=True):
        #print("Transformation created")
        self.boundaries = bounds
        self.prio = prio
        self.addResidual = addResidual
        #self.color = None
        self.color = [255, 255, 0, 255]
        self.points = []
        self.parent = None

    def __str__(self):
        print("Transformation")

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

    def getAffectedPoints(self):
        pass

    def getMatrixAt(self):
        pass

    def isInScope(self, point):
        pass

    def getResidualTransformation(self):
        pass
    def getBorderline(self, delta):
        pass

