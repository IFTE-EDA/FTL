# This file contains the geometry classes and functions for the FTL library

from __future__ import annotations
import shapely as sh
import vedo as v
from copy import deepcopy
from matplotlib import pyplot as plt


# Base class for all geometry classes
class FTLGeom:
    pass


# 2D geometry class
class FTLGeom2D:
    polygons: sh.MultiPolygon = sh.MultiPolygon()
    z: float = 0

    def __init__(self, z: float = 0, polygons: sh.MultiPolygon = None):
        if polygons is not None:
            self.polygons = polygons
        self.z = z

    @classmethod
    def make_compound(cls, geoms: FTLGeom2D) -> FTLGeom2D:
        if isinstance(geoms, FTLGeom2D):
            return geoms

        def _flatten(lst):
            for el in lst:
                if isinstance(el, (list, tuple)):
                    yield from _flatten(el)
                else:
                    yield el

        # it's a list of FTLGeom2D (or list of lists)
        # from functools import reduce
        # import operator
        print(geoms)
        if isinstance(geoms, (list, tuple)):
            # geoms = reduce(operator.concat, geoms)
            geoms = list(_flatten(geoms))
            print(geoms)
        z = geoms[0].z
        polys = sh.union_all([g.polygons for g in geoms])
        return cls(z, polys)

    @classmethod
    def get_rectangle(
        cls, start: tuple(float, float), end: tuple(float, float)
    ) -> FTLGeom2D:
        ret = FTLGeom2D()
        ret.add_rectangle(start, end)
        return ret

    @classmethod
    def get_circle(
        cls, center: tuple[float, float], radius: float = None
    ) -> FTLGeom2D:
        ret = cls()
        ret.add_circle(center, radius)
        return ret

    def is_empty(self) -> bool:
        if isinstance(self.polygons, sh.Polygon):
            return True if self.polygons.is_empty else False
        # it's a MultiPolygon or GeometryCollection
        if len(self.polygons.geoms) == 0:
            return True
        for geom in self.polygons.geoms:
            if not geom.is_empty:
                return False
        return True

    def add_polygon(
        self, polygon: sh.Polygon, holes: list[sh.Polygon] = []
    ) -> None:
        if isinstance(polygon, sh.Polygon):
            self.polygons = self.polygons.union(polygon)
        else:
            self.polygons.union(sh.Polygon(polygon, holes))

    def add_rectangle(
        self, start: tuple(float, float), end: tuple(float, float)
    ) -> None:
        self.polygons = self.polygons.union(
            sh.box(start[0], start[1], end[0], end[1])
        )

    def add_circle(
        self, center: tuple[float, float], radius: float = None
    ) -> None:
        if radius is None:
            radius = center
            center = (0, 0)
        self.add_polygon(sh.geometry.Point(center).buffer(radius))

    def cutout(self, geom: (FTLGeom2D, sh.Polygon)) -> None:
        if isinstance(geom, FTLGeom2D):
            geom = geom.polygons
        self.polygons = self.polygons.difference(geom)

    def translate(self, x: float = 0, y: float = 0) -> None:
        self.polygons = sh.affinity.translate(self.polygons, x, y)

    def rotate(
        self, angle: float = 0, center: tuple(float, float) = (0, 0)
    ) -> None:
        self.polygons = sh.affinity.rotate(self.polygons, angle, center)

    def _create_surface(self, polygon: sh.Polygon) -> v.Mesh:
        ext_coords = list(polygon.exterior.coords)
        int_coords = [list(int.coords) for int in polygon.interiors]
        line_ext = v.Line(ext_coords)
        lines_int = [v.Line(int_coords) for int_coords in int_coords]
        return v.merge(line_ext, *lines_int).triangulate()

    def _extrude_surface(
        self, surface: v.Mesh, thickness: float, zpos: float
    ) -> v.Mesh:
        translate_z = self.z if zpos is None else zpos

        if translate_z == 0:
            return surface.extrude(thickness)
        else:
            return surface.z(translate_z).extrude(thickness)

    def extrude(
        self, thickness: float, zpos: float = None, fuse: bool = True
    ) -> v.Mesh:
        surfaces = []
        if isinstance(self.polygons, sh.Polygon):
            surf = self._create_surface(self.polygons)
            return self._extrude_surface(surf, thickness, zpos)

        # self.polygons is a MultiPolygon or GeometryCollection...
        for geom in self.polygons.geoms:
            surf = self._create_surface(geom)
            surfaces.append(surf)
        if fuse:
            mesh = v.merge(*surfaces)
            return self._extrude_surface(mesh, thickness, zpos)
        else:
            meshes = []
            for surf in surfaces:
                meshes.append(self._extrude_surface(surf, thickness, zpos))
            return meshes

    def to_3D(self, thickness: float, zpos: float = None) -> FTLGeom3D:
        ret = FTLGeom3D(self.extrude(thickness, zpos, fuse=False))
        ret.geom2d = deepcopy(self)
        return ret

    def plot(self):
        def _plot(geom):
            print(f"Printing {type(geom)}...")
            if isinstance(geom, sh.Polygon):
                x, y = geom.exterior.xy
                # plt.plot(x, y)
                axs.fill(x, y, "b")
                for hole in geom.interiors:
                    x, y = hole.xy
                    # plt.plot(x, y)
                    axs.fill(x, y, "w")
            else:
                for elem in geom.geoms:
                    _plot(elem)

        fig, axs = plt.subplots()
        axs.set_aspect("equal", "datalim")
        _plot(self.polygons)
        plt.show()


# 3D geometry class
class FTLGeom3D:
    objects: list[v.Mesh] = []
    _geom2d: FTLGeom2D = None

    def __init__(self, objects: list[v.Mesh] = []):
        self.objects = objects

    def is_empty(self) -> bool:
        if isinstance(self.objects, v.Mesh):
            return True if len(self.objects.vertices) == 0 else False
        # it's a list of meshes
        for obj in self.objects:
            if len(obj.vertices) != 0:
                return False
        return True

    def add_object(self, obj: v.Mesh) -> None:
        if isinstance(self.objects, v.Mesh):
            self.objects = [self.objects, obj]
        else:
            self.objects.append(obj)

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
