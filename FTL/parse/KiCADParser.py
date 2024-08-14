from __future__ import annotations
import sys

import vedo as v

sys.path.append(r".")
from pathlib import Path
from itertools import chain
import shapely as sh
from abc import ABC, abstractmethod

sys.path.append(r"..\..")
from FTL.parse.kicad_parser import KicadPCB
from FTL.parse.kicad_parser import SexpList
from FTL.Util.logging import Logger, Loggable
from FTL.core.Geometry import FTLGeom2D


class KiCADConfig:
    via_metalization = 0.015  # 15µm metalization


class KiCADParser(Loggable):
    def __init__(self, file_path: Path, logger=None):
        if logger is None:
            self.logger = Logger("KiCADParser")
            self.logger.info("Starting parser...")
        else:
            self.logger = logger
        super().__init__(self.logger)
        self.file_path = file_path
        self.pcb = KicadPCB.load(file_path)

        self.stackup = KiCADStackupManager(
            self, self.pcb["layers"], self.pcb.setup["stackup"]
        )
        self.nets = dict(chain(self.pcb["net"]))
        self.footprints = [
            KiCADPart(self, part) for part in self.pcb["footprint"]
        ]
        # self.layers[footprint["layer"]].add_footprint(footprint)
        # self.polygons = [KiCADPolygon(poly) for poly in self.pcb["gr_poly"]]
        self.geoms = {
            "gr_text_box": [],
            "gr_line": [],
            "gr_rect": [],
            "gr_circle": [],
            "gr_arc": [],
            "gr_poly": [],
            "gr_curve": [],
            "segment": [],
            "via": [],
        }
        if "gr_text_box" in self.pcb:
            # self.geoms["gr_text_box"] = self.pcb["gr_text_box"]
            pass
            # raise Exception("Text Boxes not supported yet.")
        if "gr_line" in self.pcb:
            # self.geoms["gr_line"] = self.pcb["gr_line"]
            pass
            # raise Exception("Lines not supported yet.")
        if "gr_rect" in self.pcb:
            if not isinstance(self.pcb["gr_rect"], SexpList):
                print(type(self.pcb["gr_rect"]))
                self.stackup.add_geometry(
                    self.pcb["gr_rect"]["layer"],
                    KiCADRect(self, self.pcb["gr_rect"]),
                )
            else:
                for rect in self.pcb["gr_rect"]:
                    self.stackup.add_geometry(
                        rect["layer"], KiCADRect(self, rect)
                    )
            # raise Exception("Rectangles not supported yet.")
        if "gr_circle" in self.pcb:
            # self.geoms["gr_circle"] = self.pcb["gr_circle"]
            pass
            # raise Exception("Circles not supported yet.")
        if "gr_arc" in self.pcb:
            # self.geoms["gr_arc"] = self.pcb["gr_arc"]
            pass
            # raise Exception("Arcs not supported yet.")
        if "gr_poly" in self.pcb:
            # self.geoms["gr_poly"] = self.pcb["gr_poly"]
            for poly in self.pcb["gr_poly"]:
                self.stackup.add_geometry(
                    poly["layer"], KiCADPolygon(self, poly)
                )
        if "gr_curve" in self.pcb:
            # self.geoms["gr_curve"] = self.pcb["gr_curve"]
            pass
            # raise Exception("Curves not supported yet.")
        if "segment" in self.pcb:
            for segment in self.pcb["segment"]:
                self.stackup.add_segment(segment["layer"], segment)
        if "zone" in self.pcb:
            for zone in self.pcb["zone"]:
                self.stackup.add_zone(zone["layer"], KiCADZone(self, zone))
        if "arc" in self.pcb:
            for arc in self.pcb["arc"]:
                self.stackup.add_arc(arc["layer"], arc)
        if "via" in self.pcb:
            for via in self.pcb["via"]:
                for layer in via["layers"]:
                    via_obj = KiCADVia(self, via)
                    self.stackup.add_geometry(layer, via_obj)
                    self.stackup.add_via_metalization(
                        via_obj.get_layer_names(),
                        via_obj.at,
                        via_obj.get_metalization(),
                    )
                    via_obj.make_drills(self.stackup)

    def render_footprints(self):
        if len(self.footprints) > 0:
            self.log_info(f"Rendering {len(self.footprints)} footprints...")
            for footprint in self.footprints:
                self.log_info(f"->Rendering {footprint.name}")
                footprint.render(self.stackup)

    def render_layers(self):
        self.log_info("Rendering PCB...")
        names = []
        renders = []
        for name, layer in self.stackup.items():
            self.log_info(f"Rendering layer '{name}'...")
            names.append(name.strip('"'))
            renders.append(layer.render())
        return dict(zip(names, renders))

    def render(self):
        self.render_footprints()
        # self.stackup.add_drill("*", FTLGeom2D.get_circle((0, 0), 6))
        renders = self.render_layers()
        renders_3d = []
        for name, layer in self.stackup.stackup.items():
            if not layer.has_objects():
                continue
            if layer.name.endswith("Cu"):
                color = "orange"
            elif layer.name.endswith("Silk"):
                color = "white"
            elif layer.name.endswith("Mask"):
                color = "green"
            elif layer.name.endswith("Paste"):
                color = "gray"
            elif layer.name.endswith("Cuts"):
                color = "blue"
            else:
                color = "pink"
            self.log_info(f"Rendering layer '{name}' in {color}...")
            render = (
                renders[name]
                .extrude(layer.thickness, zpos=layer.zmin)
                .c(color)
            )
            renders_3d.append(render)
        metalization = self.stackup.fill_vias()
        if metalization is not None:
            metalization.c("orange")
        else:
            self.log_warning("No metalizations found.")
        # sub = renders["Edge.Cuts"].extrude(1.4).c("green")
        # top_cu = renders["F.Cu"].extrude(0.035, zpos=1.4).c("orange")
        # bot_cu = renders["B.Cu"].extrude(0.035, zpos=-0.035).c("orange")
        # vedo.show(sub, top_cu, bot_cu, axes=1, viewup="y", interactive=True)
        # for layer in self.stackup.get_layer_names():
        #    if self.stackup.layer_has_objects(layer):
        #        renders[layer].plot(layer)
        # renders["F.Cu"].plot("F.Cu")
        v.show(renders_3d, metalization, axes=1, viewup="y", interactive=True)
        return renders["F.Cu"]


class KiCADStackupManager(Loggable):
    def __init__(self, parent: Loggable, layer_params, stackup_params):
        Loggable.__init__(self, parent)
        self.layers = {}
        self.metalizations = []
        names = []
        layers = []
        for layer in layer_params:
            layer = KiCADLayer(self, layer, layer_params[layer])
            names.append(layer.name)
            layers.append(layer)
            # self.layers.append(layer.name, layer)
        self.layers = dict(zip(names, layers))
        self.log_info(f"Created {len(self.layers)} layer references...")
        self.layer_params = layer_params
        self.stackup_params = stackup_params
        self.build_stackup(stackup_params)

    def build_stackup(self, stackup_params):
        self.log_info(
            f"Building stackup of {len(stackup_params['layer'])} layers..."
        )
        curr_z = 0
        names = []
        layers = []
        for lay in stackup_params["layer"]:
            layer_type = lay["type"].strip('"')
            layer_name = (
                lay[0].strip('"') if layer_type != "core" else "Edge.Cuts"
            )
            layer_thickness = lay["thickness"] if "thickness" in lay else 0
            self.log_debug(
                f"...adding layer '{layer_name}' with thickness {layer_thickness} and type {layer_type} to stackup..."
            )
            layer = self.get_layer(layer_name)
            layer.thickness = layer_thickness
            layer.zmax = curr_z
            layer.zmin = curr_z - layer_thickness
            self.log_debug(
                f"-> Layer '{layer_name}' has zmin {layer.zmin} and zmax {layer.zmax}..."
            )
            curr_z -= layer_thickness
            names.append(layer.name)
            layers.append(layer)
            # self.layers.append(layer.name, layer)
        self.stackup = dict(zip(names, layers))
        self.log_info(f"Created {len(self.layers)} layers...")

    def fill_vias(self):
        renders = []
        for via in self.metalizations:
            layer1 = self.get_layer(via[0][0])
            layer2 = self.get_layer(via[0][1])
            pos = via[1]
            shape = via[2]
            self.log_debug(
                f"Adding via metalization between layers {via[0][0]} and {via[0][1]} at {pos}..."
            )
            zmin = min(layer1.zmin, layer2.zmin)
            zmax = max(layer1.zmax, layer2.zmax)
            renders.append(shape.extrude(zmax - zmin, zpos=zmin))
        return v.merge(renders)

    def _dispatch(self, dest: str, obj: KiCADObject, func):
        dest = dest.strip('"')
        if dest.startswith("*"):
            self.log_info(f"Adding object {obj} to multiple layers...: {dest}")
            for layer in self.layers.values():
                if layer.name.endswith(dest[1:]):
                    self.log_debug(
                        f"-> Adding object {obj} to layer '{layer.name}'..."
                    )
                    func(layer, obj)
        elif dest in self.layers:
            func(self.layers[dest], obj)
        else:
            raise Exception(f"Layer '{dest}' not found.")

    def _dispatch_geometry(self, dest: str, obj: KiCADObject):
        self._dispatch(dest, obj, KiCADLayer.add_geometry)

    def _dispatch_segment(self, dest: str, obj: KiCADObject):
        self._dispatch(dest, obj, KiCADLayer.add_segment)

    def _dispatch_arc(self, dest: str, obj: KiCADObject):
        self._dispatch(dest, obj, KiCADLayer.add_arc)

    def _dispatch_footprint(self, dest: str, obj: KiCADObject):
        self._dispatch(dest, obj, KiCADLayer.add_footprint)

    def _dispatch_zone(self, dest: str, obj: KiCADObject):
        self._dispatch(dest, obj, KiCADLayer.add_zone)

    def _dispatch_drill(self, dest: str, obj: KiCADObject):
        self._dispatch(dest, obj, KiCADLayer.add_drill)

    def add_footprint(self, dest: str, obj: KiCADObject):
        self._dispatch_footprint(dest, obj)

    def add_geometry(self, dest: str, obj: KiCADObject):
        self._dispatch_geometry(dest, obj)

    def add_segment(self, dest: str, obj: KiCADObject):
        self._dispatch_segment(dest, obj)

    def add_arc(self, dest: str, obj: KiCADObject):
        self._dispatch_arc(dest, obj)

    def add_zone(self, dest: str, obj: KiCADObject):
        self._dispatch_zone(dest, obj)

    def add_drill(self, dest: str, obj):
        self._dispatch_drill(dest, obj)

    def add_via_metalization(
        self, dest: tuple(str, str), at: tuple(float, float), obj: FTLGeom2D
    ):
        if len(dest) != 2:
            raise Exception("Destination must be a tuple of two layer names.")
        if dest[0] not in self.layers or dest[1] not in self.layers:
            raise Exception(
                f"One or both of the layers do not exist: {dest[0]}, {dest[1]}"
            )
        if len(at) != 2:
            raise Exception("Via position must be a tuple of two floats.")
        if not isinstance(obj, FTLGeom2D):
            raise Exception("Via geometry must be an FTLGeom2D object.")
        self.metalizations.append((dest, at, obj))

    def get_layer(self, name):
        return self.layers[name]

    def get_layers_from_pattern(self, patterns):
        layers = []
        for pattern in patterns:
            pattern = pattern.strip('"')
            self.log_debug(f"Selecting layers by pattern '{pattern}'...")
            if pattern.startswith("*"):
                for layer in self.get_layer_names():
                    if layer.endswith(pattern[1:]):
                        layers.append(self.get_layer(layer))
                        self.log_debug(
                            f"Adding layer '{layer}' to selection..."
                        )
            else:
                layers.append(self.get_layer(pattern))
                self.log_debug(f"Adding layer '{pattern}' to selection...")
            # for layer in self.layers:
            #    if layer.endswith(pattern):
            #        layers.append(layer)
        return set(layers)

    def get_layer_names_from_pattern(self, patterns):
        return [layer.name for layer in self.get_layers_from_pattern(patterns)]

    def get_lowest_layer(self, layers: list()):
        ret = None
        for layer in self.get_stackup_layer_names():
            if layer in layers:
                ret = self.layers[layer]
        return ret

    def get_highest_layer(self, layers: list()):
        for layer in self.get_stackup_layer_names():
            if layer in layers:
                return self.layers[layer]

    def get_layer_names(self):
        return self.layers.keys()

    def get_stackup_layer_names(self):
        return self.stackup.keys()

    def items(self):
        return self.layers.items()

    def layer_has_objects(self, name):
        return self.layers[name].has_objects()

    def render_layer(self, name):
        return self.layers[name].render()


class KiCADLayer(Loggable):
    def __init__(self, parent, id, params):
        Loggable.__init__(self, parent)
        self.params = params
        self.name = params[0].strip('"')
        self.type = params[1]
        self.name_long = params[2] if 2 in params else None
        self.log_debug(
            f"Created layer #{id} '{self.name}' of type '{self.type}'..."
        )
        self.geoms = []
        self.segments = []
        self.arcs = []
        self.zones = []
        self.footprints = []
        self.drills = []
        self.zmin = 0
        self.zmax = 0
        self.thickness = 0

    def has_objects(self):
        return (
            len(self.geoms) > 0
            or len(self.segments) > 0
            or len(self.footprints) > 0
        )

    def add_geometry(self, geom):
        if isinstance(geom, list):
            self.geoms.extend(geom)
        else:
            self.geoms.append(geom)

    def add_segment(self, segment):
        if isinstance(segment, list):
            self.segments.extend(segment)
        else:
            self.segments.append(segment)

    def add_arc(self, arc):
        if isinstance(arc, list):
            self.arcs.extend(arc)
        else:
            self.arcs.append(arc)

    def add_footprint(self, geom):
        if isinstance(geom, list):
            self.footprints.extend(geom)
        else:
            self.footprints.append(geom)

    def add_zone(self, zone):
        if isinstance(zone, list):
            self.zones.extend(zone)
        else:
            self.zones.append(zone)

    def add_drill(self, drill):
        if isinstance(drill, list):
            self.drills.extend(drill)
        else:
            self.drills.append(drill)

    def render(self):
        # fps = self.render_footprints()
        shapes = self.render_shapes()
        # vias = self.render_vias()
        segments = self.render_segments()
        arcs = self.render_arcs()
        zones = self.render_zones()
        ret = FTLGeom2D.make_compound(
            (self.footprints, shapes, segments, arcs, zones)
        )
        drills_rendered = FTLGeom2D.make_compound(self.drills)
        ret.cutout(drills_rendered)
        return ret

    def render_shapes(self):
        renders = []
        if len(self.geoms) > 0:
            self.log_info(f"Rendering {len(self.geoms)} geometries...")
            if self.name == "Edge.Cuts":
                for geom in self.geoms:
                    renders.append(geom.render(force_fill=True))
            else:
                for geom in self.geoms:
                    renders.append(geom.render())
        return FTLGeom2D.make_compound(renders)

    def render_vias(self):
        renders = []
        if len(self.geoms["via"]) > 0:
            self.log_info(f"Rendering {len(self.geoms['via'])} vias...")
            renders = [via.render() for via in self.geoms["via"]]
        return FTLGeom2D.make_compound(renders)

    def render_segments(self):
        renders = []
        if len(self.segments) > 0:
            self.log_info(f"Rendering {len(self.segments)} segments...")
            for segment in self.segments:
                renders.append(
                    FTLGeom2D.get_line(
                        (segment["start"], segment["end"]), segment["width"]
                    )
                )
        return FTLGeom2D.make_compound(renders)

    def render_arcs(self):
        renders = []
        if len(self.arcs) > 0:
            self.log_info(f"Rendering {len(self.arcs)} arcs...")
            for arc in self.arcs:
                renders.append(
                    FTLGeom2D.get_arc(
                        arc["start"],
                        arc["mid"],
                        arc["end"],
                        arc["width"],
                    )
                )
        return FTLGeom2D.make_compound(renders)

    def render_zones(self):
        renders = []
        if len(self.zones) > 0:
            self.log_info(f"Rendering {len(self.zones)} zones...")
            for zone in self.zones:
                renders.append(zone.render())
        return FTLGeom2D.make_compound(renders)


class KiCADObject(ABC, Loggable):
    def __init__(self, parent, params: dict):
        Loggable.__init__(self, parent)
        self.params = params
        # self.name = params[0] if 0 in params else None
        self.layer = params["layer"] if "layer" in params else None
        self.layers = params["layers"] if "layers" in params else None
        # self.descr = params["descr"]
        # self.tags = params["tags"]
        # self.path = params["path"] if "path" in params else None

    @abstractmethod
    def render(self):
        pass


class KiCADEntity(KiCADObject):
    def __init__(self, parent, params: dict):
        KiCADObject.__init__(self, parent, params)
        self.params = params
        self.name = params[0] if 0 in params else None
        self.layer = params["layer"] if "layer" in params else None
        self.layers = params["layers"] if "layers" in params else None
        self.at = params["at"]
        self.angle = self.at[2] if len(self.at) > 2 else 0
        # self.descr = params["descr"]
        # self.tags = params["tags"]
        # self.path = params["path"] if "path" in params else None

    @property
    def x(self):
        return self.at[0]

    @property
    def y(self):
        return self.at[1]

    def move_relative(self, dx: float = None, dy: float = None):
        if isinstance(dx, (tuple, list)) and dy is None:
            dx, dy = dx[0], dx[1]
        self.at = (self.at[0] + dx, self.at[1] + dy)


class KiCADSegment(KiCADObject):
    def __init__(self, parent: Loggable, params: dict):
        super().__init__(parent, params)
        self.start = params["start"]
        self.end = params["end"]
        self.width = params["width"]
        self.layer = params["layer"]


class KiCADZone(KiCADObject):
    def __init__(self, parent: Loggable, params: dict):
        super().__init__(parent, params)
        self.net = params["net"]
        self.net_name = params["net_name"]
        self.layer = params["layer"]
        self.hatch = params["hatch"]
        self.connect_pads = params["connect_pads"]
        self.min_thickness = params["min_thickness"]
        self.fill = params["fill"]
        # self.thermal_width = params["thermal_width"]
        # self.thermal_gap = params["thermal_gap"]
        # self.thermal_bridge = params["thermal_bridge"]
        self.polygon = params["polygon"]
        self.filled_polygon = []
        for filled_polygon in params["filled_polygon"]:
            self.filled_polygon.append(
                KiCADFilledPolygon(self, filled_polygon)
            )

    def render(self):
        geom = [poly.render() for poly in self.filled_polygon]
        return FTLGeom2D.make_compound(geom)


class KiCADPolygon(KiCADObject):
    def __init__(self, parent: Loggable, params: dict):
        super().__init__(parent, params)
        self.points = list(params["pts"]["xy"])
        self.points.append(self.points[0])
        self.stroke_type = params["stroke"]["type"]
        self.stroke_width = params["stroke"]["width"]
        self.fill = params["fill"]
        self.log_debug(
            f"Making polygon with {len(self.points)} points, stroke type {self.stroke_type}, width {self.stroke_width} and fill {self.fill}..."
        )

    def render(self, force_fill=False):
        geom = FTLGeom2D()
        if force_fill:
            geom.add_polygon(sh.Polygon(self.points))
        elif self.fill == "none" and self.stroke_width:
            geom.add_line(self.points, self.stroke_width)
        elif self.fill != "none" and not self.stroke_width:
            geom.add_polygon(sh.Polygon(self.points))
            self.log_warning("Filling of polygons is currently not tested.")
        else:
            raise Exception(
                "Unsupported combination of stroke and fill: stroke_type = <{self.stroke_type}>, stroke_width = {self.stroke_width}, fill = <{self.fill}>"
            )
        return geom


class KiCADFilledPolygon(KiCADObject):
    def __init__(self, parent: Loggable, params: dict):
        super().__init__(parent, params)
        self.points = list(params["pts"]["xy"])
        self.points.append(self.points[0])
        # self.stroke_type = params["stroke"]["type"]
        # self.stroke_width = params["stroke"]["width"]
        # self.fill = params["fill"]
        self.log_debug(
            f"Making filled polygon with {len(self.points)} points..."
        )

    def render(self, force_fill=False):
        geom = FTLGeom2D()
        geom.add_polygon(sh.Polygon(self.points))
        return geom


class KiCADRect(KiCADPolygon):
    def __init__(self, parent: Loggable, params: dict):
        # Loggable.__init__(self, parent)
        params["pts"] = {
            "xy": [
                params["start"],
                (params["end"][0], params["start"][1]),
                params["end"],
                (params["start"][0], params["end"][1]),
            ]
        }
        KiCADPolygon.__init__(self, parent, params)
        self.log_debug(f"Making rectangle with {params}...")

    def render(self, force_fill=False):
        return super().render(force_fill)


class KiCADPart(KiCADEntity):
    def __init__(self, parent: Loggable, params: dict):
        KiCADEntity.__init__(self, parent, params)
        # self.angle = self.at[2] if len(self.at) > 2 else 0
        self.descr = dict["descr"]
        self.tags = dict["tags"]
        self.layer = params["layer"]
        self.path = params["path"] if "path" in params else None
        self.pads = params["pad"] if "pad" in params else None
        self.pads = params["pad"] if "pad" in params else None
        self.geoms = {
            "fp_text": [],
            "fp_line": [],
            "fp_circle": [],
            "fp_arc": [],
            "fp_poly": [],
            "fp_curve": [],
        }
        for key in self.geoms.keys():
            self.geoms[key] = params[key] if key in params else []

    def render(self, layers=None) -> FTLGeom2D:
        self.log_info(f"Rendering part {self.name} at {self.at}...")
        self.log_info("->Rendering pads...")
        pads = self.render_pads(layers)
        self.log_info("->Rendering shapes...")
        shapes = self.render_shapes(layers)
        return FTLGeom2D.make_compound((pads, shapes))

    def render_pads(self, layers=None) -> FTLGeom2D:
        rendered_pads = []
        for pad_obj in self.pads:
            pad = KiCADPad(self, pad_obj)
            pad.move_relative(self.at[0], self.at[1])
            render = pad.render(layers)
            if layers is None:
                rendered_pads.append(render)
            else:
                for layer in pad.layers:
                    layer = layer.strip('"')
                    self.log_debug(
                        f"Adding pad {pad.name} to layer '{layer}'..."
                    )
                    layers.add_footprint(layer, render)
        return FTLGeom2D.make_compound(rendered_pads)

    def render_shapes(self, layers=None) -> FTLGeom2D:
        geom = []
        if len(self.geoms["fp_line"]) > 0:
            self.log_info(f"Rendering {len(self.geoms['fp_line'])} lines...")
            for line in self.geoms["fp_line"]:
                if line["stroke"]["type"] == "solid":
                    render = FTLGeom2D.get_line(
                        (line["start"], line["end"]),
                        line["stroke"]["width"],
                    )
                    if layers is None:
                        geom.append(render)
                    else:
                        layers.add_footprint(
                            line["layer"],
                            render.translate(self.at[0], self.at[1]),
                        )
                else:
                    raise Exception(
                        f"Unsupported line stroke type: <{line['stroke']['type']}>"
                    )
        if len(self.geoms["fp_circle"]) > 0:
            self.log_info(
                f"Rendering {len(self.geoms['fp_circle'])} circles..."
            )
            for circle in self.geoms["fp_circle"]:
                self.log_debug(
                    f"Rendering circle at {self.geoms['fp_circle'][0]['center']} with radius {self.geoms['fp_circle'][0]['radius']}"
                )
                render = FTLGeom2D.get_circle(
                    circle["center"], circle["radius"]
                )
                if layers is None:
                    geom.append(render)
                else:
                    layers.add_footprint(
                        circle["layer"],
                        render.translate(self.at[0], self.at[1]),
                    )
        if len(self.geoms["fp_arc"]) > 0:
            self.log_info(f"Rendering {len(self.geoms['fp_arc'])} arcs...")
            for arc in self.geoms["fp_arc"]:
                self.log_debug(
                    f"Rendering arc from {arc['start']} to {arc['end']} with mid {arc['mid']}"
                )
                self.log_debug(
                    f"Stroke type: {arc['stroke']['type']}, stroke width: {arc['stroke']['width']}"
                )
                start = arc["start"]
                mid = arc["mid"]
                end = arc["end"]
                stroke_type = arc["stroke"]["type"]
                stroke_width = arc["stroke"]["width"]
                if stroke_type == "solid":
                    render = FTLGeom2D.get_arc(start, mid, end, stroke_width)
                else:
                    raise Exception(
                        f"Unsupported arc stroke type: <{stroke_type}>"
                    )
                if layers is None:
                    geom.append(render)
                else:
                    layers.add_footprint(
                        arc["layer"], render.translate(self.at[0], self.at[1])
                    )
        if len(self.geoms["fp_poly"]) > 0:
            self.log_info(
                f"Rendering {len(self.geoms['fp_poly'])} polygons..."
            )
            raise Exception("Polygons not supported yet.")
        if len(self.geoms["fp_curve"]) > 0:
            self.log_info(f"Rendering {len(self.geoms['fp_curve'])} curves...")
            raise Exception("Curves not supported yet.")
        ret = FTLGeom2D.make_compound(geom)
        ret.translate(self.at[0], self.at[1])
        return ret

    def render_text(self):
        pass


class KiCADPad(KiCADEntity):
    def __init__(self, parent: Loggable, params: dict):
        super().__init__(parent, params)
        self.log_debug(f"Making pad with {params}")
        self.log_debug(f"{params[0]} - {params[1]} - {params[2]}")
        self.name = params[0]
        self.type = params[1]
        self.shape = params[2].strip()
        self.size = params["size"]
        self.layers = params["layers"]
        self.net = params["net"] if "net" in params else None
        self.drill = params["drill"] if "drill" in params else None
        self.pintype = params["pintype"] if "path" in params else None

    def render(self, layers: KiCADStackupManager = None):
        geom = FTLGeom2D()
        self.log_debug(
            f"Making Pad at {self.at} with size {self.size} and shape {self.shape}..."
        )
        if not isinstance(self.shape, str):
            raise Exception(
                f"Unsupported pad shape type: <{type(self.shape)}>"
            )
        if self.shape == "rect":
            self.log_debug(
                f"Rendering rectangle at {self.at} with size {self.size}"
            )
            geom.add_rectangle(
                (self.at[0] - self.size[0] / 2, self.at[1] - self.size[1] / 2),
                (self.at[0] + self.size[0] / 2, self.at[1] + self.size[1] / 2),
            )
        elif self.shape == "circle":
            self.log_debug(
                f"Rendering circle at {self.at} with size {self.size}"
            )
            geom.add_circle(self.at, self.size[0] / 2)
        elif self.shape == "oval":
            self.log_debug(
                f"Rendering oval at {self.at} with size {self.size}"
            )
            geom.add_ellipse(
                self.at,
                (
                    self.size[0] / 2,
                    self.size[1] / 2,
                ),
            )
        elif self.shape == "roundrect":
            rratio = self.params["roundrect_rratio"]
            radius = min(self.size[0], self.size[1]) * rratio
            geom.add_roundrect(
                (self.at[0] - self.size[0] / 2, self.at[1] - self.size[1] / 2),
                (self.at[0] + self.size[0] / 2, self.at[1] + self.size[1] / 2),
                radius,
            )
            self.log_debug(
                f"Making roundrect at {self.at} with size {self.size} and rratio {self.params['roundrect_rratio']}"
            )
            # return geom.add_roundrect()
        elif self.shape == "trapezoid":
            raise Exception(f"Unsupported pad shape: <{self.shape}>")
        else:
            raise Exception(f"Unsupported pad shape: <{self.shape}>")

        if self.drill is not None:
            self.log_debug(
                f"Drilling hole at {self.at} with drill size {self.drill[0]}"
            )
            # if len(self.drill) > 1:
            #    print("Multiple Arguments...")
            #    if not self.drill[1] in ("oval", "circle"):
            #        raise Exception(f"Unsupported drill shape: <{self.drill[1]}>")
            # geom.cutout(FTLGeom2D.get_circle(self.at, self.drill))
            drill = FTLGeom2D.get_circle(self.at, self.drill[0] / 2)
            for layer in self.layers:
                layers.add_drill(layer, drill)
                layers.add_drill("Edge.Cuts", drill)
            matched_layers = layers.get_layer_names_from_pattern(self.layers)
            self.log_debug(f"Adding pad to layers {matched_layers}...")
            lowest_layer = layers.get_lowest_layer(matched_layers).name
            highest_layer = layers.get_highest_layer(matched_layers).name
            layers.add_via_metalization(
                (lowest_layer, highest_layer), self.at, self.get_metalization()
            )

        if self.angle != 0:
            geom.rotate(self.angle, self.at)

        return geom

    def get_drill(self):
        if self.drill is not None:
            return FTLGeom2D.get_circle(self.at, self.drill[0] / 2)
        else:
            raise Exception("No drill size specified.")

    def make_drills(self, layers: KiCADLayer):
        self.log_debug(f"Making drills for via at {self.at}...")
        if layers is not None:
            for layer in self.layers:
                layers.add_drill(layer, self.get_drill())
            layers.add_drill("Edge.Cuts", self.get_drill())
            # geom.cutout(sh.Point(self.at).buffer(float(self.drill / 2)))

    def get_metalization(self):
        ret = self.get_drill()
        ret.cutout(
            FTLGeom2D.get_circle(
                self.at, self.drill[0] / 2 - KiCADConfig.via_metalization
            )
        )
        return ret


class KiCADVia(KiCADEntity):
    def __init__(self, parent: Loggable, params: dict):
        super().__init__(parent, params)
        self.size = params["size"]
        self.drill = params["drill"]

    def render(self, layers: KiCADLayer = None):
        geom = FTLGeom2D.get_circle(self.at, self.size / 2)
        # drill = FTLGeom2D.get_circle(self.at, self.drill / 2)
        return geom

    def get_layer_names(self):
        return [layer.strip('"') for layer in self.layers]

    def get_drill(self):
        return FTLGeom2D.get_circle(self.at, self.drill / 2)

    def make_drills(self, layers: KiCADLayer):
        self.log_debug(f"Making drills for via at {self.at}...")
        if layers is not None:
            for layer in self.layers:
                layers.add_drill(layer, self.get_drill())
            layers.add_drill("Edge.Cuts", self.get_drill())
            # geom.cutout(sh.Point(self.at).buffer(float(self.drill / 2)))

    def get_metalization(self):
        ret = self.get_drill()
        ret.cutout(
            FTLGeom2D.get_circle(
                self.at, self.drill / 2 - KiCADConfig.via_metalization
            )
        )
        return ret
