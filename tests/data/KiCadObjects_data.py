LAYER_PARAMS_TEST = ["Test Layer", "layer type", "Long Layer Name"]

"""PARAMS_MULTILAYER = {
    "start": [0, 0],
    "end": [100, 100],
    "stroke": {
        "width": 0.2,
        "type": "default"
    },
    "fill": "solid",
    "layers": [
        "Testlayer1",
        "Testlayer2",
        "Testlayer3",
    ],
    "tstamp": "TSTAMPTEST",
}"""

PARAMS_LINE = {
    "start": [0, 0],
    "end": [100, 100],
    "stroke": {"width": 0.2, "type": "default"},
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_RECT = {
    "start": [0, 0],
    "end": [100, 100],
    "stroke": {"width": 0, "type": "default"},
    "fill": "solid",
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_RECT_WIDTH = {
    "start": [0, 0],
    "end": [100, 100],
    "stroke": {"width": 0.2, "type": "default"},
    "fill": "solid",
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_ARC = {
    "start": [-50, 0],
    "mid": [0, 50],
    "end": [50, 0],
    "stroke": {"width": 0.2, "type": "solid"},
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_POLYGON = {
    "pts": {
        "xy": [
            [0, 0],
            [0, 100],
            [100, 100],
            [100, 0],
            [0, 0],
        ]
    },
    "stroke": {"width": 0.2, "type": "default"},
    "width": 0.2,
    "fill": "no",
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_POLYGON_CCW = {
    "pts": {
        "xy": [
            [0, 0],
            [100, 0],
            [100, 100],
            [0, 100],
        ]
    },
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_ZONE = {
    "net": 0,
    "net_name": "MyNetName",
    "hatch": "solid",
    "connect_pads": "no",
    "min_thickness": 0.2,
    "polygon": {
        "pts": {
            "xy": [
                [0, 0],
                [100, 0],
                [100, 100],
                [0, 100],
            ]
        },
    },
    "filled_polygon": [
        {
            "pts": {
                "xy": [
                    [0, 0],
                    [100, 0],
                    [100, 100],
                    [0, 100],
                ]
            },
        }
    ],
    "fill": "solid",
    "layer": "Testlayer",
    "tstamp": "TSTAMPTEST",
}

PARAMS_VIA = {
    "at": [0, 0],
    "size": [3],
    "drill": [1],
    "layers": ["F.Cu", "B.Cu"],
    "net": [2],
}

PARAMS_PAD_ROUNDRECT = {
    0: "1",
    1: "smd",
    2: "roundrect",
    "at": [-30, 0],
    "size": [10, 14],
    "layers": ["*.Cu"],
    "roundrect_rratio": 0.25,
    "net": [0, "GND"],
}

PARAMS_PAD_ROUNDRECT_DRILLED = {
    0: "1",
    1: "thru_hole",
    2: "roundrect",
    "at": [-30, 0],
    "size": [10, 14],
    "drill": [1],
    "layers": ["*.Cu"],
    "roundrect_rratio": 0.25,
    "net": [0, "GND"],
}

PARAMS_PAD_ROUNDRECT_DRILLED_2 = (
    {
        0: "1",
        1: "thru_hole",
        2: "roundrect",
        "at": [-30, 0],
        "size": [10, 14],
        "drill": [1],
        "layers": ["Testlayer1", "Testlayer2"],
        "roundrect_rratio": 0.25,
        "net": [0, "GND"],
    },
)

PARAMS_PART = {
    0: "TestPart",
    # "ref": "U1",
    "descr": "TestDescription",
    "tags": ["TestTag1", "TestTag2"],
    "layer": "Testlayer",
    "path": "TestPath",
    "at": [0, 0, 0],
    "pads": [
        {
            0: "1",
            1: "smd",
            2: "roundrect",
            "at": [-30, 0],
            "size": [10, 14],
            "layers": ["F.*"],
            "roundrect_rratio": 0.25,
            "net": [0, "GND"],
        },
        {
            0: "2",
            1: "smd",
            2: "roundrect",
            "at": [-30, 0],
            "size": [10, 14],
            "layers": ["B.*"],
            "roundrect_rratio": 0.25,
            "net": [0, "GND"],
        },
    ],
    "property": [
        [
            '"Reference"',
            "T1",
        ]
    ],
    "footprint": "TestFootprint",
    "datasheet": "TestDatasheet",
    "tstamp": "TSTAMPTEST",
}

PARAMS_PART_DRILLED_PADS = {
    0: "TestPart",
    # "ref": "U1",
    "descr": "TestDescription",
    "tags": ["TestTag1", "TestTag2"],
    "layer": "Testlayer",
    "path": "TestPath",
    "at": [0, 0, 0],
    "pads": [
        {
            0: "1",
            1: "thru_hole",
            2: "oval",
            "at": [-30, 0],
            "size": [1.7, 1.7],
            "drill": [1],
            "layers": ["F.Cu", "B.Cu"],
            "roundrect_rratio": 0.25,
            "net": [0, "GND"],
        },
        {
            0: "2",
            1: "thru_hole",
            2: "oval",
            "at": [-30, 0],
            "size": [1.7, 1.7],
            "drill": [1],
            "layers": ["F.Cu", "B.Cu"],
            "roundrect_rratio": 0.25,
            "net": [0, "GND"],
        },
    ],
    "property": [
        [
            '"Reference"',
            "T1",
        ]
    ],
    "footprint": "TestFootprint",
    "datasheet": "TestDatasheet",
    "tstamp": "TSTAMPTEST",
}
