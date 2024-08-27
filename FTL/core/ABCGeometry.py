# This file contains the geometry classes and functions for the FTL library

from __future__ import annotations
from abc import ABC, abstractmethod


# Base class for all geometry classes
class FTLGeom:
    pass


class AbstractGeom2D(ABC, FTLGeom):
    @classmethod
    @abstractmethod
    def make_compound(cls, geoms: AbstractGeom2D) -> AbstractGeom2D:
        pass

    @classmethod
    @abstractmethod
    def get_polygon(self, polygon, holes: list = []) -> AbstractGeom2D:
        pass

    @classmethod
    @abstractmethod
    def get_polygon_orient(self, polygon, holes: list = []) -> AbstractGeom2D:
        pass

    @classmethod
    @abstractmethod
    def get_rectangle(
        cls, start: tuple(float, float), end: tuple(float, float)
    ) -> AbstractGeom2D:
        pass

    @classmethod
    @abstractmethod
    def get_circle(
        cls, center: tuple[float, float], radius: float = None
    ) -> AbstractGeom2D:
        pass

    @classmethod
    @abstractmethod
    def get_ellipse(
        self,
        center: tuple[float, float],
        radii: tuple[float, float],
        angle: float = 0,
    ) -> AbstractGeom2D:
        pass

    @classmethod
    @abstractmethod
    def get_roundrect(
        cls,
        start: tuple[float, float],
        end: tuple[float, float],
        radius: float,
    ) -> AbstractGeom2D:
        pass

    @classmethod
    @abstractmethod
    def get_line(
        cls, pts: list[tuple[float, float]], width: float
    ) -> AbstractGeom2D:
        pass

    @classmethod
    @abstractmethod
    def get_arc(
        cls,
        start: tuple[float, float],
        mid: tuple[float, float],
        end: tuple[float, float],
        width: float,
    ) -> AbstractGeom2D:
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        pass

    @abstractmethod
    def add_polygon(self, polygon, holes: list = []) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def add_rectangle(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def add_circle(
        self, center: tuple[float, float], radius: float = None
    ) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def add_ellipse(
        self,
        center: tuple[float, float],
        radii: tuple[float, float],
        angle: float = 0,
    ) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def add_roundrect(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        radius: float,
    ) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def add_line(
        self, pts: list[tuple[float, float]], width: float
    ) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def add_arc(
        self,
        start: tuple[float, float],
        mid: tuple[float, float],
        end: tuple[float, float],
        width: float,
    ) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def cutout(self, geom: ("AbstractGeom2D")) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def translate(self, x: float = 0, y: float = 0) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def rotate(
        self, angle: float = 0, center: tuple[float, float] = (0, 0)
    ) -> "AbstractGeom2D":
        pass

    @abstractmethod
    def extrude(self, thickness: float, zpos: float = None, fuse: bool = True):
        pass

    @abstractmethod
    def to_3D(self, thickness: float, zpos: float = None) -> "AbstractGeom3D":
        pass

    @abstractmethod
    def plot(self, title: str = None):
        pass


def AbstractGeom3D(ABC, FTLGeom):
    # 3D geometry class

    # objects: list = []
    # _geom2d: AbstractGeom2D = None

    def __init__(self, objects: list = []):
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        pass

    @abstractmethod
    def add_object(self, obj) -> None:
        pass

    @abstractmethod
    @property
    def geom2d(self) -> AbstractGeom2D:
        pass

    @abstractmethod
    @geom2d.setter
    def geom2d(self, geom2d: AbstractGeom2D):
        pass
