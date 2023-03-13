import numpy as np
import shapely.geometry
import shapely.geometry.polygon
import vedo as v
from enum import Enum
import copy
from Transformation import *
from LinearTransformation import *

DIR = Enum('DIR', 'NEGY POSY NEGX POSX')
global MAX_EDGE_LENGTH


class ZBend(Transformation):

    def __init__(self, xmin, xmax, ymin, ymax, angle, dir, prio=0, addResidual=True, name=None):

        # debug("Transformation created")
        self.angle = np.deg2rad(angle)
        self.dir = dir
        # self.boundaries = shapely.geometry.box(xmin, ymin, xmax, ymax)
        self.boundaries = shapely.geometry.Polygon([[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]])
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.prio = prio
        self.addResidual = addResidual
        self.name = name
        self.parent = None
        # self.points = []
        self.meshes = []
        self.mel = []

        # self.super().__init__(self.boundaries, prio, addResidual, name)

    def __repr__(self):
        return "Tr.ZBEND: [D={}; P={}; Res={}; angle={}; x={}->{}, y={}->{}]".format(self.dir, self.prio,
                                                                                     self.addResidual, self.angle,
                                                                                     self.xmin, self.xmax, self.ymin,
                                                                                     self.ymax)

    def __str__(self):
        return "Tr.ZBEND: [D={}; P={}; Res={}; angle={}; x={}->{}, y={}->{}]".format(self.dir, self.prio,
                                                                                     self.addResidual, self.angle,
                                                                                     self.xmin, self.xmax, self.ymin,
                                                                                     self.ymax)

    def isInScope(self, point):
        pt = Point(point[0], point[1])
        if not pt.disjoint(self.boundaries):
            return True
        # else:
        #    debug(pt.__str__() + " out of scope")

    def getScope(self):
        if self.dir == DIR.NEGY or self.dir == DIR.POSY:
            return Rectangle((self.xmin - self.parent.mel, self.ymin - self.parent.mel),
                             (self.xmax + self.parent.mel, self.ymin + self.parent.mel)).extrude(
                self.parent.zmax - self.parent.zmin + 2 * self.parent.mel).z(self.parent.zmin - self.parent.mel)
        elif self.dir == DIR.NEGX or self.dir == DIR.POSX:
            return Rectangle((self.xmin - self.parent.mel, self.ymin - self.parent.mel),
                             (self.xmin + self.parent.mel, self.ymax + self.parent.mel)).extrude(
                self.parent.zmax - self.parent.zmin + 2 * self.parent.mel).z(self.parent.zmin - self.parent.mel)

    def getBorderScope(self, delta=None):
        if delta is None:
            delta = self.parent.mel

        if self.dir == DIR.NEGY:
            return [min(self.xmin, self.xmax) - delta, self.ymin + delta, max(self.xmin, self.xmax) + delta,
                    self.ymin - delta]
        elif self.dir == DIR.POSY:
            return [min(self.xmin, self.xmax) - delta, self.ymin - delta, max(self.xmin, self.xmax) + delta,
                    self.ymin + delta]
        elif self.dir == DIR.NEGX:
            return [self.xmin - delta, min(self.ymin, self.ymax) - delta, self.xmin + delta,
                    max(self.ymin, self.ymax) + delta]
        elif self.dir == DIR.POSX:
            return [self.xmin + delta, min(self.ymin, self.ymax) - delta, self.xmin - delta,
                    max(self.ymin, self.ymax) + delta]

        """
        if (self.dir == DIR.NEGY):
            return [self.xmin - delta, self.ymin + delta, self.xmax + delta, self.ymin - delta]
        elif (self.dir == DIR.POSY):
            return [self.xmin - delta, self.ymin - delta, self.xmax + delta, self.ymin + delta]
        elif (self.dir == DIR.NEGX):
            return [self.xmin + delta, self.ymin - delta, self.xmin - delta, self.ymax + delta]
        elif (self.dir == DIR.POSX):
            return [self.xmin - delta, self.ymin - delta, self.xmin + delta, self.ymax + delta]
        """

    def getOutlinePts(self):
        # pts = self.boundaries.exterior.coords[:-1]
        # pts[:, 2] = self.parent.zmaxi
        poly = shapely.geometry.polygon.orient(self.boundaries)
        # debug ("Poly is CCW: {}".format(poly.exterior.is_ccw))
        # x = self.boundaries.exterior.coords.xy[0][:-1]
        # y = self.boundaries.exterior.coords.xy[1][:-1]
        x = poly.exterior.coords.xy[0][:-1]
        y = poly.exterior.coords.xy[1][:-1]
        # x, y = self.boundaries.exterior.coords.xy[:][:-1]
        # z = [self.parent.zmax] * len(x)
        z = [0] * len(x)
        # pts = np.zeros((len(x), 3))  # zip(x, y, z)
        # pts[:][0] = x
        # pts[:][1] = y
        # pts[:][2] = z
        pts = list(zip(x, y, z))

        return pts

    def getOutline(self):
        return v.Line(self.getOutlinePts(), closed=True)

    def getBorderlinePts(self):
        pts = []
        if self.dir == DIR.NEGY:
            pts = [(self.xmin, self.ymin, 0), (self.xmax, self.ymin, 0)]
        elif self.dir == DIR.POSY:
            pts = [(self.xmin, self.ymin, 0), (self.xmax, self.ymin, 0)]
        elif self.dir == DIR.NEGX:
            pts = [(self.xmin, self.ymin, 0), (self.xmin, self.ymax, 0)]
        elif self.dir == DIR.POSX:
            pts = [(self.xmin, self.ymin, 0), (self.xmin, self.ymax, 0)]
        return pts

    def getBorderline(self):
        return Line(self.getBorderlinePts())

    def getResidualTransformation(self):
        if self.dir == DIR.NEGY:
            r = (self.ymax - self.ymin) / self.angle
            a = self.angle

            newTr = np.zeros((3, 4), dtype=float)
            newTr[0] = 1, 0, 0, 0
            newTr[1] = 0, cos(a), -sin(a), -self.ymax * cos(a) + self.ymin + r * (sin(a))
            newTr[2] = 0, sin(a), cos(a), self.ymax * sin(a) - r * (1 - cos(a))

            # newBounds = shapely.geometry.box(self.xmin, self.ymax, self.xmax, self.parent.ymin)
            newBounds = shapely.geometry.box(self.parent.xmin, self.ymax, self.parent.xmax, self.parent.ymin)
            ret = LinearTransformation(newTr, newBounds, self.prio, residual=True)
            # return LinearTransformation([[1, 0, 0, 10], [0, 1, 0, 0], [0, 0, 1, 5]], newBounds, self.prio)

        elif self.dir == DIR.POSY:
            r = (self.ymax - self.ymin) / self.angle
            a = self.angle

            newTr = np.zeros((3, 4), dtype=float)
            newTr[0] = 1, 0, 0, 0
            newTr[1] = 0, cos(a), -sin(a), -self.ymax * cos(a) + self.ymin + r * (sin(a))
            newTr[2] = 0, sin(a), cos(a), -self.ymax * sin(a) + r * (1 - cos(a))

            # newBounds = shapely.geometry.box(self.xmin, self.ymax, self.xmax, self.parent.ymax)
            newBounds = shapely.geometry.box(self.parent.xmin, self.ymax, self.parent.xmax, self.parent.ymax)
            return LinearTransformation(newTr, newBounds, self.prio, residual=True)

        elif self.dir == DIR.NEGX:
            r = (self.xmax - self.xmin) / self.angle
            a = self.angle

            newTr = np.zeros((3, 4), dtype=float)
            newTr[0] = cos(a), 0, -sin(a), -self.xmax * cos(a) + self.xmin + r * (sin(a))
            newTr[1] = 0, 1, 0, 0
            newTr[2] = sin(a), 0, cos(a), -self.xmax * sin(a) + r * (1 - cos(a))

            # newBounds = shapely.geometry.box(self.xmax, self.ymin, 650, -600)
            newBounds = shapely.geometry.box(self.xmax, self.parent.ymin, self.parent.xmin, self.parent.ymax)
            ret = LinearTransformation(newTr, newBounds, self.prio, residual=True)
        elif self.dir == DIR.POSX:
            r = (self.xmax - self.xmin) / self.angle
            a = self.angle

            newTr = np.zeros((3, 4), dtype=float)
            newTr[0] = cos(a), 0, -sin(a), -self.xmax * cos(a) + self.xmin + r * (sin(a))
            newTr[1] = 0, 1, 0, 0
            newTr[2] = sin(a), 0, cos(a), -self.xmax * sin(a) + r * (1 - cos(a))

            # newBounds = shapely.geometry.box(self.xmax, self.ymin, 650, -600)
            newBounds = shapely.geometry.box(self.xmax, self.parent.ymin, self.parent.xmax, self.parent.ymax)
            ret = LinearTransformation(newTr, newBounds, self.prio, residual=True)
        else:
            raise ValueError("Direction of ZBend-Transformation not found: {}".format(self.dir))
        ret.name = self.name + "-Res"
        return ret

    def getMatrixAt(self, pt):
        x = pt[0]
        y = pt[1]
        # z = pt[2]
        mat = np.zeros((3, 4), dtype=float)
        if self.dir == DIR.NEGY:
            r = (self.ymax - self.ymin) / self.angle
            t = (y - self.ymin) / (self.ymax - self.ymin)
            a = t * self.angle

            mat[0] = 1, 0, 0, 0
            mat[1] = 0, 0, sin(a), self.ymin + r * sin(a)
            mat[2] = 0, 0, cos(a), -(1 - cos(a)) * r
        elif self.dir == DIR.POSY:  # TODO
            r = (self.ymax - self.ymin) / self.angle
            t = (y - self.ymin) / (self.ymax - self.ymin)
            a = t * self.angle

            mat[0] = 1, 0, 0, 0
            mat[1] = 0, 0, -sin(a), self.ymin + r * sin(a)
            mat[2] = 0, 0, cos(a), (1 - cos(a)) * r
        elif self.dir == DIR.NEGX:
            r = (self.xmax - self.xmin) / self.angle
            t = (x - self.xmin) / (self.xmax - self.xmin)
            a = t * self.angle

            mat[0] = 0, 0, -sin(a), self.xmin + r * sin(a)
            mat[1] = 0, 1, 0, 0
            mat[2] = 0, 0, cos(a), (1 - cos(a)) * r
        elif self.dir == DIR.POSX:  # TODO
            r = abs(self.xmax - self.xmin) / self.angle
            t = abs(x - self.xmin) / abs(self.xmax - self.xmin)
            a = t * self.angle

            mat[0] = 0, 0, -sin(a), self.xmin + r * sin(a)
            mat[1] = 0, 1, 0, 0
            mat[2] = 0, 0, cos(a), (1 - cos(a)) * r
        return mat
