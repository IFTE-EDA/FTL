from __future__ import annotations
import sys
import gmsh
import ezdxf

sys.path.append(r".")
from pathlib import Path
from abc import ABC, abstractmethod
import numpy as np

from FTL.Util.logging import Logger, Loggable
from FTL.core.GMSHGeometry import GMSHGeom2D, GMSHGeom3D, dimtags
from FTL.core.PolygonNester import PolygonNester, Polygon

SNAP_TOLERANCE = 0.02

# TODO: "has_layer" method to check if layer exists


class DXFParser(Loggable):
    def __init__(self, file_path: Path, logger=None):
        if logger is None:
            self.logger = Logger("DXFParser")
            self.logger.info("Starting parser...")
        else:
            self.logger = logger
        super().__init__(self.logger)
        self.file_path = file_path
        self.doc = self._readfile(file_path)

        self._init_structures()

    def _readfile(self, file_path: Path):
        doc = ezdxf.readfile(file_path)
        # try:
        # doc = ezdxf.readfile(file_path)
        # except IOError:
        # print(f"File I/O error.")
        # sys.exit(1)
        # except ezdxf.DXFStructureError:
        # print(f"DXF file corrupted or invalid.")
        # sys.exit(2)
        return doc

    def _init_structures(self):
        self.layers = {}
        self.msp = self.doc.modelspace()
        for layer in self.doc.layers:
            print(f"Layer: {layer.dxf.name}")
            self.layers[layer.dxf.name] = DXFLayer(
                layer, self.msp.query(f"*[layer == '{layer.dxf.name}']")
            )
            # render_layer(msp.query(f"*[layer == '{layer.dxf.name}']"))

    def get_layer_names(self):
        return list(self.layers.keys())

    def get_layer(self, layer_name):
        if layer_name not in self.layers:
            raise KeyError(f"Layer {layer_name} not found")
        return self.layers[layer_name]


class DXFLayer(Loggable):
    def __init__(self, layer, entities):
        self.layer = layer
        self.name = layer.dxf.name
        self.entities = entities
        self.pn = PolygonNester()
        self.open_polys = []

    def add_entity(self, entity):
        self.entities.append(entity)

    def get_entities(self):
        # return [e for e in self.ent]
        return self.entities

    def render(self, fuse=True):
        geom = GMSHGeom2D()
        # if layer.dxf.name != "0":
        #    return geom
        print(f"Rendering layer: {self.name}")
        for e in self.entities:
            # tmp = GMSHGeom2D()
            print(f"Rendering entity: {e}")
            if hasattr(e, "is_closed"):
                print("Closed: ", e.is_closed)
            if hasattr(e, "has_width"):
                print("Has width: ", e.has_width)
            self.render_entity(e, geom)
        print(f"There are {len(self.open_polys)} open polys remaining.")
        for op in self.open_polys:
            print(f"{op[2][0]} -> {op[2][-1]} ({len(op[2])} points)")
        print("============================================")
        print("POLYGON DUMP")
        self.pn.dump()
        print("============================================")
        print("Rendering remaining open polies as lines...")
        for poly in self.open_polys:
            geom.add_line([[p[0], p[1], p[2]] for p in poly[2]], 1, bulge=True)
        print("Rendering nested polygons...")
        for poly in self.pn.polygons:
            # geom.add_polygon(poly.points, bulge=True)
            # TODO: just for testing. correct later.
            if len(poly.children) > 0:
                geom.add_polygon(
                    poly.points,
                    [hole.points for hole in poly.children],
                    bulge=poly.bulge,
                )
            else:
                geom.add_polygon(poly.points, bulge=poly.bulge)
        # geom.plot()
        return geom

    def extrude(self, height, zpos=0):
        geom = self.render()
        geom.extrude(height, zpos=zpos)
        return geom

    def render_entity(self, e, geom):
        if e.dxftype() == "LINE":
            return self.render_line(e, geom)
        elif e.dxftype() == "ARC":
            return self.render_arc(e, geom)
        elif e.dxftype() == "LWPOLYLINE":
            return self.render_lw_polyline(e, geom)
        elif e.dxftype() == "CIRCLE":
            return self.render_circle(e, geom)
        elif e.dxftype() == "MTEXT":
            return self.render_mtext(e, geom)
        elif e.dxftype() == "DIMENSION":
            return GMSHGeom2D()
        else:
            raise Exception(f"Cannot render entity: {e.dxftype()}")

    def render_line(self, e, geom):
        print(f"LINE: {e.dxf.start} -> {e.dxf.end}, width={e.dxf.thickness}")
        # print(e.dxf.__dict__)
        # TODO: midpoint should not be needed to be added here...
        p_mid = (
            (e.dxf.start[0] + e.dxf.end[0]) / 2,
            (e.dxf.start[1] + e.dxf.end[1]) / 2,
        )
        # TODO: handle "0" width, needs to be added to open poly array
        geom.add_line(
            [
                (e.dxf.start[0], e.dxf.start[1]),
                p_mid,
                (e.dxf.end[0], e.dxf.end[1]),
            ],
            e.dxf.lineweight * 10,  # if e.dxf.lineweight != 0 else 1,
        )

    def render_arc(self, e, geom):
        print(
            f"Arc: Center {e.dxf.center}, radius {e.dxf.radius}, from {e.dxf.start_angle} to {e.dxf.end_angle}"
        )
        # print(e.dxf.__dict__)
        start_angle = e.dxf.start_angle
        end_angle = (
            e.dxf.end_angle
            if e.dxf.end_angle > start_angle
            else e.dxf.end_angle + 360
        )
        p_start = (
            e.dxf.center[0] + e.dxf.radius * np.cos(np.radians(start_angle)),
            e.dxf.center[1] + e.dxf.radius * np.sin(np.radians(start_angle)),
        )
        p_mid = (
            e.dxf.center[0]
            + e.dxf.radius * np.cos(np.radians((start_angle + end_angle) / 2)),
            e.dxf.center[1]
            + e.dxf.radius * np.sin(np.radians((start_angle + end_angle) / 2)),
        )
        p_end = (
            e.dxf.center[0] + e.dxf.radius * np.cos(np.radians(end_angle)),
            e.dxf.center[1] + e.dxf.radius * np.sin(np.radians(end_angle)),
        )
        geom.add_arc(p_start, p_mid, p_end, 1)

    def print_duplicates(self, points):
        seen = set()
        uniq = [
            (p[0], p[1])
            for p in points
            if (p[0], p[1]) not in seen and not seen.add((p[0], p[1]))
        ]
        print(f"Duplicate points: {len(points) - len(uniq)}")

    def render_lw_polyline(self, e, geom):
        # for print(e.get_points())
        with e.points("xyb") as points:
            reshaped = np.reshape(points, (-1, 3))
            coords = [[round(p[i], 2) for i in [0, 1, 2]] for p in reshaped]
            """if (
                round(reshaped[0][0], 6) == round(reshaped[-1][0], 6)
                and round(reshaped[0][1], 6) == round(reshaped[-1][1], 6)
            ) or e.is_closed:
                return"""
            print(f"> Rendering LWPolyline: #{e.dxf.handle}")
            print(f"Const width: {e.dxf.const_width}")
            print(f"Closed: {e.is_closed}")
            print(f"Has width: {e.has_width}")
            print(f"Length: {len(coords)}")
            # if (len(reshaped) < 3):
            #    print("Not enough points to render polyline")
            #    return
            pts = []
            old_x, old_y = None, None
            # print(reshaped)
            for x, y, b in coords:
                x_rounded, y_rounded = round(x, 6), round(y, 6)
                if x_rounded == old_x and y_rounded == old_y:
                    print(f"Found duplicate point: {x_rounded}, {y_rounded}")
                    pts[-1] = (x_rounded, y_rounded, b)
                else:
                    pts.append((x_rounded, y_rounded, b))
                    # print((x_rounded, y_rounded))
                    old_x, old_y = x_rounded, y_rounded
            if pts[0] != pts[-1] and e.is_closed:
                print("Closing shape...")
                pts.append(pts[0])
            if len(pts) <= 1:
                print("Not enough points to render polyline")
                return None
            if pts[0][0] == pts[-1][0] and pts[0][1] == pts[-1][1]:
                print("Endpoints meet. Making shape...")
                # geom.add_polygon(pts, bulge=True)
                self.pn.add_polygon(Polygon(pts), bulge=True)
            elif (
                np.sqrt(
                    (pts[0][0] - pts[-1][0]) ** 2
                    + (pts[0][1] - pts[-1][1]) ** 2
                )
                < SNAP_TOLERANCE
            ):
                print("Endpoints close enough. Closing shape...")
                pts[-1] = pts[0]
                # geom.add_polygon(pts, bulge=True)
                self.pn.add_polygon(Polygon(pts), bulge=True)
            else:
                print(
                    "Distance: ",
                    np.sqrt(
                        (pts[0][0] - pts[-1][0]) ** 2
                        + (pts[0][1] - pts[-1][1]) ** 2
                    ),
                )
                if e.dxf.const_width > 0:
                    print(f"Adding polyline with width {e.dxf.const_width}")
                    geom.add_line(
                        [(np.round(p[0], 3), np.round(p[1], 3)) for p in pts],
                        e.dxf.const_width,
                        bulge=False,
                    )
                else:

                    def _reverse_poly(poly):
                        from scipy.ndimage import shift

                        if not isinstance(poly, np.ndarray):
                            _poly = np.array(poly)
                        else:
                            _poly = poly
                        coords = _poly[:, 0:2]
                        bulges = _poly[
                            :, 2
                        ]  # [np.round(p, 2) for p in _poly[:, 2]]
                        return np.column_stack(
                            (
                                coords[::-1],
                                -shift(bulges, 1, cval=bulges[-1])[::-1],
                            )
                        ).tolist()

                    print(
                        "Line has no width; checking for coincidence with stored polys..."
                    )
                    # print(f"{len(self.open_polys)} open polys in list.")
                    store_poly = True
                    new_pts = None
                    delete_entries = []
                    for poly in self.open_polys:
                        if pts[-1] in (poly[0], poly[1]):
                            print(
                                "Last point of current poly matched with point of stored poly. Closing..."
                            )
                            if (
                                pts[-1][0] == poly[0][0]
                                and pts[-1][1] == poly[0][1]
                            ):
                                print("pts[-1] == poly[0]")
                                # end point of current poly equals starting point of new poly - easy, just chain them
                                # print("--------------------")
                                # print("Current poly: \n", np.array(pts))
                                # print("--------------------")
                                # print("Stored poly: \n", np.array(poly[2]))
                                # print("--------------------")
                                new_pts = np.concatenate(
                                    (pts[:-1], poly[2])
                                ).tolist()
                                # print("Result: \n", np.array(new_pts))
                            else:
                                # end point of current poly equals end point of new poly - more difficult, turn the latter around to keep orientation
                                print("pts[-1] == poly[-1]; rev. poly\n")
                                # print("--------------------")
                                # print("Current poly: \n", np.array(pts))
                                # print("--------------------")
                                # print("Stored poly: \n", np.array(poly[2]))
                                # print("--------------------")
                                new_pts = np.concatenate(
                                    (pts[:-1], _reverse_poly(poly[2]))
                                ).tolist()
                                # print("Result: \n", np.array(new_pts))
                        elif pts[0] in (poly[0], poly[1]):
                            print(
                                "First point of current poly matched with point of stored poly. Closing..."
                            )
                            # to make things easier, convert the start point to an end point
                            if (
                                pts[0][0] == poly[0][0]
                                and pts[0][1] == poly[0][1]
                            ):
                                # start point of current poly equals starting point of new poly - easy, just chain them
                                print("pts[0] == poly[0]; rev. pts")
                                # print("--------------------")
                                # print("Current poly: \n", np.array(pts))
                                # print("--------------------")
                                # print("Stored poly: \n", np.array(poly[2]))
                                # print("--------------------")
                                new_pts = np.concatenate(
                                    (_reverse_poly(pts[1:]), poly[2])
                                ).tolist()
                                # print("Result: \n", np.array(new_pts))
                            else:
                                # start point of current poly equals end point of new poly - more difficult, turn the latter around to keep orientation
                                print("pts[0] == poly[-1]; rev. both")
                                # print("--------------------")
                                # print("Current poly: \n", np.array(pts))
                                # print("--------------------")
                                # print("Stored poly: \n", np.array(poly[2]))
                                # print("--------------------")
                                new_pts = np.concatenate(
                                    (
                                        _reverse_poly(pts[1:]),
                                        _reverse_poly(poly[2]),
                                    )
                                ).tolist()
                                # print("Result: \n", np.array(new_pts))
                        if new_pts is not None:
                            # we found something!
                            store_poly = False
                            if (
                                new_pts[0][0] == new_pts[-1][0]
                                and new_pts[0][1] == new_pts[-1][1]
                            ):
                                print(
                                    "Poly closed successfully, adding as polygon..."
                                )
                                # TODO: choose different data type. This is not a good idea and will decrease performance.
                                new_pts = [
                                    [x, y, np.round(b, 6)]
                                    for x, y, b in new_pts
                                ]
                                print(np.array(new_pts))
                                # geom.add_polygon(new_pts, bulge=True)
                                self.pn.add_polygon(
                                    Polygon(new_pts), bulge=True
                                )
                                delete_entries.append((poly[0], poly[1]))
                                break
                            else:

                                def np64tofloat(lst):
                                    return tuple((np.float64(x) for x in lst))

                                print(
                                    "Poly not closed yet, storing for later..."
                                )
                                self.open_polys.append(
                                    [
                                        np64tofloat(new_pts[0]),
                                        np64tofloat(new_pts[-1]),
                                        [np64tofloat(p) for p in new_pts],
                                    ]
                                )
                                delete_entries.append(
                                    (tuple(poly[0]), tuple(poly[1]))
                                )
                                break

                    # print("---------------\nDelete: \n", delete_entries)
                    def _check_keep_poly(poly):
                        ret = (poly[0], poly[1]) not in delete_entries
                        return ret

                    self.open_polys[:] = [
                        p for p in self.open_polys if _check_keep_poly(p)
                    ]
                    if store_poly:
                        print("Nothing found. Storing poly for later...")
                        self.open_polys.append([pts[0], pts[-1], pts])
                    # print("---------------\nOpen polys: \n", self.open_polys)
                # gmsh.model.occ.synchronize()
                # gmsh.fltk.run()
            # gmsh.model.occ.synchronize()
            # gmsh.fltk.run()

    def render_circle(self, e, geom):
        print(f"Circle: {e.dxf.center}, {e.dxf.radius}")
        geom.add_circle((e.dxf.center[0], e.dxf.center[1]), e.dxf.radius)

    def render_mtext(self, e, geom):
        pass  # print(f"MText: {e.dxf.text}")
