import numpy as np
import shapely
#from shapely import LineString, Point, Polygon
from shapely.geometry import Point, Polygon
import shapely.geometry.polygon
from shapely.ops import nearest_points
import vedo as v
from enum import Enum
import copy
from Transformation import *
from LinearTransformation import *

DIR = Enum('DIR', 'NEGY POSY NEGX POSX')#
global MAX_EDGE_LENGTH


class DirBend(Transformation):

    #def __init__(self, boundaries, baseline, length, angle, prio=0, addResidual=True, name=None):
    def __init__(self, data, prio=0, addResidual=True, name=None):

        self.prio = prio
        self.addResidual = addResidual
        self.name = name
        self.parent = None

        if "points" in data:  # found point data; prioritize those
            if len(data["points"]) < 4:
                raise ValueError("Not enough points in points array of transformation {}: {} (expecting 4+)".format(data["name"], len(data["points"])))
            poly = Polygon([[p["x"], p["y"]] for p in data["points"]])
            baseline = LineString(((data["points"][0]["x"], data["points"][0]["y"]), (data["points"][1]["x"], data["points"][1]["y"])))

            minx, miny, maxx, maxy = poly.bounds
            bounding_box = shapely.geometry.box(minx, miny, maxx, maxy)
            ax, ay, bx, by = baseline.bounds
            if ax == bx:  # vertical line
                extended_line = LineString([(ax, miny), (ax, maxy)])
            elif ay == by:  # horizonthal line
                extended_line = LineString([(minx, ay), (maxx, ay)])
            else:
                # linear equation: y = k*x + m
                m = -(ay - by) / (ax - bx)
                n = ay - m * ax + (by-ay)
                y0 = m * minx + n
                y1 = m * maxx + n
                x0 = (miny - n) / m
                x1 = (maxy - n) / m
                print ("m: {}; n: {}; P1({}, {}), 2({}, {})".format(m, n, x0, y0, x1, y1))
                print("Angle is {}".format(np.arctan(m)/(2*np.pi)*360))
                #points_on_boundary_lines = [Point(minx, y0), Point(maxx, y1), Point(x0, miny), Point(x1, maxy)]
                #points_sorted_by_distance = sorted(points_on_boundary_lines, key=bounding_box.distance)
                #self.extLine = LineString(points_sorted_by_distance[:2])
                self.extLine = LineString((Point(minx, y0), Point(maxx, y1)))

            #dists = [baseline.distance(Point(p)) for p in poly.exterior.coords]
            dists = [self.extLine.distance(Point(p)) for p in poly.exterior.coords]
            distPoints = [(dists[i], poly.exterior.coords[i]) for i in range(len(poly.exterior.coords)) if dists[i] > 0]

            points_sorted_by_distance = sorted(distPoints, key=lambda x: x[0])
            #length = self.extLine.distance(points_sorted_by_distance[0])  #TODO
            length = points_sorted_by_distance[0][0]
            print(">>min: {}".format(length))
            self.projPoint, _ = nearest_points(self.extLine, Point(points_sorted_by_distance[0][1]))
            self.ortho = LineString([self.projPoint, Point(points_sorted_by_distance[0][1])])
            #self.projPoint = self.extLine.project(Point(points_sorted_by_distance[0][1]))
            print(self.projPoint)
            #print(poly)
            #print(baseline)
        else:
            raise ValueError("Not enough data for Transformation {}".format(self.name))

        # debug("Transformation created")
        self.angle = np.deg2rad(data["angle"])
        self.z_angle = np.arctan((bx-ax)/(ay-by))
        print("Z_ANGLE: {}".format(np.rad2deg(self.z_angle)))
        #self.dir = dir
        self.boundaries = poly
        # self.boundaries = shapely.geometry.box(xmin, ymin, xmax, ymax)
        # self.boundaries = shapely.geometry.Polygon([[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]])
        """
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        """
        self.baseline = baseline
        self.length = length
        # self.points = []
        self.meshes = []
        self.mel = []

        # self.super().__init__(self.boundaries, prio, addResidual, name)

    def __repr__(self):
        return "Tr.DirBend: [P={}; Res={}; angle={}; len={}; baseline={}; bounds={}]".format(self.prio, self.addResidual, self.angle, self.length, self.baseline, self.boundaries)

    def __str__(self):
        return "Tr.DirBend: [P={}; Res={}; angle={}; len={}; baseline={}; bounds={}]".format(self.prio, self.addResidual, self.angle, self.length, self.baseline, self.boundaries)

    def debugShow(self):
        def getPoints(obj):
            x = obj.coords.xy[0]
            y = obj.coords.xy[1]
            z = [0] * len(x)
            pts = list(zip(x, y, z))
            return pts

        #bl = v.Line(getPoints(self.baseline), closed=False).c("Red")
        ext = v.Line(getPoints(self.extLine), closed=False).c("Blue")
        ortho = v.Line(getPoints(self.ortho), closed=False).c("Yellow")
        perp = v.Point((self.projPoint.x, self.projPoint.y, 0), r=12, c="Red")

        #print(self.baseline)
        print(self.extLine)
        return v.merge(ext, perp, ortho)

    def isInScope(self, point):
        pt = Point(point[0], point[1])
        if not pt.disjoint(self.boundaries):
            return True
        # else:
        #    debug(pt.__str__() + " out of scope")

    def getScope(self):
        return self.boundaries

        if self.dir == DIR.NEGY or self.dir == DIR.POSY:
            return Rectangle((self.xmin - self.parent.mel, self.ymin - self.parent.mel),
                             (self.xmax + self.parent.mel, self.ymin + self.parent.mel)).extrude(
                self.parent.zmax - self.parent.zmin + 2 * self.parent.mel).z(self.parent.zmin - self.parent.mel)
        elif self.dir == DIR.NEGX or self.dir == DIR.POSX:
            return Rectangle((self.xmin - self.parent.mel, self.ymin - self.parent.mel),
                             (self.xmin + self.parent.mel, self.ymax + self.parent.mel)).extrude(
                self.parent.zmax - self.parent.zmin + 2 * self.parent.mel).z(self.parent.zmin - self.parent.mel)

    """
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
        p0 = self.baseline.coords[0]
        p1 = self.baseline.coords[1]
        pts = [(p0[0], p0[1], 0), (p1[0], p1[1], 0)]
        return pts

    def getBorderline(self):
        return Line(self.getBorderlinePts())

    def getResidualTransformation(self):    #TODO
        """r = (self.ymax - self.ymin) / self.angle
        a = self.angle

        newTr = np.zeros((3, 4), dtype=float)
        newTr[0] = 1, 0, 0, 0
        newTr[1] = 0, cos(a), -sin(a), -self.ymax * cos(a) + self.ymin + r * (sin(a))
        newTr[2] = 0, sin(a), cos(a), self.ymax * sin(a) - r * (1 - cos(a))

        # newBounds = shapely.geometry.box(self.xmin, self.ymax, self.xmax, self.parent.ymin)
        newBounds = shapely.geometry.box(self.parent.xmin, self.ymax, self.parent.xmax, self.parent.ymin)
        ret = LinearTransformation(newTr, newBounds, self.prio, residual=True)
        # return LinearTransformation([[1, 0, 0, 10], [0, 1, 0, 0], [0, 0, 1, 5]], newBounds, self.prio)


        newBounds = shapely.geometry.box(self.xmax, self.parent.ymin, self.parent.xmax, self.parent.ymax)
        ret = LinearTransformation(newTr, newBounds, self.prio, residual=True)
        ret.name = self.name + "-Res"
        return ret
        """
        return LinearTransformation([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], self.boundaries, self.prio)

    def getMatrixAt(self, pt):  #TODO
        x = pt[0]
        y = pt[1]
        # z = pt[2]
        mat = np.zeros((3, 4), dtype=float)

        if self.boundaries.disjoint(Point(x, y)):
            mat[0] = 1, 0, 0, 0
            mat[1] = 0, 1, 0, 0
            mat[2] = 0, 0, 1, 0

            return mat

        dist = self.extLine.distance(Point(x, y))
        r = self.length / self.angle
        t = dist / self.length
        a = t * self.angle

        #r = (self.ymax - self.ymin) / self.angle
        #t = (y - self.ymin) / (self.ymax - self.ymin)
        #a = t * self.angle

        #mat[0] = 1, 0, 0, 0
        #mat[1] = 0, 1, 0, 0
        #mat[2] = 0, 0, 1, 10
        mat[0] = 0, 0, -sin(a), x + r * sin(a)
        mat[1] = 0, 1, 0, 0
        mat[2] = 0, 0, cos(a), (1 - cos(a)) * r

        return mat
