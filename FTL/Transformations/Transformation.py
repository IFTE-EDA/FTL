from __future__ import annotations

# from typing import Self
from abc import ABCMeta, abstractmethod
import logging

import numpy as np


class Transformation(metaclass=ABCMeta):
    def __init__(
        self,
        bounds: tuple[tuple[float, float], tuple[float, float]],
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

    def get_preprocessed_mesh(self, layerId: int):
        logging.debug(
            "    Transformation {}\n     -> layer {}/{}".format(
                self, layerId, len(self.mel)
            )
        )

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

    # @abstractmethod
    def get_borderline(self):
        pass
