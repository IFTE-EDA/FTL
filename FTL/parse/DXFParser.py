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
        # geom.plot()
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
        else:
            raise Exception(f"Cannot render entity: {e.dxftype()}")

    def render_line(self, e, geom):
        print(f"Line: {e.dxf.start} -> {e.dxf.end}, width={e.dxf.thickness}")
        # print(e.dxf.__dict__)
        geom.add_line(
            [(e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1])],
            e.dxf.thickness,
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
        print(f"Rendering LWPolyline: {e.dxf}")
        print(f"Const width: {e.dxf.const_width}")
        print(f"Closed: {e.is_closed}")
        print(f"Has width: {e.has_width}")

        if e.has_width and e.dxf.const_width == 0:
            raise Exception(
                "Width definition in segments not supported. Please use const_width instead."
            )

        # for print(e.get_points())
        with e.points() as points:
            reshaped = np.reshape(points, (-1, 5))
            # if (len(reshaped) < 3):
            #    print("Not enough points to render polyline")
            #    return
            pts = []
            old_x, old_y = None, None
            # print(reshaped)
            self.print_duplicates(reshaped)
            for x, y, w_s, w_e, b in reshaped:
                x_rounded, y_rounded = round(x, 6), round(y, 6)
                if x_rounded == old_x and y_rounded == old_y:
                    print(f"Duplicate point: {x_rounded}, {y_rounded}")
                else:
                    pts.append((x_rounded, y_rounded, w_s, w_e, b))
                    print((x_rounded, y_rounded), w_s, w_e, b)
                    old_x, old_y = x_rounded, y_rounded
            if pts[0] != pts[-1] and e.is_closed:
                print("Closing shape...")
                pts.append(pts[0])
            if len(pts) <= 1:
                print("Not enough points to render polyline")
                return None
            # print(pts)
            self.print_duplicates(pts)
            # geom.add_line(pts, 5)
            if pts[0] == pts[-1]:  # closed shape
                geom.add_polygon([(p[0], p[1], p[4]) for p in pts], bulge=True)
            else:
                geom.add_line(pts, e.dxf.const_width, bulge=True)

    def render_circle(self, e, geom):
        print(f"Circle: {e.dxf.center}, {e.dxf.radius}")
        geom.add_circle((e.dxf.center[0], e.dxf.center[1]), e.dxf.radius)

    def render_mtext(self, e, geom):
        pass  # print(f"MText: {e.dxf.text}")
