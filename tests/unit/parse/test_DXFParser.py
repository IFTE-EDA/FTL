from __future__ import annotations
from pathlib import Path

import gmsh
import numpy as np

from FTL.parse.DXFParser import DXFParser

PRECISION_DIGITS = 2


def get_file(file_name: str):
    return Path(__file__).parent.parent.parent / "data" / file_name


def get_bbox_rounded(dim, tag):
    return [
        round(i, PRECISION_DIGITS)
        for i in gmsh.model.occ.getBoundingBox(dim, tag)
    ]


def get_mass_rounded(dim, tag):
    return round(gmsh.model.occ.getMass(dim, tag), PRECISION_DIGITS)


def get_com_rounded(dim, tag):
    return [
        round(i, PRECISION_DIGITS)
        for i in gmsh.model.occ.getCenterOfMass(dim, tag)
    ]


class Test_DXFParser:
    def setup_class(self):
        pass

    def test_dxfparser_open_non_existent_file(self):
        try:
            DXFParser(get_file("non_existent_file.dxf"))
        except Exception as e:
            print("Exception type: ", type(e))
            print("Assertion: ", isinstance(e, FileNotFoundError))
            if isinstance(e, FileNotFoundError):
                return
        assert False

    def test_dxfparser_layers(self):
        parser = DXFParser(get_file("layers.dxf"))
        print("Layers: ", parser.get_layer_names())
        assert parser.get_layer_names() == [
            "0",
            "Defpoints",
            "TestLayer1",
            "TestLayer2",
            "TestLayer3",
        ]

    def test_dxfparser_get_layer_not_existant(self):
        parser = DXFParser(get_file("layers.dxf"))
        try:
            parser.get_layer("NonExistantLayer")
        except Exception as e:
            print("Exception type: ", type(e))
            print("Assertion: ", isinstance(e, KeyError))
            if isinstance(e, KeyError):
                return
        assert False

    def test_dxfparser_get_layer(self):
        parser = DXFParser(get_file("layers.dxf"))
        print(parser.get_layer("TestLayer1").name)
        assert parser.get_layer("TestLayer1").name == "TestLayer1"
        assert parser.get_layer("TestLayer2").name == "TestLayer2"
        assert parser.get_layer("TestLayer3").name == "TestLayer3"

    def test_dxfparser_lines(self):
        parser = DXFParser(get_file("lines.dxf"))
        print("Layers: ", parser.get_layer_names())
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 4
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LINE"
            print("Start: ", e.dxf.start)
            print("End: ", e.dxf.end)
            assert e.dxf.start in [(0, 0), (10, 0), (10, 10), (0, 10)]
            assert e.dxf.end in [(0, 0), (10, 0), (10, 10), (0, 10)]
            assert e.dxf.thickness == 1
        layer2 = parser.get_layer("width_2")
        assert len(layer2.get_entities()) == 1
        for e in layer2.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LINE"
            print("Start: ", e.dxf.start)
            print("End: ", e.dxf.end)
            assert e.dxf.start == (0, 0)
            assert e.dxf.end == (10, 10)
            assert e.dxf.thickness == 2

    def test_dxfparser_arc(self):
        parser = DXFParser(get_file("arc.dxf"))
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "ARC"
            assert e.dxf.center == (0, 0)
            assert e.dxf.radius == 5

    def test_dxfparser_circle(self):
        parser = DXFParser(get_file("circle.dxf"))
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "CIRCLE"
            assert e.dxf.center == (0, 0)
            assert e.dxf.radius == 5

    def test_dxfparser_polyline(self):
        parser = DXFParser(get_file("polyline.dxf"))
        layer = parser.get_layer("straight_cw3")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LWPOLYLINE"
            assert not e.is_closed
            assert e.dxf.const_width == 3
            print("Points: ", e.get_points())
            print("Checking points...")
            points_rounded = [(p[0], p[1]) for p in e.get_points()]
            assert points_rounded == [(0, 0), (10, 0)]
            widths = [(p[2], p[3]) for p in e.get_points()]
            assert widths == [(0.0, 0.0), (0.0, 0.0)]
        """
        layer = parser.get_layer("straight_w2")
        assert len(layer.get_entities()) == 1
        e = layer.get_entities()[0]
        print("Entity: ", e)
        assert e.dxftype() == "LWPOLYLINE"
        assert not e.is_closed
        assert e.dxf.const_width == 0
        print("Points: ", e.get_points())
        print("Checking points...")
        points_rounded = [(p[0], p[1], p[2]) for p in e.get_points()]
        assert points_rounded == [(0, 0, 2), (10, 0, 2)]
        """

    def test_dxfparser_poly(self):
        gmsh.clear()
        parser = DXFParser(get_file("poly.dxf"))
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LWPOLYLINE"
            assert e.is_closed
            print("Points: ", e.get_points())
            print("Checking points...")
            points_rounded = [(p[0], p[1]) for p in e.get_points()]
            assert points_rounded == [(0, 0), (10, 0), (10, 10), (0, 10)]
            print("Checking bulges...")
            bulges = [p[4] for p in e.get_points()]
            assert bulges == [0.0, 0.0, 0.0, 0.0]
            widths = [(p[2], p[3]) for p in e.get_points()]
            assert widths == [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]

    def test_dxfparser_poly_bulge(self):
        parser = DXFParser(get_file("poly_bulge.dxf"))
        layer = parser.get_layer("0")
        assert len(layer.get_entities()) == 1
        for e in layer.get_entities():
            print("Entity: ", e)
            assert e.dxftype() == "LWPOLYLINE"
            print("Points: ", e.get_points())
            print("Checking points...")
            points_rounded = [(p[0], p[1]) for p in e.get_points()]
            assert points_rounded == [(0, 0), (10, 0), (10, 10), (0, 10)]
            print("Checking bulges...")
            bulges = [p[4] for p in e.get_points()]
            assert bulges == [0.5, 0.5, 0.5, 0.5]
            widths = [(p[2], p[3]) for p in e.get_points()]
            assert widths == [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]

    def test_dxfparser_open_2parts_poly_invert_none(self):
        gmsh.clear()
        parser = DXFParser(get_file("poly_open_2parts.dxf"))
        layer = parser.get_layer("invert_none")
        assert len(layer.get_entities()) == 2
        layer.render()
        assert gmsh.model.get_entities(2) == [(2, 1)]
        assert gmsh.model.get_entities(1) == [(1, i) for i in range(1, 5)]
        assert gmsh.model.get_entities(0) == [(0, i) for i in range(1, 5)]
        assert get_bbox_rounded(2, 1) == [0.0, 0.0, 0.0, 10.0, 10.0, 0.0]

    def test_dxfparser_open_2parts_poly_invert_second(self):
        gmsh.clear()
        parser = DXFParser(get_file("poly_open_2parts.dxf"))
        layer = parser.get_layer("invert_second")
        assert len(layer.get_entities()) == 2
        layer.render()
        assert gmsh.model.get_entities(2) == [(2, 1)]
        assert gmsh.model.get_entities(1) == [(1, i) for i in range(1, 5)]
        assert gmsh.model.get_entities(0) == [(0, i) for i in range(1, 5)]
        assert get_bbox_rounded(2, 1) == [0.0, 0.0, 0.0, 10.0, 10.0, 0.0]

    def test_dxfparser_open_2parts_poly_invert_first(self):
        gmsh.clear()
        parser = DXFParser(get_file("poly_open_2parts.dxf"))
        layer = parser.get_layer("invert_first")
        assert len(layer.get_entities()) == 2
        layer.render()
        assert gmsh.model.get_entities(2) == [(2, 1)]
        assert gmsh.model.get_entities(1) == [(1, i) for i in range(1, 5)]
        assert gmsh.model.get_entities(0) == [(0, i) for i in range(1, 5)]
        assert get_bbox_rounded(2, 1) == [0.0, 0.0, 0.0, 10.0, 10.0, 0.0]

    def test_dxfparser_open_2parts_poly_invert_first_and_second(self):
        gmsh.clear()
        parser = DXFParser(get_file("poly_open_2parts.dxf"))
        layer = parser.get_layer("invert_first_and_second")
        assert len(layer.get_entities()) == 2
        layer.render()
        assert gmsh.model.get_entities(2) == [(2, 1)]
        assert gmsh.model.get_entities(1) == [(1, i) for i in range(1, 5)]
        assert gmsh.model.get_entities(0) == [(0, i) for i in range(1, 5)]
        assert get_bbox_rounded(2, 1) == [0.0, 0.0, 0.0, 10.0, 10.0, 0.0]

    def _execute_3parts_test(self, pattern: str):
        gmsh.clear()
        parser = DXFParser(get_file("poly_open_3parts.dxf"))
        layer = parser.get_layer(pattern)
        assert len(layer.get_entities()) == 3
        layer.render()
        assert gmsh.model.get_entities(2) == [(2, 1)]
        assert gmsh.model.get_entities(1) == [(1, i) for i in range(1, 9)]
        assert gmsh.model.get_entities(0) == [(0, i) for i in range(1, 9)]
        assert get_bbox_rounded(2, 1) == [0.0, 0.0, 0.0, 10.0, 10.0, 0.0]
        assert get_mass_rounded(2, 1) == 100.0
        assert get_com_rounded(2, 1) == [5.0, 5.0, 0.0]

    def test_dxfparser_open_3parts_poly_ppp(self):
        self._execute_3parts_test("ppp")

    def test_dxfparser_open_3parts_poly_ppi(self):
        self._execute_3parts_test("ppi")

    def test_dxfparser_open_3parts_poly_pip(self):
        self._execute_3parts_test("pip")

    def test_dxfparser_open_3parts_poly_pii(self):
        self._execute_3parts_test("pii")

    def test_dxfparser_open_3parts_poly_ipp(self):
        self._execute_3parts_test("ipp")

    def test_dxfparser_open_3parts_poly_ipi(self):
        self._execute_3parts_test("ipi")

    def test_dxfparser_open_3parts_poly_iip(self):
        self._execute_3parts_test("iip")

    def test_dxfparser_open_3parts_poly_iii(self):
        self._execute_3parts_test("iii")
