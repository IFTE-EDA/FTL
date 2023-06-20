import numpy as np
import shapely
#from shapely import LineString, Point, Polygon
from shapely.geometry import Point, Polygon
import shapely.geometry.polygon
from shapely import affinity
from shapely.ops import nearest_points
import vedo as v
from enum import Enum
import copy
from Transformation import *
from LinearTransformation import *
from DirBend import *

DIR = Enum('DIR', 'NEGY POSY NEGX POSX')#
global MAX_EDGE_LENGTH


class Spiral(DirBend):

    #def __init__(self, boundaries, baseline, length, angle, prio=0, addResidual=True, name=None):
    def __init__(self, data, prio=0, addResidual=True, name=None):
        self.boundaries_rot = None
        self.prio = prio
        self.addResidual = addResidual
        self.name = name
        self.parent = None

        if "turns" in data:
            data["angle"] = data["turns"] * 2*np.pi
        elif "angle" in data:
            data["turns"] = data["angle"] / (2*np.pi)
        if "dir" in data:
            dir2angle = ["POSX", "POSY", "NEGX", "NEGY"]
            if data["dir"] in dir2angle:
                self.dir = np.deg2rad(dir2angle.index(data["dir"])*90)
                print("Direction of Spiralling calculated as {} degrees".format(data["dir"]))
            else:
                try:
                    self.dir = float(data["dir"])
                except ValueError:
                    raise ValueError("Value 'dir' for transformation '{}' is not a number.".format(name))
                # TODO:Check if value is a number
        else:
            pass
            # TODO calculate direction from geometry

        if ("diameter" in data) and ("angle" in data):
            if "length" in data:
                raise ValueError("Transformation '{}' overdefined. Expecting exactly 2 of these values: Diameter, length, turns/angle".format(name))   #  TODO: Specify type
            self.diameter = data["diameter"]
            self.angle = data["angle"]
            self.length = np.pi * self.diameter * self.turns
            print("Calculated length as {}".format(self.length))
        elif ("diameter" in data) and ("length" in data):
            if "angle" in data:
                raise ValueError("Transformation '{}' overdefined. Expecting exactly 2 of these values: Diameter, length, turns/angle".format(name))   #  TODO: Specify type
            self.diameter = data["diameter"]
            self.length = data["length"]
            self.turns = self.length / (self.diameter*np.pi)
            self.angle = self.turns * 2*np.pi
            data["angle"] = self.diameter
            print("Calculated angle as {}".format(np.rad2deg(self.angle)))
        elif ("length" in data) and ("angle" in data):
            if "diameter" in data:
                raise ValueError("Transformation '{}' overdefined. Expecting exactly 2 of these values: Diameter, length, turns/angle".format(name))   #  TODO: Specify type
            self.angle = data["angle"]
            self.length = data["length"]
            self.diameter = self.length / self.angle
            print("Calculated diameter as {}".format(self.diameter))
        else:
            raise ValueError("Transformation '{}' underdefined. Expecting exactly 2 of these values: Diameter, length, turns/angle".format(name))  #  TODO: Specify type

        if not "points" in data:  # found point data; prioritize those
            raise ValueError("No data points found for Transformation '{}'".format(self.name))
        if len(data["points"]) < 2:
            raise ValueError("Not enough points in 'points' list of transformation '{}': {} (expecting 2)".format(data["name"], len(data["points"])))

        points = [(p["x"], p["y"]) for p in data["points"]]
        #baseline = LineString( ( points[0], points[1] ) )
        dx, dy = self.length * np.array( (np.cos(self.dir), np.sin(self.dir)) )
        print(dx, dy)
        points.extend([(p[0] + dx, p[1] + dy) for p in [points[1], points[0]]])
        data["points"] = [{"x": p[0], "y": p[1]} for p in points]
        data["angle"] = np.rad2deg(data["angle"])
        print(points)
        #baseline = LineString(((data["points"][0]["x"], data["points"][0]["y"]), (data["points"][1]["x"], data["points"][1]["y"])))
        #poly = Polygon([[p["x"], p["y"]] for p in data["points"]])
        #poly = Polygon(points)
        #diff = self.length * np.array((np.cos(self.dir), np.sin(self.dir)))
        #poly[2] = poly[0] + np.array(diff)
        #poly[3] = poly[1] + np.array(diff)

        #self.boundaries = poly
        super().__init__(data, prio, addResidual, name)
        """
        minx, miny, maxx, maxy = poly.bounds
        bounding_box = shapely.geometry.box(minx, miny, maxx, maxy)
        ax, ay, bx, by = baseline.bounds
        self.pivot = list(poly.exterior.coords[0])
        self.pivot.append(0)
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
            self.extLine = LineString((Point(minx, y0), Point(maxx, y1)))

        dists = [self.extLine.distance(Point(p)) for p in poly.exterior.coords]
        distPoints = [(dists[i], poly.exterior.coords[i]) for i in range(len(poly.exterior.coords)) if dists[i] > 0]

        points_sorted_by_distance = sorted(distPoints, key=lambda x: x[0])
        #length = self.extLine.distance(points_sorted_by_distance[0])  #TODO
        length = points_sorted_by_distance[0][0]
        print(">>min: {}".format(length))
        self.projPoint, _ = nearest_points(self.extLine, Point(points_sorted_by_distance[0][1]))
        self.ortho = LineString([self.projPoint, Point(points_sorted_by_distance[0][1])])
        print(self.projPoint)

        self.angle = np.deg2rad(data["angle"])
        self.z_angle = np.arctan((bx-ax)/(ay-by))
        print("Z_ANGLE: {}".format(np.rad2deg(self.z_angle)))
        self.boundaries_rot = affinity.rotate(poly, self.z_angle, origin=self.pivot, use_radians=True)

        r = length / self.angle
        a = self.angle
        self.newTr = np.zeros((3, 4), dtype=float)
        self.newTr[0] = cos(a), 0, -sin(a), -(self.pivot[0]+length) * cos(a) + self.pivot[0] + r * (sin(a))
        self.newTr[1] = 0, 1, 0, 0
        self.newTr[2] = sin(a), 0, cos(a), -(self.pivot[0]+length) * sin(a) + r * (1 - cos(a))

        self.baseline = baseline
        self.length = length
        # self.points = []
        self.meshes = []
        self.mel = []
        self.transformWholeMesh = True

        # self.super().__init__(self.boundaries, prio, addResidual, name)
        """

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

        ext = v.Line(getPoints(self.extLine), closed=False).c("Blue")
        ortho = v.Line(getPoints(self.ortho), closed=False).c("Yellow")
        perp = v.Point((self.projPoint.x, self.projPoint.y, 0), r=12, c="Red")

        print(self.extLine)
        return v.merge(ext, perp, ortho)

    def isInScope(self, point):
        pt = Point(point[0], point[1])
        if not pt.disjoint(self.boundaries):
            return True
        # else:
        #    debug(pt.__str__() + " out of scope")

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

    def getResidualTransformation(self, mesh=None):    #TODO
        newBounds = shapely.geometry.box(self.pivot[0], self.pivot[1], self.pivot[0]+100, self.pivot[1]+100)
        ret = LinearTransformation(self.newTr, newBounds, self.prio, residual=True, angle=self.z_angle, pivot=self.pivot)
        ret.name = self.name + "-Res"
        return ret

        #return LinearTransformation([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], self.boundaries, self.prio)

    def transformMesh(self, mesh):
        print("--> Transforming a whole mesh now")
        mesh.rotate_z(self.z_angle, rad=True, around=self.pivot)
        points = mesh.points()
        for pid, pt in enumerate(points):
            self.parent.update_progress(pid, len(points))
            vec = np.array([pt[0], pt[1], pt[2], 1])
            vec = np.dot(self.getMatrixAt(pt), vec)
            points[pid][0] = vec[0]
            points[pid][1] = vec[1]
            points[pid][2] = vec[2]
        mesh.points(points)
        mesh.rotate_z(-self.z_angle, rad=True, around=self.pivot)
        return mesh

    def getMatrixAt(self, pt):  #TODO
        x = pt[0]
        y = pt[1]
        # z = pt[2]
        if x > (self.pivot[0]+self.length):
            return self.newTr

        mat = np.zeros((3, 4), dtype=float)

        if self.boundaries_rot.disjoint(Point(x, y)):
            mat[0] = 1, 0, 0, 0
            mat[1] = 0, 1, 0, 0
            mat[2] = 0, 0, 1, 0

            return mat

        r = abs(self.length) / self.angle
        t = abs(x - self.pivot[0]) / self.length
        a = t * self.angle

        mat[0] = 0, 0, -sin(a), self.pivot[0] + r * sin(a)
        mat[1] = 0, 1, 0, 0
        mat[2] = 0, 0, cos(a), (1 - cos(a)) * r

        return mat
