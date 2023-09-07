import numpy as np
import vedo as v
from shapely import Point
from Transformation import Transformation


class LinearTransformation(Transformation):
    def __init__(
        self,
        mat,
        bounds,
        prio=0,
        residual=False,
        name=None,
        angle=0,
        pivot=None,
    ):
        # super().__init__(bounds, prio, not residual, name=name)
        super().__init__(bounds, prio, False)
        self.name = name
        self.residual = False
        self.mat = mat
        self.boundaries = bounds
        # shapely.geometry.box(xmin, ymin, xmax, ymax)
        self.prio = prio
        self.isResidual = residual
        self.z_angle = angle
        self.pivot = pivot
        if angle and pivot:
            self.transformWholeMesh = True

    def __repr__(self):
        return "Tr.Lin: [P={}; Res={}; bounds: {}]".format(
            self.prio, self.addResidual, self.boundaries
        )

    def __str__(self):
        return "Tr.Lin: [P={}; Res={}; bounds: {}]".format(
            self.prio, self.addResidual, self.boundaries
        )

    def isInScope(self, point):
        pt = Point(point[0], point[1])
        if not pt.disjoint(self.boundaries):
            return True

    def transformMesh(self, mesh):
        mesh.rotate_z(self.z_angle, rad=True, around=self.pivot)
        points = mesh.points()
        for pid, pt in enumerate(points):
            vec = np.array([pt[0], pt[1], pt[2], 1])
            vec = np.dot(self.mat, vec)
            points[pid][0] = vec[0]
            points[pid][1] = vec[1]
            points[pid][2] = vec[2]
        mesh.points(points)
        mesh.rotate_z(-self.z_angle, rad=True, around=self.pivot)
        return mesh

    def getMatrixAt(self, pt):
        return self.mat
