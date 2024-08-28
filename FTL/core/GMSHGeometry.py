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

from FTL.core.ABCGeometry import AbstractGeom2D, AbstractGeom3D


class GMSHGeom2D(AbstractGeom2D):
    polygons: list[int]
    geoms: list[int]

    z: float = 0

    def __init__(self, z: float = 0, polygons: list[int] = None):
        self.geoms = [polygons] if polygons is not None else []
        self.z = z
        if not gmsh.is_initialized():
            gmsh.initialize()
            print("GMSH was started.")

    @classmethod
    def make_compound(cls, geoms: GMSHGeom2D) -> GMSHGeom2D:
        # if isinstance(geoms, GMSHGeom2D):
        #    return geoms

        def _flatten(lst):
            for el in lst:
                if isinstance(el, (list, tuple)):
                    yield from _flatten(el)
                else:
                    yield el

        # it's a list of GMSHGeom2D (or list of lists)
        # from functools import reduce
        # import operator
        if isinstance(geoms, (list, tuple)):
            # geoms = reduce(operator.concat, geoms)
            geoms = list(_flatten(geoms))
        z = geoms[0].z if len(geoms) > 0 else 0
        polys = gmsh.model.occ.fuse([g.polygons for g in geoms])
        return cls(z, polys)

    @classmethod
    def get_polygon(
        self, polygon: sh.Polygon, holes: list[sh.Polygon] = []
    ) -> GMSHGeom2D:
        ret = GMSHGeom2D()
        ret.add_polygon(polygon, holes)
        return ret

    @classmethod
    def get_polygon_orient(
        self, polygon: sh.Polygon, holes: list[sh.Polygon] = []
    ) -> GMSHGeom2D:
        ret = GMSHGeom2D()
        ret.add_polygon_orient(polygon, holes)
        return ret

    @classmethod
    def get_rectangle(
        cls, start: tuple(float, float), end: tuple(float, float)
    ) -> GMSHGeom2D:
        ret = cls()
        ret.add_rectangle(start, end)
        return ret

    @classmethod
    def get_circle(
        cls, center: tuple[float, float], radius: float = None
    ) -> GMSHGeom2D:
        ret = cls()
        ret.add_circle(center, radius)
        return ret

    @classmethod
    def get_ellipse(
        self,
        center: tuple[float, float],
        radii: tuple[float, float],
        angle: float = 0,
    ) -> GMSHGeom2D:
        ret = GMSHGeom2D()
        ret.add_ellipse(center, radii, angle)
        return ret

    @classmethod
    def get_roundrect(
        cls,
        start: tuple[float, float],
        end: tuple[float, float],
        radius: float,
    ) -> GMSHGeom2D:
        ret = GMSHGeom2D()
        ret.add_roundrect(start, end, radius)
        return ret

    @classmethod
    def get_line(
        cls, pts: list[tuple[float, float]], width: float
    ) -> GMSHGeom2D:
        ret = GMSHGeom2D()
        ret.add_line(pts, width)
        return ret

    @classmethod
    def get_arc(
        cls,
        start: tuple[float, float],
        mid: tuple[float, float],
        end: tuple[float, float],
        width: float,
    ) -> GMSHGeom2D:
        ret = GMSHGeom2D()
        ret.add_arc(start, mid, end, width)
        return ret

    def is_empty(self) -> bool:
        if len(self.geoms) == 0:
            return True
        return False

    def render(self):
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.generate(3)

    def _add_list_polygon(
        self,
        coords_outline: list[(float, float)],
        coords_holes: list[list[(float, float)]],
    ) -> int:
        # TODO: Make it faster - maybe just return index of last element?
        def _fix_list(lst):
            if len(lst) == 0:
                return lst
            return lst[0:-1] if lst[0] == lst[-1] else lst

        holes = []
        pts_outline = [
            gmsh.model.occ.add_point(x, y, 0)
            for x, y in _fix_list(coords_outline)
        ]
        lines = [
            gmsh.model.occ.add_line(pts_outline[i], pts_outline[i + 1])
            for i in range(len(pts_outline) - 1)
        ]
        lines.append(
            gmsh.model.occ.add_line(
                pts_outline[len(pts_outline) - 1], pts_outline[0]
            )
        )
        outline = gmsh.model.occ.add_curve_loop(lines)
        for pts_hole in coords_holes:
            pts = [
                gmsh.model.occ.add_point(x, y, 0)
                for x, y in _fix_list(pts_hole)
            ]
            lines = [
                gmsh.model.occ.add_line(pts[i], pts[i + 1])
                for i in range(len(pts) - 1)
            ]
            lines.append(gmsh.model.occ.add_line(pts[len(pts) - 1], pts[0]))
            hole = gmsh.model.occ.add_curve_loop(lines)
            holes.append(hole)
        surface = gmsh.model.occ.add_plane_surface([outline, *holes])
        gmsh.model.occ.synchronize()
        self.geoms.append(surface)
        return surface

    def _add_shapely_polygon(self, polygon, holes):
        return self._add_list_polygon(
            list(polygon.exterior.coords),
            [list(hole.coords) for hole in polygon.interiors],
        )

    def add_polygon(self, polygon, holes: list = []) -> GMSHGeom2D:
        if isinstance(polygon, list):
            self._add_list_polygon(polygon, holes)
            return self
        if isinstance(polygon, sh.Polygon):
            self._add_shapely_polygon(polygon, holes)
            return self
        if isinstance(polygon, sh.MultiPolygon):
            for poly in polygon.geoms:
                self.add_polygon(poly)
            return self
        raise Exception("Invalid polygon type")

    def add_polygon_orient(
        self, polygon: sh.Polygon, holes: list[sh.Polygon] = []
    ) -> GMSHGeom2D:
        if isinstance(polygon, sh.Polygon):
            new_poly = orient(polygon)
        else:
            try:
                new_poly = orient(sh.Polygon(polygon, holes))
            except Exception:
                print(f"Poly: {polygon}")
                print(f"Holes: {holes}")
                raise Exception("Error in orienting polygon")
        self.polygons = self.polygons.union(new_poly)
        return self

    def add_rectangle(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> GMSHGeom2D:
        rect = gmsh.model.occ.add_rectangle(
            start[0], start[1], 0, end[0] - start[0], end[1] - start[1]
        )
        gmsh.model.occ.synchronize()
        self.geoms.append(rect)
        return self

    def add_circle(
        self, center: tuple[float, float], radius: float = None
    ) -> GMSHGeom2D:
        if radius is None:
            radius = center
            center = (0, 0)
        circle = gmsh.model.occ.addCircle(center[0], center[1], 0, radius)
        circlecl = gmsh.model.occ.addCurveLoop([circle])
        surface = gmsh.model.occ.addPlaneSurface([circlecl])
        self.geoms.append(surface)
        return self

    def add_ellipse(
        self,
        center: tuple[float, float],
        radii: tuple[float, float],
        angle: float = 0,
    ) -> GMSHGeom2D:
        if radii[1] > radii[0]:
            radii = (radii[1], radii[0])
            angle += 90
        ellipse = gmsh.model.occ.addEllipse(
            center[0], center[1], 0, radii[0], radii[1]
        )
        if angle:
            gmsh.model.occ.rotate(
                [(1, ellipse)],
                center[0],
                center[1],
                0.0,
                0,
                0,
                1,
                math.radians(angle),
            )
        ellipse_cl = gmsh.model.occ.addCurveLoop([ellipse])
        surface = gmsh.model.occ.addPlaneSurface([ellipse_cl])
        self.geoms.append(surface)
        return self

    def add_roundrect(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        radius: float,
    ) -> GMSHGeom2D:
        rect = gmsh.model.occ.add_rectangle(
            start[0], start[1], 0, end[0], end[1], roundedRadius=radius
        )
        gmsh.model.occ.synchronize()
        self.geoms.append(rect)
        return self

    def add_line(
        self,
        coords: list[tuple[float, float]],
        width: float,
    ) -> GMSHGeom2D:
        if len(coords) < 3:
            coords.append(coords[1])
            coords[1] = (
                (coords[0][0] + coords[2][0]) / 2,
                (coords[0][1] + coords[2][1]) / 2,
            )
        print("Coords: ", coords)
        pts = [gmsh.model.occ.add_point(x, y, 0) for x, y in coords]
        lines = [
            gmsh.model.occ.add_line(pts[i], pts[i + 1])
            for i in range(len(pts) - 1)
        ]
        # lines.append(gmsh.model.occ.add_line(pts[len(pts) - 1], pts[0]))
        curve_loop = gmsh.model.occ.add_wire(lines)
        offset_curve = gmsh.model.occ.offset_curve(curve_loop, width / 2)
        surface_loop = gmsh.model.occ.add_curve_loop(
            [c[1] for c in offset_curve]
        )
        surface = gmsh.model.occ.add_plane_surface([surface_loop])
        gmsh.model.occ.synchronize()
        self.geoms.append(surface)
        return self

    def add_arc(
        self,
        start: tuple[float, float],
        mid: tuple[float, float],
        end: tuple[float, float],
        width: float,
    ) -> GMSHGeom2D:
        pts = [gmsh.model.occ.add_point(x, y, 0) for x, y in [start, mid, end]]
        arc = gmsh.model.occ.add_circle_arc(
            pts[0], pts[1], pts[2], center=False
        )
        arc_wire = gmsh.model.occ.add_wire([arc])
        offset_curve = gmsh.model.occ.offset_curve(arc_wire, width / 2)
        surface_loop = gmsh.model.occ.add_curve_loop(
            [c[1] for c in offset_curve]
        )
        surface = gmsh.model.occ.add_plane_surface([surface_loop])
        gmsh.model.occ.synchronize()
        self.geoms.append(surface)
        return self

    def _fuse_all(self) -> int:
        if len(self.geoms) == 1:
            return self.geoms[0]
        # print(f"Geoms: {self.geoms}")
        objects = [(2, self.geoms[0])]
        tools = [(2, tag) for tag in self.geoms[1:]]
        # print(f"Objects: {objects}")
        # print(f"Tools: {tools}")
        fused = gmsh.model.occ.fuse(objects, tools)
        # print(f"Fused: {fused}")
        self.geoms = [f[1] for f in fused[0]]
        return fused[0]

    def cutout(self, geoms: (GMSHGeom2D, sh.Polygon)) -> GMSHGeom2D:
        if isinstance(geoms, GMSHGeom2D):
            geoms = geoms.geoms
        if isinstance(geoms, list) and isinstance(geoms[0], GMSHGeom2D):
            ret = []
            for g in geoms:
                ret.extend(g.geoms)
            print("Ret:", ret)
            geoms = ret
        if not isinstance(geoms, list):
            geoms = [geoms]
        self._fuse_all()
        cut = gmsh.model.occ.cut(
            [(2, g) for g in self.geoms],
            [(2, g) for g in geoms],
        )
        print("Cut: ", cut)
        return self

    def translate(self, x: float = 0, y: float = 0) -> GMSHGeom2D:
        self.polygons = sh.affinity.translate(self.polygons, x, y)
        return self

    def rotate(
        self, angle: float = 0, center: tuple(float, float) = (0, 0)
    ) -> GMSHGeom2D:
        self.polygons = sh.affinity.rotate(self.polygons, angle, center)
        return self

    def _create_surface(self, polygon: sh.Polygon) -> v.Mesh:
        poly = orient(polygon)
        ext_coords = list(poly.exterior.coords)
        int_coords = [list(int.coords) for int in poly.interiors]
        line_ext = v.Line(ext_coords)
        lines_int = [v.Line(int_coords) for int_coords in int_coords]
        return v.merge(
            line_ext.join_segments(),
            *[line.join_segments() for line in lines_int],
        ).triangulate()

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


class FTLGeom3D(AbstractGeom3D):
    pass
