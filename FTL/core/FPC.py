from __future__ import annotations


class FPC:
    name: str = ""
    layers = []

    def __init__(self, name: str = None):
        if name is not None:
            self.name = name
        self.layers = []


class FPCLayer:
    name = ""
    thickness = 0.0
    material = None

    def __init__(self, name: str, thickness: float, material: Material):
        if name is not None:
            self.name = name
        self.thickness = thickness
        self.material = material


class Material:
    name = ""
    conductivity = 0.0
    dielectric = 0.0
    loss_tangent = 0.0

    def __init__(
        self,
        name: str,
        conductivity: float,
        dielectric: float,
        loss_tangent: float,
    ):
        if name is not None:
            self.name = name
        self.conductivity = conductivity
        self.dielectric = dielectric
        self.loss_tangent = loss_tangent
