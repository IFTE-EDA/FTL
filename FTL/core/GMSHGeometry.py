from __future__ import annotations

import math
import numpy as np
from copy import deepcopy, copy
from matplotlib import pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection
import shapely as sh
from shapely.geometry.polygon import orient
import vedo as v
import gmsh

from FTL.core.ABCGeometry import AbstractGeom2D, AbstractGeom3D


def dimtags(geoms: list[int], dim: int = 2) -> list[tuple[int, int]]:
    if not isinstance(geoms, list):
        return [(dim, geoms)]
    return [(dim, tag) for tag in geoms]


def dimtags2int(geoms: list[tuple[int, int]]) -> list[int]:
    return [e[1] for e in geoms]


class GMSHGeom2D(AbstractGeom2D):
    def __init__(
        self, z: float = 0, geoms: list[int] = None, name: str = "Unnamed"
    ):
        self._used = False
        self.name = name
        if geoms is not None:
            self.geoms = geoms if isinstance(geoms, list) else [geoms]
        else:
            self.geoms = []
        self.z = z
        if not gmsh.is_initialized():
            gmsh.initialize()
            gmsh.option.setNumber("General.Verbosity", 3)
            gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
            print("GMSH was started.")

    @classmethod
    def make_compound(cls, geoms: GMSHGeom2D) -> GMSHGeom2D:
        def _flatten(lst):
            for el in lst:
                if isinstance(el, (list, tuple)):
                    yield from _flatten(el)
                else:
                    if isinstance(el, GMSHGeom2D):
                        yield from el.geoms
                    else:
                        yield el

        # it's a list of GMSHGeom2D (or list of lists)
        if isinstance(geoms, (list, tuple)):
            # geoms = reduce(operator.concat, geoms)
            geoms = list(_flatten(geoms))
        if len(geoms) > 1:
            # objects = [(2, geoms[0])]
            objects = dimtags(geoms[0])
            tools = dimtags(geoms[1:])
            # tools = [(2, tag) for tag in geoms[1:]]
            print("Objects: ", objects)
            print("Tools: ", tools)
            if not isinstance(tools, list):
                tools = [tools]
            geoms = dimtags2int(gmsh.model.occ.fuse(objects, tools)[0])
            print("Fused: ", geoms)
            return cls(0, geoms)
        if len(geoms) == 1:
            return cls(0, geoms)
        return cls()

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

    def __len__(self):
        return len(self.geoms)

    def is_empty(self) -> bool:
        if len(self.geoms) == 0:
            return True
        return False

    def get(self):
        if self._used:
            return self.copy()
        else:
            self._used = True
            return self

    def copy(self):
        copy = deepcopy(self)
        copy.geoms = dimtags2int(gmsh.model.occ.copy(self.dimtags()))
        return copy

    def render(self, dim=3):
        gmsh.model.occ.synchronize()
        gmsh.model.mesh.generate(dim)
        return self

    def _add_list_polygon(
        self,
        coords_outline: list[(float, float)],
        coords_holes: list[list[(float, float)]],
        orient: bool = False,
    ) -> int:
        # TODO: Make it faster - maybe just return index of last element?
        def _fix_list(lst):
            if len(lst) == 0:
                return lst
            return lst[0:-1] if lst[0] == lst[-1] else lst

        holes = []
        in_outline = coords_outline
        if orient:
            in_outline.reverse()
            print("Re-oriented.")
        pts_outline = [
            gmsh.model.occ.add_point(x, y, 0) for x, y in _fix_list(in_outline)
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

    def _add_list_polygon_bulge(
        self,
        coords_outline: list[(float, float, float)],
        coords_holes: list[list[(float, float, float)]] = [],
        orient: bool = False,
    ) -> int:
        # TODO: Make it faster - maybe just return index of last element?
        def _fix_list(lst):
            if len(lst) == 0:
                return lst
            return lst[0:-1] if lst[0] == lst[-1] else lst

        def _add_line(pt1, pt2, pids=None):
            if pids is not None:
                p1 = pids[0]
                p2 = pids[1]
            else:
                p1 = gmsh.model.occ.add_point(pt1[0], pt1[1], 0)
                p2 = gmsh.model.occ.add_point(pt2[0], pt2[1], 0)
            # print(f"Adding line from {pt1} to {pt2} with bulge {pt1[2]}")
            # no bulge? draw a straight line
            if np.round(pt1[2], 2) == 0:
                return gmsh.model.occ.add_line(p1, p2)
            # bulged line
            delta_x = pt2[0] - pt1[0]
            delta_y = pt2[1] - pt1[1]
            alpha = math.atan2(delta_y, delta_x)
            length = math.sqrt(delta_x**2 + delta_y**2)

            pt_m = ((pt1[0] + pt2[0]) / 2, (pt1[1] + pt2[1]) / 2)
            c_u = pt1[2] * length / 2
            if pt1[2] > 0:
                c_u = -c_u
            if pt1[2] > 0:
                pt_u = (
                    pt_m[0] + c_u * np.cos(alpha + np.pi / 2),
                    pt_m[1] + c_u * np.sin(alpha + np.pi / 2),
                )
            else:
                pt_u = (
                    pt_m[0] - c_u * np.cos(alpha + np.pi / 2),
                    pt_m[1] - c_u * np.sin(alpha + np.pi / 2),
                )

            # pt_u = (
            #    pt_m[0] - c_u * np.sin(alpha),
            #    pt_m[1] - c_u * np.cos(alpha),
            # )
            pu = gmsh.model.occ.add_point(pt_u[0], pt_u[1], 0)
            return gmsh.model.occ.add_circle_arc(p1, pu, p2, center=False)

        holes = []
        in_outline = _fix_list(coords_outline)
        if orient:
            in_outline.reverse()
            print("Re-oriented.")

        if (
            in_outline[0][0] == in_outline[-1][0]
            and in_outline[0][1] == in_outline[-1][1]
        ):
            print("Rendering closed line...: ", in_outline)
            pts = [
                gmsh.model.occ.add_point(x, y, 0)
                for x, y, _ in in_outline[:-1]
            ]
            print(len(pts), len(in_outline))
            lines = [
                _add_line(
                    in_outline[i], in_outline[i + 1], pids=(pts[i], pts[i + 1])
                )
                for i in range(len(in_outline) - 2)
            ]
            print("Adding closing segment...")
            lines.append(
                _add_line(
                    in_outline[len(pts) - 1],
                    in_outline[0],
                    pids=(
                        pts[len(pts) - 1],
                        pts[0],
                    ),
                )
            )
        else:
            print("Rendering open line as closed poly...")
            pts = [gmsh.model.occ.add_point(x, y, 0) for x, y, _ in in_outline]
            lines = [
                _add_line(
                    in_outline[i], in_outline[i + 1], pids=(pts[i], pts[i + 1])
                )
                for i in range(len(in_outline) - 1)
            ]
            lines.append(
                _add_line(
                    in_outline[len(pts) - 1],
                    in_outline[0],
                    pids=(pts[len(pts) - 1], pts[0]),
                )
            )

        outline = gmsh.model.occ.add_curve_loop(lines)
        for pts_hole in coords_holes:
            # TODO: remove additional holes?
            print("Making hole...")
            lines = [
                _add_line(pts_hole[i], pts_hole[i + 1])
                for i in range(len(pts_hole) - 1)
            ]
            lines.append(_add_line(pts_hole[len(pts_hole) - 1], pts_hole[0]))
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

    def add_polygon(
        self,
        polygon,
        holes: list = [],
        orient: bool = False,
        bulge: bool = False,
    ) -> GMSHGeom2D:
        if isinstance(polygon, list):
            if bulge:
                self._add_list_polygon_bulge(polygon, holes, orient)
            else:
                self._add_list_polygon(polygon, holes, orient)
            return self
        # TODO: implement tests for ndarray
        if isinstance(polygon, np.ndarray):
            if bulge:
                self._add_list_polygon_bulge(polygon.tolist(), holes, orient)
            else:
                self._add_list_polygon(polygon.tolist(), holes, orient)
            return self
        if isinstance(polygon, sh.Polygon):
            self._add_shapely_polygon(polygon, holes)
            return self
        if isinstance(polygon, sh.MultiPolygon):
            for poly in polygon.geoms:
                self.add_polygon(poly)
            return self
        raise Exception("Invalid polygon type: ", type(polygon))

    def add_polygon_orient(
        self, polygon: sh.Polygon, holes: list[sh.Polygon] = []
    ) -> GMSHGeom2D:
        return self.add_polygon(orient(polygon), [orient(h) for h in holes])
        if isinstance(polygon, sh.Polygon):
            new_poly = orient(polygon)
        else:
            try:
                new_poly = orient(sh.Polygon(polygon, holes))
            except Exception:
                print(f"Poly: {polygon}")
                print(f"Holes: {holes}")
                raise Exception("Error in orienting polygon")
        self.add_polygon(new_poly)
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
            start[0],
            start[1],
            0,
            end[0] - start[0],
            end[1] - start[1],
            roundedRadius=radius,
        )
        gmsh.model.occ.synchronize()
        self.geoms.append(rect)
        return self

    def _add_line_bulge(
        self,
        coords: list[tuple[float, float, float, float, float]],
        width: float,
    ) -> GMSHGeom2D:
        def _add_line(pt1, pt2):
            # print(f"Adding line from {pt1} to {pt2} with bulge {pt1[4]}")
            p1 = gmsh.model.occ.add_point(pt1[0], pt1[1], 0)
            p2 = gmsh.model.occ.add_point(pt2[0], pt2[1], 0)
            if pt1[4] == 0:
                # render straight line
                return gmsh.model.occ.add_line(p1, p2)
            else:
                # render bulged line
                delta_x = pt2[0] - pt1[0]
                delta_y = pt2[1] - pt1[1]
                alpha = math.atan2(delta_y, delta_x)
                length = math.sqrt(delta_x**2 + delta_y**2)

                pt_m = ((pt1[0] + pt2[0]) / 2, (pt1[1] + pt2[1]) / 2)
                c_u = pt1[4] * length / 2
                if pt1[4] > 0:
                    c_u = -c_u
                if pt1[4] > 0:
                    pt_u = (
                        pt_m[0] + c_u * np.cos(alpha + np.pi / 2),
                        pt_m[1] + c_u * np.sin(alpha + np.pi / 2),
                    )
                else:
                    pt_u = (
                        pt_m[0] - c_u * np.cos(alpha + np.pi / 2),
                        pt_m[1] - c_u * np.sin(alpha + np.pi / 2),
                    )

                # pt_u = (
                #    pt_m[0] - c_u * np.sin(alpha),
                #    pt_m[1] - c_u * np.cos(alpha),
                # )

                pu = gmsh.model.occ.add_point(pt_u[0], pt_u[1], 0)
                segment = gmsh.model.occ.add_circle_arc(
                    p1, pu, p2, center=False
                )

                return segment

        in_outline = coords
        if orient:
            in_outline.reverse()
            print("Re-oriented.")
        if len(in_outline) == 2:
            # TODO: test if it really works
            pt12 = tuple(
                (
                    (in_outline[0][i] + in_outline[1][i]) / 2
                    for i in range(0, 5)
                )
            )
            in_outline = [in_outline[0], pt12, in_outline[1]]
        lines = [
            _add_line(in_outline[i], in_outline[i + 1])
            for i in range(len(in_outline) - 1)
        ]
        # lines.append(
        #    _add_line(in_outline[len(in_outline) - 1], in_outline[0])
        # )
        # outline = gmsh.model.occ.add_curve_loop(lines)

        curve_loop = gmsh.model.occ.add_wire(lines)
        offset_curve = gmsh.model.occ.offset_curve(curve_loop, width / 2)
        surface_loop = gmsh.model.occ.add_curve_loop(
            [c[1] for c in offset_curve]
        )
        surface = gmsh.model.occ.add_plane_surface([surface_loop])
        gmsh.model.occ.synchronize()
        self.geoms.append(surface)
        return self

    def add_line(
        self,
        coords: list[
            (tuple[float, float], tuple[float, float, float, float, float])
        ],
        width: float,
        bulge: bool = False,
    ) -> GMSHGeom2D:
        coords = list(coords)
        if bulge:
            # TODO: make more compact
            return self._add_line_bulge(coords, width)
        if len(coords) < 3:
            coords.append(copy(coords[1]))
            coords[1] = (
                (coords[0][0] + coords[2][0]) / 2,
                (coords[0][1] + coords[2][1]) / 2,
            )
        if coords[0] == coords[-1]:
            print("Rendering closed line...")
            pts = [gmsh.model.occ.add_point(x, y, 0) for x, y in coords[:-1]]
            lines = [
                gmsh.model.occ.add_line(pts[i], pts[i + 1])
                for i in range(len(pts) - 1)
            ]
            lines.append(gmsh.model.occ.add_line(pts[len(pts) - 1], pts[0]))
        else:
            print("Rendering open line...")
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

    def dimtags(self) -> list[tuple[int, int]]:
        return dimtags(self.geoms)

    # TODO: check before fusing if only 1 element contained?
    def _fuse_all(self) -> int:
        if not len(self.geoms):
            return []
        if len(self.geoms) == 1:
            return self.geoms[0]
        tags = self.dimtags()
        fused = gmsh.model.occ.fuse([tags[0]], tags[1:])
        self.geoms = [f[1] for f in fused[0]]
        return fused[0]

    def cutout(self, geoms: (GMSHGeom2D, sh.Polygon)) -> GMSHGeom2D:
        if isinstance(geoms, GMSHGeom2D):
            geoms = geoms.geoms
        if (
            isinstance(geoms, list)
            and len(geoms)
            and isinstance(geoms[0], GMSHGeom2D)
        ):
            ret = []
            for g in geoms:
                ret.extend(g.geoms)
            geoms = ret
        if not isinstance(geoms, list):
            geoms = [geoms]
        if geoms == []:
            return self
        self._fuse_all()
        gmsh.model.occ.cut(
            self.dimtags(),
            [(2, g) for g in geoms],
        )
        return self

    def translate(self, x: float = 0, y: float = 0) -> GMSHGeom2D:
        gmsh.model.occ.translate(self.dimtags(), x, y, 0)
        return self

    def rotate(
        self, angle: float = 0, center: tuple(float, float) = (0, 0)
    ) -> GMSHGeom2D:
        gmsh.model.occ.rotate(
            self.dimtags(),
            x=center[0],
            y=center[1],
            z=0,
            angle=math.radians(angle),
            ax=0,
            ay=0,
            az=1,
        )
        return self

    def extrude(
        self, thickness: float, zpos: float = None, fuse: bool = True
    ) -> GMSHGeom3D:
        if not len(self.geoms):
            return GMSHGeom3D()
        if fuse:
            self._fuse_all()
        if zpos is None:
            zpos = self.z
        if zpos != 0:
            gmsh.model.occ.translate(self.dimtags(), 0, 0, zpos)
        extr = gmsh.model.occ.extrude(self.dimtags(), 0, 0, thickness)
        extr = [e[1] for e in extr if e[0] == 3]
        return GMSHGeom3D(extr, self)

    def to_3D(self, thickness: float, zpos: float = None) -> GMSHGeom3D:
        ret = GMSHGeom3D(self.extrude(thickness, zpos, fuse=False))
        ret.geom2d = deepcopy(self)
        return ret

    def set_visible(self, visible: bool = True):
        gmsh.model.setVisibility(self.dimtags(), visible)

    def plot(self, title: str = ""):
        gmsh.model.occ.synchronize()
        all_entities = gmsh.model.occ.getEntities(-1)
        gmsh.model.setVisibility(all_entities, 0)
        gmsh.model.setVisibility(self.dimtags(), 1, True)
        gmsh.fltk.setStatusMessage(title)
        gmsh.fltk.run()


class GMSHGeom3D(AbstractGeom3D):
    def __init__(
        self,
        geoms: list[int] = [],
        geom2d: GMSHGeom2D = None,
        name: str = "Unnamed",
    ):
        if len(geoms):
            self.geoms = geoms
        else:
            self.geoms = []
        self._geom2d = geom2d
        self.name = name

    def __len__(self):
        return len(self.geoms)

    def dimtags(self) -> list[tuple[int, int]]:
        return dimtags(self.geoms, 3)

    @classmethod
    def make_compound(cls, geoms: GMSHGeom3D) -> GMSHGeom3D:
        def _flatten(lst):
            for el in lst:
                if isinstance(el, (list, tuple)):
                    yield from _flatten(el)
                else:
                    if isinstance(el, GMSHGeom3D):
                        yield from el.geoms
                    else:
                        yield el

        # it's a list of GMSHGeom2D (or list of lists)
        if isinstance(geoms, (list, tuple)):
            # geoms = reduce(operator.concat, geoms)
            geoms = list(_flatten(geoms))
        if len(geoms) > 1:
            # objects = [(2, geoms[0])]
            objects = dimtags(geoms[0], 3)
            tools = dimtags(geoms[1:], 3)
            # tools = [(2, tag) for tag in geoms[1:]]
            print("Objects: ", objects)
            print("Tools: ", tools)
            if not isinstance(tools, list):
                tools = [tools]
            geoms = dimtags2int(gmsh.model.occ.fuse(objects, tools)[0])
            print("Fused: ", geoms)
            return cls(geoms)
        if len(geoms) == 1:
            return cls(geoms)
        return cls()

    def is_empty(self) -> bool:
        return not len(self.geoms)

    def set_visible(self, visible: bool = True):
        gmsh.model.setVisibility(self.dimtags(), visible)

    def _dimtags(self) -> list[tuple[int, int]]:
        return dimtags(self.geoms, 3)

    # TODO: Support adding list of integers?
    def add_object(self, obj: int) -> None:
        if isinstance(obj, int):
            self.geoms.append(obj)
            return self
        if not isinstance(obj, int):
            if isinstance(obj, GMSHGeom3D):
                self.geoms.extend(obj.geoms)
                return self
            raise TypeError("Object must be an integer or GMSHGeom3D.")

    @property
    def geom2d(self) -> GMSHGeom2D:
        if self._geom2d is not None:
            return self._geom2d
        else:
            raise AttributeError(
                "This geometry was not created from a 2D geometry object."
            )

    @geom2d.setter
    def geom2d(self, geom2d: GMSHGeom2D):
        self._geom2d = geom2d

    def plot(self, title: str = ""):
        gmsh.model.occ.synchronize()
        all_entities = gmsh.model.occ.getEntities(-1)
        gmsh.model.setVisibility(all_entities, 0)
        gmsh.model.setVisibility(self.dimtags(), 1, True)
        gmsh.fltk.setStatusMessage(title)
        gmsh.fltk.run()
