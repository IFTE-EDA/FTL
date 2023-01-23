import numpy as np
from vedo import *
from Transformation import *

class LinearTransformation(Transformation):

    def __init__(self, mat, bounds, prio=0):
        super().__init__(self, bounds, prio)
        self.residual = False
        self.mat = mat
        self.boundaries = bounds
        #shapely.geometry.box(xmin, ymin, xmax, ymax)
        self.prio = prio

    def __repr__(self):
        return "Tr.Lin: [P={}; Res={}; bounds: {}]".format(self.prio, self.addResidual, self.boundaries)

    def __str__(self):
        return "Tr.Lin: [P={}; Res={}; bounds: {}]".format(self.prio, self.addResidual, self.boundaries)

    def isInScope(self, point):
        #if (self.boundaries[0][0] <= pt[0] and pt[0] <= self.boundaries[0][1] and self.boundaries[1][0] <= pt[1] and pt[1] <= self.boundaries[1][1] and self.boundaries[2][0] <= pt[2] and pt[2] <= self.boundaries[2][1]):
        pt = Point(point[0], point[1])
        if (not pt.disjoint(self.boundaries)):
            return True

    def getMatrixAt(self, pt):
        return self.mat
        #return [[1, 0, 0, 10], [0, 1, 0, 0], [0, 0.1, 1, 0]]
