from __future__ import annotations

# from typing import Self
from abc import ABCMeta, abstractmethod
import logging

import numpy as np
import shapely as sh
import vedo as v


class Transformation(metaclass=ABCMeta):
    def __init__(
        self,
        bounds: sh.Polygon,
        prio: int = 0,
        addResidual: bool = True,
        name: str = None,
    ):
        # debug("Transformation created")
        self.boundaries = bounds
        self.prio = prio
        self.addResidual = addResidual
        self.isResidual = False
        # self.color = None
        self.color = [255, 255, 0, 255]
        # self.points = []
        self.mel = []
        self.parent = None
        self.name = name
        self.transformWholeMesh = False

    def __str__(self) -> str:
        return "Transformation"

    def get_outline_points(self) -> np.array:
        x = self.boundaries.exterior.coords.xy[0][:-1]
        y = self.boundaries.exterior.coords.xy[1][:-1]
        z = [self.parent.zmax] * len(x)
        # pts = np.zeros((len(x), 3))  # zip(x, y, z)
        pts = list(zip(x, y, z))
        return pts

    def get_preprocessed_mesh(self, layerId: int):
        logging.debug(
            "    Transformation {}\n     -> layer {}/{}".format(
                self, layerId, len(self.mel)
            )
        )
        return self.meshes[layerId].clone().subdivide(1, 2, self.mel[layerId])

    def get_area(self):
        return self.get_outline_points().triangulate().lw(0)

    # TODO: really needed?
    def getAffectedPoints(self):
        raise NotImplementedError(
            "Please implement the function in a new class."
        )

    @abstractmethod
    def get_matrix_at(self, pt) -> np.array:
        pass

    # @abstractmethod
    def is_in_scope(self, point):
        pass

    @abstractmethod
    def get_residual_transformation(self):
        pass

    @abstractmethod
    def get_borderline(self):
        pass
