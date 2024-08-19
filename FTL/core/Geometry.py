# This file contains the geometry classes and functions for the FTL library

from __future__ import annotations
import math
import numpy as np
from copy import deepcopy
from matplotlib import pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection
import shapely as sh
from shapely.geometry.polygon import orient
import vedo as v
import gmsh
import pygmsh


# Base class for all geometry classes
class FTLGeom:
    pass


# 2D geometry class
class FTLGeom2D(FTLGeom):
    polygons: sh.MultiPolygon = sh.MultiPolygon()
    z: float = 0

    def __init__(self, z: float = 0, polygons: sh.MultiPolygon = None):
        if polygons is not None:
            self.polygons = polygons
        self.z = z

    @classmethod
    def make_compound(cls, geoms: FTLGeom2D) -> FTLGeom2D:
        # if isinstance(geoms, FTLGeom2D):
        #    return geoms

        def _flatten(lst):
            for el in lst:
                if isinstance(el, (list, tuple)):
                    yield from _flatten(el)
                else:
                    yield el

        # it's a list of FTLGeom2D (or list of lists)
        # from functools import reduce
        # import operator
        if isinstance(geoms, (list, tuple)):
            # geoms = reduce(operator.concat, geoms)
            geoms = list(_flatten(geoms))
        z = geoms[0].z if len(geoms) > 0 else 0
        polys = sh.union_all([g.polygons for g in geoms])
        return cls(z, polys)

    @classmethod
    def get_polygon(
        self, polygon: sh.Polygon, holes: list[sh.Polygon] = []
    ) -> FTLGeom2D:
        ret = FTLGeom2D()
        ret.add_polygon(polygon, holes)
        return ret

    @classmethod
    def get_polygon_orient(
        self, polygon: sh.Polygon, holes: list[sh.Polygon] = []
    ) -> FTLGeom2D:
        ret = FTLGeom2D()
        ret.add_polygon_orient(polygon, holes)
        return ret

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

    @classmethod
    def get_ellipse(
        self,
        center: tuple[float, float],
        radii: tuple[float, float],
        angle: float = 0,
    ) -> FTLGeom2D:
        ret = FTLGeom2D()
        ret.add_ellipse(center, radii, angle)
        return ret

    @classmethod
    def get_roundrect(
        cls,
        start: tuple[float, float],
        end: tuple[float, float],
        radius: float,
    ) -> FTLGeom2D:
        ret = FTLGeom2D()
        ret.add_roundrect(start, end, radius)
        return ret

    @classmethod
    def get_line(
        cls, pts: list[tuple[float, float]], width: float
    ) -> FTLGeom2D:
        ret = FTLGeom2D()
        ret.add_line(pts, width)
        return ret

    @classmethod
    def get_arc(
        cls,
        start: tuple[float, float],
        mid: tuple[float, float],
        end: tuple[float, float],
        width: float,
    ) -> FTLGeom2D:
        ret = FTLGeom2D()
        ret.add_arc(start, mid, end, width)
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
    ) -> FTLGeom2D:
        if isinstance(polygon, sh.Polygon):
            self.polygons = self.polygons.union(polygon)
        else:
            self.polygons = self.polygons.union(sh.Polygon(polygon, holes))
        return self

    def add_polygon_orient(
        self, polygon: sh.Polygon, holes: list[sh.Polygon] = []
    ) -> FTLGeom2D:
        if isinstance(polygon, sh.Polygon):
            new_poly = orient(polygon)
        else:
            new_poly = orient(sh.Polygon(polygon, holes))
        self.polygons = self.polygons.union(new_poly)
        return self

    def add_rectangle(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> FTLGeom2D:
        self.polygons = self.polygons.union(
            sh.box(start[0], start[1], end[0], end[1])
        )
        return self

    def add_circle(
        self, center: tuple[float, float], radius: float = None
    ) -> FTLGeom2D:
        if radius is None:
            radius = center
            center = (0, 0)
        self.add_polygon(sh.geometry.Point(center).buffer(radius))
        return self

    def add_ellipse(
        self,
        center: tuple[float, float],
        radii: tuple[float, float],
        angle: float = 0,
    ) -> FTLGeom2D:
        circle = sh.geometry.Point(center).buffer(1)
        ellipse = sh.affinity.scale(circle, radii[0], radii[1])
        if angle != 0:
            ellipse = sh.affinity.rotate(ellipse, angle, center)
        self.add_polygon(ellipse)
        return self

    def add_roundrect(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        radius: float,
    ) -> FTLGeom2D:
        self.add_polygon(
            sh.geometry.box(
                start[0] + radius,
                start[1] + radius,
                end[0] - radius,
                end[1] - radius,
            ).buffer(radius)
        )
        return self

    def add_line(
        self,
        pts: list[tuple[float, float]],
        width: float,
    ) -> FTLGeom2D:
        self.add_polygon(sh.LineString(pts).buffer(width / 2))
        return self

    def add_arc(
        self,
        start: tuple[float, float],
        mid: tuple[float, float],
        end: tuple[float, float],
        width: float,
    ) -> FTLGeom2D:
        def _center(p1, p2, p3):
            dx1 = p2[0] - p1[0]
            dy1 = p2[1] - p1[1]
            dx2 = p3[0] - p2[0]
            dy2 = p3[1] - p2[1]

            slope1 = dy1 / dx1
            slope2 = dy2 / dx2
            center = [0, 0]
            center[0] = (
                slope1 * slope2 * (p1[1] - p3[1])
                + slope2 * (p1[0] + p2[0])
                - slope1 * (p2[0] + p3[0])
            ) / (2 * (slope2 - slope1))
            center[1] = (
                -(center[0] - (p1[0] + p2[0]) / 2) / slope1
                + (p1[1] + p2[1]) / 2
            )

            return center

        def _polar(angle):
            return (
                center[0] + radius * math.cos(math.radians(angle)),
                center[1] + radius * math.sin(math.radians(angle)),
            )

        def _angle(p):
            return math.degrees(math.atan2(p[1] - center[1], p[0] - center[0]))

        center = _center(start, mid, end)
        radius = math.sqrt(
            (center[0] - start[0]) ** 2 + (center[1] - start[1]) ** 2
        )
        angle_start = _angle(start)
        angle_end = _angle(end)

        def _restrict_angle(angle):
            if angle < -180:
                angle += 360
            if angle > 180:
                angle -= 360
            return angle

        angle_start = _restrict_angle(angle_start)
        angle_end = _restrict_angle(angle_end)

        if _restrict_angle(angle_end - angle_start) < 0:
            angle_start, angle_end = angle_end, angle_start

        if angle_start > angle_end:
            angle_start = angle_start - 360
        else:
            pass

        arc = []
        steps = round((angle_end - angle_start) / 90 * 20)
        if not steps:
            steps = 2
        for a in np.linspace(angle_start, angle_end, steps, endpoint=True):
            arc.append(_polar(a))
        arc.append(_polar(angle_end))

        self.add_polygon(sh.LineString(arc).buffer(width / 2))
        return self

    def cutout(self, geom: (FTLGeom2D, sh.Polygon)) -> FTLGeom2D:
        if isinstance(geom, FTLGeom2D):
            geom = geom.polygons
        self.polygons = self.polygons.difference(geom)
        return self

    def translate(self, x: float = 0, y: float = 0) -> FTLGeom2D:
        self.polygons = sh.affinity.translate(self.polygons, x, y)
        return self

    def rotate(
        self, angle: float = 0, center: tuple(float, float) = (0, 0)
    ) -> FTLGeom2D:
        self.polygons = sh.affinity.rotate(self.polygons, angle, center)
        return self

    def _extrude_surface(
        self, thickness: float, zpos: float, part=None
    ) -> v.Mesh:
        def _create_surface(geom, polygon: sh.Polygon) -> v.Mesh:
            import collections

            print(f"Points before: {len(polygon.exterior.coords)}")
            polygon = orient(polygon).simplify(1e-4)
            print(f"Points after: {len(polygon.exterior.coords)}")
            # gmsh.option.setNumber("Geometry.Tolerance", 1e-11)
            gmsh.option.setNumber("Mesh.MeshSizeMin", 1e-2)

            pts = list(polygon.exterior.coords[:-1])
            # print(f"Dupes in exterior: {[item for item, count in collections.Counter(pts).items() if count > 1]}")
            resolution = 1
            if len(polygon.interiors) == 0:
                poly = geom.add_polygon(pts, resolution, make_surface=True)
            else:
                print("Making holes for polygon...")
                holes = [
                    geom.add_polygon(
                        list(ring.coords[:-1]), resolution, make_surface=False
                    )
                    for ring in polygon.interiors
                ]
                # for hole in holes:
                # print(f"Dupes in hole: {[item for item, count in collections.Counter(hole).items() if count > 1]}")
                if not gmsh.isInitialized():
                    print("Initing GMSH...")
                    gmsh.initialize()
                poly = geom.add_polygon(pts, holes=holes, make_surface=True)
            return poly

        if thickness == 0:
            thickness = 0.05
        if part is None:
            part = self.polygons
        translate_z = self.z if zpos is None else zpos
        if not gmsh.isInitialized():
            print("Initing GMSH...")
            gmsh.initialize()
        with pygmsh.geo.Geometry() as geom:
            print("Started geo kernel")
            # gmsh.option.setNumber("Geometry.Tolerance", 1e-11)
            poly = _create_surface(geom, part)
            print("Surface created.")
            if translate_z != 0:
                geom.translate(poly, [0, 0, translate_z])
            print("Extruding...")
            geom.extrude(poly, translation_axis=[0, 0, thickness])
            print("Extruded. Synchronizing...")
            geom.synchronize()
            print("Synchronized. Generating mesh...")
            msh = geom.generate_mesh(dim=3)
        print("GMSH done.")
        lines, triangles, tetras, vertices = msh.cells
        vmsh = v.TetMesh([msh.points, tetras.data]).tomesh(fill=True)
        try:
            gmsh.clear()
            gmsh.finalize()
        except Exception:
            pass

        return vmsh

    def extrude(
        self, thickness: float, zpos: float = None, fuse: bool = True
    ) -> v.Mesh:
        if isinstance(self.polygons, sh.Polygon):
            # surf = self._create_surface(self.polygons)
            # return self._extrude_surface(surf, thickness, zpos)
            return self._extrude_surface(thickness, zpos)

        # self.polygons is a MultiPolygon or GeometryCollection...
        geoms = []
        for part in self.polygons.geoms:
            print(f"Making part with area {part.area}...")
            if (part.area <= 2) or part.is_empty:
                print("-> Skipped.")
                continue
            print("------------------")
            print(f"Ext: {list(part.exterior.coords)}")
            print(f"Int: {[list(hole.coords) for hole in part.interiors]}")
            # surf = self._create_surface(geom)
            submesh = self._extrude_surface(thickness, zpos, part=part)
            geoms.append(submesh)
            print("Done!")
        if fuse:
            # mesh = v.merge(*surfaces)
            # return self._extrude_surface(mesh, thickness, zpos)
            return v.merge(geoms)
        else:
            # meshes = []
            # for surf in surfaces:
            #    meshes.append(self._extrude_surface(surf, thickness, zpos))
            # return meshes
            return geoms

    def to_3D(self, thickness: float, zpos: float = None) -> FTLGeom3D:
        ret = FTLGeom3D(self.extrude(thickness, zpos, fuse=False))
        ret.geom2d = deepcopy(self)
        return ret

    def plot(self, title: str = None):
        def _plot(geom):
            if isinstance(geom, sh.Polygon):
                path = Path.make_compound_path(
                    Path(np.asarray(geom.exterior.coords)),
                    *[
                        Path(np.asarray(hole.coords))
                        for hole in geom.interiors
                    ],
                )

                patch = PathPatch(path)
                collection = PatchCollection([patch])

                axs.add_collection(collection, autolim=True)
                axs.autoscale_view()
            else:
                for elem in geom.geoms:
                    _plot(elem)

        fig, axs = plt.subplots()
        # axs.xaxis.set_major_locator(plt.NullLocator())
        # axs.yaxis.set_major_locator(plt.NullLocator())
        axs.patch.set_color("w")
        axs.set_aspect("equal", "datalim")
        _plot(self.polygons)
        if title is not None:
            plt.title(title)
        plt.show()


# 3D geometry class
class FTLGeom3D(FTLGeom):
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
