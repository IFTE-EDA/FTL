from pathlib import Path
import ezdxf

data_dir = Path(__file__).parent


def main():
    make_dxf_layers()
    make_dxf_lines()
    make_dxf_poly_nobulge()
    make_dxf_poly_bulge()
    make_dxf_circle()


def make_dxf_layers():
    doc = ezdxf.new("R2010")
    doc.layers.add("TestLayer1")
    doc.layers.add("TestLayer2")
    doc.layers.add("TestLayer3")
    doc.saveas(data_dir / "layers.dxf")


def make_dxf_lines():
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_line((0, 0), (10, 0))
    msp.add_line((10, 0), (10, 10))
    msp.add_line((10, 10), (0, 10))
    msp.add_line((0, 10), (0, 0))
    doc.saveas(data_dir / "lines.dxf")


def make_dxf_circle():
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_circle(center=(0, 0), radius=5)
    doc.saveas(data_dir / "circle.dxf")


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


if __name__ == "__main__":
    main()
