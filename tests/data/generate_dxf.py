from pathlib import Path
import ezdxf

data_dir = Path(__file__).parent


def main():
    print("Making DXF test files")
    make_dxf_layers()
    make_dxf_lines()
    make_dxf_arc()
    make_dxf_circle()
    make_dxf_polyline()
    make_dxf_poly_nobulge()
    make_dxf_poly_bulge()
    make_dxf_poly_duplicated_points()
    make_dxf_poly_snap_endpoints()
    make_dxf_poly_open_2parts()
    make_dxf_poly_open_3parts()
    make_dxf_poly_bulge_orientation()
    make_dxf_poly_holes()


def make_dxf_layers():
    doc = ezdxf.new("R2010")
    doc.layers.add("TestLayer1")
    doc.layers.add("TestLayer2")
    doc.layers.add("TestLayer3")
    doc.saveas(data_dir / "layers.dxf")


def make_dxf_lines():
    doc = ezdxf.new("R2010")
    doc.layers.add(name="width_2")
    msp = doc.modelspace()
    line1 = msp.add_line((0, 0), (10000, 0))
    line1.dxf.lineweight = 100
    line2 = msp.add_line((10000, 0), (10000, 10000))
    line2.dxf.lineweight = 100
    line3 = msp.add_line((10000, 10000), (0, 10000))
    line3.dxf.lineweight = 100
    line4 = msp.add_line((0, 10000), (0, 0))
    line4.dxf.lineweight = 100

    msp.add_line(
        (0, 0),
        (10000, 10000),
        dxfattribs={"layer": "width_2", "lineweight": 200},
    )
    doc.saveas(data_dir / "lines.dxf")


def make_dxf_circle():
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_circle(center=(0, 0), radius=5)
    doc.saveas(data_dir / "circle.dxf")


def make_dxf_arc():
    doc = ezdxf.new("R2010")
    doc.layers.add(name="180")
    doc.layers.add(name="270")
    doc.layers.add(name="different_angles")
    doc.layers.add(name="different_center")
    msp = doc.modelspace()
    msp.add_arc(center=(0, 0), radius=5, start_angle=0, end_angle=90)
    msp.add_arc(
        center=(0, 0),
        radius=5,
        start_angle=0,
        end_angle=180,
        dxfattribs={"layer": "180"},
    )
    msp.add_arc(
        center=(0, 0),
        radius=5,
        start_angle=0,
        end_angle=270,
        dxfattribs={"layer": "270"},
    )
    msp.add_arc(
        center=(0, 0),
        radius=5,
        start_angle=180,
        end_angle=90,
        dxfattribs={"layer": "different_angles"},
    )
    msp.add_arc(
        center=(5, 5),
        radius=5,
        start_angle=180,
        end_angle=90,
        dxfattribs={"layer": "different_center"},
    )
    # msp.add_arc_dim_3p((0, 0), (5, 0), (5, 5), 0, 90)
    doc.saveas(data_dir / "arc.dxf")


def make_dxf_polyline():
    doc = ezdxf.new("R2010")
    doc.layers.add(name="straight_cw3")
    # doc.layers.add(name="straight_w2")
    msp = doc.modelspace()
    points = [(0, 0), (10, 0)]
    polyline = msp.add_lwpolyline(points, dxfattribs={"layer": "straight_cw3"})
    polyline.dxf.const_width = 3
    # polyline.dxf.thickness = 6
    polyline.close(False)
    doc.saveas(data_dir / "polyline.dxf")


def make_dxf_poly_nobulge():
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    points = [(0, 0), (10, 0), (10, 10), (0, 10)]
    polyline = msp.add_lwpolyline(points)
    doc.saveas(data_dir / "poly_open.dxf")
    polyline.close(True)
    doc.saveas(data_dir / "poly.dxf")


def make_dxf_poly_bulge():
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    points_b_out = [(0, 0, 0.5), (10, 0, 0.5), (10, 10, 0.5), (0, 10, 0.5)]
    points_b_in = [(0, 0, -0.2), (10, 0, -0.2), (10, 10, -0.2), (0, 10, -0.2)]
    polyline_b_out = msp.add_lwpolyline(points_b_out, format="xyb")
    polyline_b_out.close(True)
    doc.layers.add(name="1", color=7)
    polyline_b_in = msp.add_lwpolyline(
        points_b_in, format="xyb", dxfattribs={"layer": "1"}
    )
    polyline_b_in.close(True)
    doc.saveas(data_dir / "poly_bulge.dxf")


def make_dxf_poly_duplicated_points():
    doc = ezdxf.new("R2010")
    doc.layers.add(name="straight")
    msp = doc.modelspace()
    points_b_out = [
        (0, 0, 0),
        (10, 0, 0),
        (10, 0, 0),
        (10, 10, 0),
        (0, 10, 0),
        (0, 10, 0),
        (0, 0, 0),
    ]
    polyline_b_out = msp.add_lwpolyline(
        points_b_out, format="xyb", dxfattribs={"layer": "straight"}
    )
    polyline_b_out.close(False)
    doc.layers.add(name="straight_closed")
    msp = doc.modelspace()
    points_b_out = [
        (0, 0, 0),
        (10, 0, 0),
        (10, 0, 0),
        (10, 10, 0),
        (0, 10, 0),
        (0, 10, 0),
        (0, 0, 0),
    ]
    polyline_b_out = msp.add_lwpolyline(
        points_b_out, format="xyb", dxfattribs={"layer": "straight_closed"}
    )
    polyline_b_out.close(True)
    doc.layers.add(name="bulge")
    msp = doc.modelspace()
    points_b_out = [
        (0, 0, 1),
        (10, 0, 0),
        (10, 0, 1),
        (10, 10, 1),
        (0, 10, 0),
        (0, 10, 1),
        (0, 0, 0),
    ]
    polyline_b_out = msp.add_lwpolyline(
        points_b_out, format="xyb", dxfattribs={"layer": "bulge"}
    )
    polyline_b_out.close(False)
    doc.saveas(data_dir / "poly_duplicate_points_bulge.dxf")


def make_dxf_poly_snap_endpoints():
    doc = ezdxf.new("R2010")
    doc.layers.add(name="snap_straight")
    msp = doc.modelspace()

    pts = [
        (0, 0, 0),
        (10, 0, 0),
        (10, 10, 0),
        (0, 10, 0),
        (-0.01, -0.01, 0),
    ]
    poly = msp.add_lwpolyline(
        pts, format="xyb", dxfattribs={"layer": "snap_straight"}
    )
    poly.close(False)
    poly.dxf.const_width = 0

    doc.saveas(data_dir / "poly_snap_endpoints.dxf")


def make_dxf_poly_open_2parts():
    doc = ezdxf.new("R2010")
    doc.layers.add(name="invert_none")
    doc.layers.add(name="invert_first")
    doc.layers.add(name="invert_second")
    doc.layers.add(name="invert_first_and_second")
    msp = doc.modelspace()

    pts_first_plain = [
        (0, 0, 0),
        (10, 0, 0),
        (10, 10, 0),
        (0, 10, 0),
    ]
    pts_second_plain = [
        (0, 10, 0),
        (0, 0, 0),
    ]
    pts_first_inverted = [
        (0, 10, 0),
        (10, 10, 0),
        (10, 0, 0),
        (0, 0, 0),
    ]
    pts_second_inverted = [
        (0, 0, 0),
        (0, 10, 0),
    ]
    poly1a = msp.add_lwpolyline(
        pts_first_plain, format="xyb", dxfattribs={"layer": "invert_none"}
    )
    poly1a.close(False)
    poly1a.dxf.const_width = 0
    poly1b = msp.add_lwpolyline(
        pts_second_plain, format="xyb", dxfattribs={"layer": "invert_none"}
    )
    poly1b.close(False)
    poly1b.dxf.const_width = 0

    poly2a = msp.add_lwpolyline(
        pts_first_plain, format="xyb", dxfattribs={"layer": "invert_second"}
    )
    poly2a.close(False)
    poly2a.dxf.const_width = 0
    poly2b = msp.add_lwpolyline(
        pts_second_inverted,
        format="xyb",
        dxfattribs={"layer": "invert_second"},
    )
    poly2b.close(False)
    poly2b.dxf.const_width = 0

    poly3a = msp.add_lwpolyline(
        pts_first_inverted, format="xyb", dxfattribs={"layer": "invert_first"}
    )
    poly3a.close(False)
    poly3a.dxf.const_width = 0
    poly3b = msp.add_lwpolyline(
        pts_second_plain, format="xyb", dxfattribs={"layer": "invert_first"}
    )
    poly3b.close(False)
    poly3b.dxf.const_width = 0

    poly4a = msp.add_lwpolyline(
        pts_first_inverted,
        format="xyb",
        dxfattribs={"layer": "invert_first_and_second"},
    )
    poly4a.close(False)
    poly4a.dxf.const_width = 0
    poly4b = msp.add_lwpolyline(
        pts_second_inverted,
        format="xyb",
        dxfattribs={"layer": "invert_first_and_second"},
    )
    poly4b.close(False)
    poly4b.dxf.const_width = 0

    doc.saveas(data_dir / "poly_open_2parts.dxf")


def make_dxf_poly_open_3parts():
    def _make_layer(msp, pattern: tuple[bool], layer: str):
        poly1 = msp.add_lwpolyline(
            pts_first_plain if pattern[0] else pts_first_inverted,
            format="xyb",
            dxfattribs={"layer": layer},
        )
        poly1.close(False)
        poly1.dxf.const_width = 0
        poly2 = msp.add_lwpolyline(
            pts_second_plain if pattern[1] else pts_second_inverted,
            format="xyb",
            dxfattribs={"layer": layer},
        )
        poly2.close(False)
        poly2.dxf.const_width = 0
        poly2 = msp.add_lwpolyline(
            pts_third_plain if pattern[2] else pts_third_inverted,
            format="xyb",
            dxfattribs={"layer": layer},
        )
        poly2.close(False)
        poly2.dxf.const_width = 0

    doc = ezdxf.new("R2010")
    doc.layers.add(name="ppp")
    doc.layers.add(name="ppi")
    doc.layers.add(name="pip")
    doc.layers.add(name="pii")
    doc.layers.add(name="ipp")
    doc.layers.add(name="ipi")
    doc.layers.add(name="iip")
    doc.layers.add(name="iii")
    msp = doc.modelspace()

    pts_first_plain = [
        (0, 0, 0),
        (5, 0, 0),
        (10, 0, 0),
        (10, 5, 0),
        (10, 10, 0),
    ]
    pts_second_plain = [
        (10, 10, 0),
        (5, 10, 0),
        (0, 10, 0),
    ]
    pts_third_plain = [
        (0, 10, 0),
        (0, 5, 0),
        (0, 0, 0),
    ]
    pts_first_inverted = [
        (10, 10, 0),
        (10, 5, 0),
        (10, 0, 0),
        (5, 0, 0),
        (0, 0, 0),
    ]
    pts_second_inverted = [
        (0, 10, 0),
        (5, 10, 0),
        (10, 10, 0),
    ]
    pts_third_inverted = [
        (0, 0, 0),
        (0, 5, 0),
        (0, 10, 0),
    ]

    _make_layer(msp, (True, True, True), "ppp")
    _make_layer(msp, (True, True, False), "ppi")
    _make_layer(msp, (True, False, True), "pip")
    _make_layer(msp, (True, False, False), "pii")
    _make_layer(msp, (False, True, True), "ipp")
    _make_layer(msp, (False, True, False), "ipi")
    _make_layer(msp, (False, False, True), "iip")
    _make_layer(msp, (False, False, False), "iii")

    doc.saveas(data_dir / "poly_open_3parts.dxf")


def make_dxf_poly_bulge_orientation():
    def _make_layer(msp, pattern: tuple[bool], layer: str):
        poly1 = msp.add_lwpolyline(
            pts_first_plain if pattern[0] else pts_first_inverted,
            format="xyb",
            dxfattribs={"layer": layer},
        )
        poly1.close(False)
        poly1.dxf.const_width = 0
        poly2 = msp.add_lwpolyline(
            pts_second_plain if pattern[1] else pts_second_inverted,
            format="xyb",
            dxfattribs={"layer": layer},
        )
        poly2.close(False)
        poly2.dxf.const_width = 0
        poly2 = msp.add_lwpolyline(
            pts_third_plain if pattern[2] else pts_third_inverted,
            format="xyb",
            dxfattribs={"layer": layer},
        )
        poly2.close(False)
        poly2.dxf.const_width = 0

    doc = ezdxf.new("R2010")
    doc.layers.add(name="ppp")
    doc.layers.add(name="ppi")
    doc.layers.add(name="pip")
    doc.layers.add(name="pii")
    doc.layers.add(name="ipp")
    doc.layers.add(name="ipi")
    doc.layers.add(name="iip")
    doc.layers.add(name="iii")
    msp = doc.modelspace()

    pts_first_plain = [
        (0, 0, 0),
        (3, 0, 0.2),
        (7, 0, 0),
        (10, 0, 0),
        (10, 3, 0.4),
        (10, 7, 0),
        (10, 10, 0),
    ]
    pts_second_plain = [
        (10, 10, 0),
        (7, 10, 0.6),
        (3, 10, 0),
        (0, 10, 0),
    ]
    pts_third_plain = [
        (0, 10, 0),
        (0, 7, 0.8),
        (0, 3, 0),
        (0, 0, 0),
    ]
    pts_first_inverted = [
        (10, 10, 0),
        (10, 7, -0.4),
        (10, 3, 0),
        (10, 0, 0),
        (7, 0, -0.2),
        (3, 0, 0),
        (0, 0, 0),
    ]
    pts_second_inverted = [
        (0, 10, 0),
        (3, 10, -0.6),
        (7, 10, 0),
        (10, 10, 0),
    ]
    pts_third_inverted = [
        (0, 0, 0),
        (0, 3, -0.8),
        (0, 7, 0),
        (0, 10, 0),
    ]

    _make_layer(msp, (True, True, True), "ppp")
    _make_layer(msp, (True, True, False), "ppi")
    _make_layer(msp, (True, False, True), "pip")
    _make_layer(msp, (True, False, False), "pii")
    _make_layer(msp, (False, True, True), "ipp")
    _make_layer(msp, (False, True, False), "ipi")
    _make_layer(msp, (False, False, True), "iip")
    _make_layer(msp, (False, False, False), "iii")

    doc.saveas(data_dir / "poly_open_bulge_orientation.dxf")


def make_dxf_poly_holes():
    doc = ezdxf.new("R2010")
    doc.layers.add(name="poly_hole")
    doc.layers.add(name="poly_multiple_holes")
    doc.layers.add(name="island_in_hole")
    doc.layers.add(name="island_in_hole_backwards")
    doc.layers.add(name="poly_multiple_islands")
    doc.layers.add(name="island_with_hole_in_hole")
    msp = doc.modelspace()

    pts_outer = [
        (0, 0, 0),
        (10, 0, 0),
        (10, 10, 0),
        (0, 10, 0),
    ]
    pts_hole_in_outer = [
        (1, 1, 0),
        (9, 1, 0),
        (9, 9, 0),
        (1, 9, 0),
    ]
    pts_island1 = [
        (2, 2, 0),
        (8, 2, 0),
        (8, 8, 0),
        (2, 8, 0),
    ]
    pts_island1_hole = [
        (3, 3, 0),
        (7, 3, 0),
        (7, 7, 0),
        (3, 7, 0),
    ]
    pts_inner_11 = [
        (4, 4, 0),
        (4.5, 4, 0),
        (4.5, 4.5, 0),
        (4, 4.5, 0),
    ]
    pts_inner_21 = [
        (5.5, 4, 0),
        (6, 4, 0),
        (6, 4.5, 0),
        (5.5, 4.5, 0),
    ]
    pts_inner_12 = [
        (4, 5.5, 0),
        (4.5, 5.5, 0),
        (4.5, 6, 0),
        (4, 6, 0),
    ]
    pts_inner_22 = [
        (5.5, 5.5, 0),
        (6, 5.5, 0),
        (6, 6, 0),
        (5.5, 6, 0),
    ]

    poly1 = msp.add_lwpolyline(
        pts_outer,
        format="xyb",
        dxfattribs={"layer": "poly_hole"},
    )
    poly1.close(True)
    poly1.dxf.const_width = 0
    poly2 = msp.add_lwpolyline(
        pts_hole_in_outer,
        format="xyb",
        dxfattribs={"layer": "poly_hole"},
    )
    poly2.close(True)
    poly2.dxf.const_width = 0

    poly1 = msp.add_lwpolyline(
        pts_outer,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_holes"},
    )
    poly1.close(True)
    poly1.dxf.const_width = 0
    hole11 = msp.add_lwpolyline(
        pts_inner_11,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_holes"},
    )
    hole11.close(True)
    hole11.dxf.const_width = 0
    hole21 = msp.add_lwpolyline(
        pts_inner_21,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_holes"},
    )
    hole21.close(True)
    hole21.dxf.const_width = 0
    hole12 = msp.add_lwpolyline(
        pts_inner_12,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_holes"},
    )
    hole12.close(True)
    hole12.dxf.const_width = 0
    hole22 = msp.add_lwpolyline(
        pts_inner_22,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_holes"},
    )
    hole22.close(True)
    hole22.dxf.const_width = 0

    poly1 = msp.add_lwpolyline(
        pts_outer,
        format="xyb",
        dxfattribs={"layer": "island_in_hole"},
    )
    poly1.close(True)
    poly1.dxf.const_width = 0
    poly2 = msp.add_lwpolyline(
        pts_hole_in_outer,
        format="xyb",
        dxfattribs={"layer": "island_in_hole"},
    )
    poly2.close(True)
    poly2.dxf.const_width = 0
    poly3 = msp.add_lwpolyline(
        pts_island1,
        format="xyb",
        dxfattribs={"layer": "island_in_hole"},
    )
    poly3.close(True)
    poly3.dxf.const_width = 0

    poly3 = msp.add_lwpolyline(
        pts_island1,
        format="xyb",
        dxfattribs={"layer": "island_in_hole_backwards"},
    )
    poly3.close(True)
    poly3.dxf.const_width = 0
    poly2 = msp.add_lwpolyline(
        pts_hole_in_outer,
        format="xyb",
        dxfattribs={"layer": "island_in_hole_backwards"},
    )
    poly2.close(True)
    poly2.dxf.const_width = 0
    poly1 = msp.add_lwpolyline(
        pts_outer,
        format="xyb",
        dxfattribs={"layer": "island_in_hole_backwards"},
    )
    poly1.close(True)
    poly1.dxf.const_width = 0

    poly1 = msp.add_lwpolyline(
        pts_outer,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_islands"},
    )
    poly1.close(True)
    poly1.dxf.const_width = 0
    poly2 = msp.add_lwpolyline(
        pts_hole_in_outer,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_islands"},
    )
    poly2.close(True)
    poly2.dxf.const_width = 0
    """poly3 = msp.add_lwpolyline(
        pts_island1,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_islands"},
    )
    poly3.close(True)
    poly3.dxf.const_width = 0"""
    hole11 = msp.add_lwpolyline(
        pts_inner_11,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_islands"},
    )
    hole11.close(True)
    hole11.dxf.const_width = 0
    hole21 = msp.add_lwpolyline(
        pts_inner_21,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_islands"},
    )
    hole21.close(True)
    hole21.dxf.const_width = 0
    hole12 = msp.add_lwpolyline(
        pts_inner_12,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_islands"},
    )
    hole12.close(True)
    hole12.dxf.const_width = 0
    hole22 = msp.add_lwpolyline(
        pts_inner_22,
        format="xyb",
        dxfattribs={"layer": "poly_multiple_islands"},
    )
    hole22.close(True)
    hole22.dxf.const_width = 0

    poly1 = msp.add_lwpolyline(
        pts_outer,
        format="xyb",
        dxfattribs={"layer": "island_with_hole_in_hole"},
    )
    poly1.close(True)
    poly1.dxf.const_width = 0
    poly2 = msp.add_lwpolyline(
        pts_hole_in_outer,
        format="xyb",
        dxfattribs={"layer": "island_with_hole_in_hole"},
    )
    poly2.close(True)
    poly2.dxf.const_width = 0
    poly3 = msp.add_lwpolyline(
        pts_island1,
        format="xyb",
        dxfattribs={"layer": "island_with_hole_in_hole"},
    )
    poly3.close(True)
    poly3.dxf.const_width = 0
    poly4 = msp.add_lwpolyline(
        pts_island1_hole,
        format="xyb",
        dxfattribs={"layer": "island_with_hole_in_hole"},
    )
    poly4.close(True)
    poly4.dxf.const_width = 0

    doc.saveas(data_dir / "poly_holes.dxf")


if __name__ == "__main__":
    main()
