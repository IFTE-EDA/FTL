# This file contains the geometry classes and functions for the FTL library

from __future__ import annotations
import shapely as sh
import vedo as v


# Base class for all geometry classes
class FTLGeom:
    pass


# 2D geometry class
class FTLGeom2D:
    polygons: list[v.Polygon] = []
    z: float = 0

    def __init__(self, z: float = 0, polygons: list[v.Polygon] = None):
        self.polygons = polygons if polygons is not None else []
        self.z = z

    def add_polygon(self, polygon: list[tuple(float, float)]):
        self.polygons.append(polygon)

    def extrude(self, thickness: float, zpos: float = None) -> v.Mesh:
        translate_z = self.z if zpos is None else zpos
        if translate_z == 0:
            return [poly.extrude(thickness) for poly in self.polygons]
        else:
            return [
                poly.translate([0, 0, translate_z]).extrude(thickness)
                for poly in self.polygons
            ]

    def to_3D(self, thickness: float, zpos: float = None) -> FTLGeom3D:
        ret = FTLGeom3D(self.extrude(thickness, zpos))
        ret.geom2d = self
        return ret


# 3D geometry class
class FTLGeom3D:
    objects: list[v.Mesh] = []
    _geom2d: FTLGeom2D = None

    def __init__(self, objects: list[v.Mesh] = []):
        self.objects = objects

    @property
    def geom2d(self) -> FTLGeom2D:
        if self._geom2d is not None:
            return self._geom2d
        else:
            raise AttributeError(
                "This geometry was not created from a 2D geometry object."
            )

    @geom2d.setter
    def geom2d(self, geom2d: FTLGeom2D):
        self._geom2d = geom2d
