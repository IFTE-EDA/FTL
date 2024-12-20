from __future__ import annotations
from typing import Tuple

import numpy as np
from .Transformation import Transformation


class LinearTransformation(Transformation):
    def __init__(
        self,
        mat: np.array,
        bounds: tuple[tuple[float, float], tuple[float, float]],
        prio: int = 0,
        residual: bool = False,
        name: str = None,
        angle: int = 0,
        pivot: Tuple[int, int] = None,
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

    def is_in_scope(self, point):
        if (
            self.boundaries[0][0] <= point[0] <= self.boundaries[0][1]
            and self.boundaries[1][0] <= point[1] <= self.boundaries[1][1]
        ):
            return True

    def transformPoints(self, points):
        # mesh.rotate_z(self.z_angle, rad=True, around=self.pivot)
        # points = mesh.points()
        for pid, pt in enumerate(points):
            vec = np.array([pt[0], pt[1], pt[2], 1])
            vec = np.dot(self.mat, vec)
            points[pid][0] = vec[0]
            points[pid][1] = vec[1]
            points[pid][2] = vec[2]
        # mesh.points(points)
        # mesh.rotate_z(-self.z_angle, rad=True, around=self.pivot)
        return points

    def get_matrix_at(self, pt):
        return self.mat

    def get_residual_transformation(self):
        return None

    def get_borderline(self):
        return self.bounds
