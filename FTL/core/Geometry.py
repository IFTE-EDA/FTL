# This file contains the geometry classes and functions for the FTL library

from __future__ import annotations


# Base class for all geometry classes
class FTLGeom:
    pass


# 2D geometry class
class FTLGeom2D:
    polygons: list[list[tuple(float, float)]] = []

    def __init__(self):
        self.polygons = []

    def add_polygon(self, polygon: list[tuple(float, float)]):
        self.polygons.append(polygon)

    def extrude(self, zstart: float, thickness: float) -> FTLGeom3D:
        pass


# 3D geometry class
class FTLGeom3D:
    pass
