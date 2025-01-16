from pathlib import Path
import ezdxf

data_dir = Path(__file__).parent

sub_l = 50000
sub_w = 10000
trace_w = 150
trace_l = 50000


def main():
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    doc.layers.add(name="sub")
    doc.layers.add(name="top_metal")
    doc.layers.add(name="bot_metal")

    polyline_trace = [
        (-trace_l / 2, -trace_w / 2),
        (-trace_l / 2, trace_w / 2),
        (trace_l / 2, trace_w / 2),
        (trace_l / 2, -trace_w / 2),
    ]
    polyline_sub = [
        (-sub_l / 2, -sub_w / 2),
        (-sub_l / 2, sub_w / 2),
        (sub_l / 2, sub_w / 2),
        (sub_l / 2, -sub_w / 2),
    ]
    trace = msp.add_lwpolyline(
        polyline_trace, dxfattribs={"layer": "top_metal"}
    )
    trace.close(True)
    trace.dxf.const_width = 0
    sub = msp.add_lwpolyline(polyline_sub, dxfattribs={"layer": "sub"})
    sub.close(True)
    sub.dxf.const_width = 0
    gnd = msp.add_lwpolyline(polyline_sub, dxfattribs={"layer": "bot_metal"})
    gnd.close(True)
    gnd.dxf.const_width = 0

    filename = data_dir.name + ".dxf"
    doc.saveas(data_dir / filename)


if __name__ == "__main__":
    main()
