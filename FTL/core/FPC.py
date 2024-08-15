# container class for FPC object

from __future__ import annotations


class FPC:
    """Flexible Printed Circuit container class."""

    name: str = ""
    stackup: list[FPCLayer] = []

    def __init__(self, name: str = None):
        if name is not None:
            self.name = name
        self.stackup = []


class FPCLayer:
    """FPC Layer class."""

    name = "Unnamed Layer"
    z = 0.0
    thickness = 0.0
    material = None

    def __init__(
        self, name: str, thickness: float = 0, material: Material = None
    ):
        if name is not None:
            self.name = name
        self.thickness = thickness
        self.material = material


class Material:
    """Material class for FPCLayer."""

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
