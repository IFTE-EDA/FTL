# test_FPCLayer.py
import pytest
from FTL.core.FPC import FPCLayer, Material


class Test_FPCLayer:
    def setup_class(self):
        pass

    def test_fpclayer_default_empty_name(self):
        material = Material("Copper", 5.8e7, 1.0, 0.0)
        layer = FPCLayer(None, 0.001, material)
        assert layer.name == "Unnamed Layer"

    def test_fpclayer_name(self):
        material = Material("Copper", 5.8e7, 1.0, 0.0)
        layer = FPCLayer("MyLayer", 0.001, material)
        assert layer.name == "MyLayer"

    def test_fpclayer_thickness(self):
        material = Material("Copper", 5.8e7, 1.0, 0.0)
        layer = FPCLayer("MyLayer", 0.001, material)
        assert layer.thickness == 0.001

    def test_fpclayer_material(self):
        material = Material("Copper", 5.8e7, 1.0, 0.0)
        layer = FPCLayer("MyLayer", 0.001, material)
        assert layer.material == material

    def test_fpclayer_material_name(self):
        material = Material("Copper", 5.8e7, 1.0, 0.0)
        layer = FPCLayer("MyLayer", 0.001, material)
        assert layer.material.name == "Copper"

    def test_fpclayer_material_conductivity(self):
        material = Material("Copper", 5.8e7, 1.0, 0.0)
        layer = FPCLayer("MyLayer", 0.001, material)
        assert layer.material.conductivity == 5.8e7

    def test_fpclayer_material_dielectric(self):
        material = Material("Copper", 5.8e7, 1.0, 0.0)
        layer = FPCLayer("MyLayer", 0.001, material)
        assert layer.material.dielectric == 1.0
