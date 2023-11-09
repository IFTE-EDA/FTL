from enum import Enum
import logging

import numpy as np
from numpy import sin, cos
import shapely as sh
from shapely.ops import nearest_points

# from shapely.geometry.polygon import orient
import vedo as v

# from shapely import affinity
# from shapely.ops import nearest_points


import copy

# from FTL.Transformations.Transformation import Transformation
from .Transformation import Transformation
from .LinearTransformation import LinearTransformation

DIR = Enum("DIR", "NEGY POSY NEGX POSX")  #
global MAX_EDGE_LENGTH


class DirBend(Transformation):
    def __init__(self, data, prio=0, addResidual=True, name=None):
        self.boundaries_rot = None
        self.prio = prio
        self.addResidual = addResidual
        self.name = name
        self.parent = None

        # TODO: create standard name because otherwise getResidual() fails

        if "points" not in data:  # found point data; prioritize those
            raise ValueError(
                "Not enough data for Transformation {}".format(self.name)
            )
        if len(data["points"]) < 4:
            raise ValueError(
                "Not enough points in points array of transformation {}: {} (expecting 4+)".format(
                    data["name"], len(data["points"])
                )
            )

        poly = sh.Polygon([[p["x"], p["y"]] for p in data["points"]])
        baseline = sh.LineString(
            (
                (data["points"][0]["x"], data["points"][0]["y"]),
                (data["points"][1]["x"], data["points"][1]["y"]),
            )
        )
        self.boundaries = poly
        super().__init__(self.boundaries, prio, addResidual, name)

        minx, miny, maxx, maxy = poly.bounds
        # bounding_box = shapely.geometry.box(minx, miny, maxx, maxy)
        ax, ay, bx, by = baseline.bounds
        self.pivot = list(poly.exterior.coords[0])
        self.pivot.append(0)
        if ax == bx:  # vertical line
            self.extLine = sh.LineString([(ax, miny), (ax, maxy)])
        elif ay == by:  # horizonthal line
            self.extLine = sh.LineString([(minx, ay), (maxx, ay)])
        else:
            # linear equation: y = k*x + m
            m = -(ay - by) / (ax - bx)
            n = ay - m * ax + (by - ay)
            y0 = m * minx + n
            y1 = m * maxx + n
            x0 = (miny - n) / m
            x1 = (maxy - n) / m
            logging.debug(
                "m: {}; n: {}; P1({}, {}), 2({}, {})".format(
                    m, n, x0, y0, x1, y1
                )
            )
            logging.debug(
                "Angle is {}".format(np.arctan(m) / (2 * np.pi) * 360)
            )
            self.extLine = sh.LineString(
                (sh.Point(minx, y0), sh.Point(maxx, y1))
            )

        dists = [
            self.extLine.distance(sh.Point(p)) for p in poly.exterior.coords
        ]
        distPoints = [
            (dists[i], poly.exterior.coords[i])
            for i in range(len(poly.exterior.coords))
            if dists[i] > 0
        ]

        points_sorted_by_distance = sorted(distPoints, key=lambda x: x[0])
        length = points_sorted_by_distance[0][0]
        logging.debug(">>min: {}".format(length))
        self.projPoint, _ = nearest_points(
            self.extLine, sh.Point(points_sorted_by_distance[0][1])
        )
        self.ortho = sh.LineString(
            [self.projPoint, sh.Point(points_sorted_by_distance[0][1])]
        )
        logging.debug(self.projPoint)

        self.angle = np.deg2rad(data["angle"])
        self.z_angle = np.arctan((bx - ax) / (ay - by))
        logging.debug("Z_ANGLE: {}".format(np.rad2deg(self.z_angle)))
        self.boundaries_rot = sh.affinity.rotate(
            poly, self.z_angle, origin=self.pivot, use_radians=True
        )

        r = length / self.angle
        a = self.angle
        self.newTr = np.zeros((3, 4), dtype=float)
        self.newTr[0] = (
            cos(a),
            0,
            -sin(a),
            -(self.pivot[0] + length) * cos(a) + self.pivot[0] + r * (sin(a)),
        )
        self.newTr[1] = 0, 1, 0, 0
        self.newTr[2] = (
            sin(a),
            0,
            cos(a),
            -(self.pivot[0] + length) * sin(a) + r * (1 - cos(a)),
        )

        self.baseline = baseline
        self.length = length
        # self.points = []
        self.meshes = []
        self.mel = []
        self.transformWholeMesh = True

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Tr.DirBend: [P={}; Res={}; angle={}; len={}; baseline={}; bounds={}]".format(
            self.prio,
            self.addResidual,
            self.angle,
            self.length,
            self.baseline,
            self.boundaries,
        )

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

        logging.debug(self.extLine)
        return v.merge(ext, perp, ortho)

    def is_in_scope(self, point):
        pt = sh.Point(point[0], point[1])
        if not pt.disjoint(self.boundaries):
            return True

    def get_outline_pts(self):
        poly = sh.geometry.polygon.orient(self.boundaries)
        x = poly.exterior.coords.xy[0][:-1]
        y = poly.exterior.coords.xy[1][:-1]
        z = [0] * len(x)
        pts = list(zip(x, y, z))

        return pts

    def get_outline_points(self):
        return v.Line(self.get_outline_pts(), closed=True)

    def get_borderline_pts(self):
        p0 = self.baseline.coords[0]
        p1 = self.baseline.coords[1]
        pts = [(p0[0], p0[1], 0), (p1[0], p1[1], 0)]
        return pts

    def get_borderline(self):
        return v.Line(self.get_borderline_pts())

    def get_residual_transformation(self, mesh=None):  # TODO
        newBounds = sh.box(
            self.pivot[0],
            self.pivot[1],
            self.pivot[0] + 100,
            self.pivot[1] + 100,
        )
        ret = LinearTransformation(
            self.newTr,
            newBounds,
            self.prio,
            residual=True,
            angle=self.z_angle,
            pivot=self.pivot,
        )
        ret.name = self.name + "-Res"
        return ret

    def transform_mesh(self, mesh):
        logging.debug("--> Transforming a whole mesh now")
        mesh.rotate_z(self.z_angle, rad=True, around=self.pivot)
        points = mesh.points()
        for pid, pt in enumerate(points):
            self.parent.update_progress(pid, len(points))
            vec = np.array([pt[0], pt[1], pt[2], 1])
            vec = np.dot(self.get_matrix_at(pt), vec)
            points[pid][0] = vec[0]
            points[pid][1] = vec[1]
            points[pid][2] = vec[2]
        mesh.points(points)
        mesh.rotate_z(-self.z_angle, rad=True, around=self.pivot)
        return mesh

    def get_matrix_at(self, pt):  # TODO
        x = pt[0]
        y = pt[1]
        if x > (self.pivot[0] + self.length):
            return self.newTr

        mat = np.zeros((3, 4), dtype=float)

        if self.boundaries_rot.disjoint(sh.Point(x, y)):
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
