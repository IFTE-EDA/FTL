from FTL.core.FPC import Material


class Test_Material:
    def setup_class(self):
        pass

    def test_material_default_empty_name(self):
        material = Material(None, 0.0, 0.0, 0.0)
        assert material.name == ""

    def test_material_name(self):
        material = Material("Copper", 0.0, 0.0, 0.0)
        assert material.name == "Copper"

    def test_material_conductivity(self):
        material = Material("Copper", 5.8e7, 0.0, 0.0)
        assert material.conductivity == 5.8e7

    def test_material_dielectric(self):
        material = Material("Copper", 0.0, 1.0, 0.0)
        assert material.dielectric == 1.0

    def test_material_loss_tangent(self):
        material = Material("Copper", 0.0, 0.0, 0.1)
        assert material.loss_tangent == 0.1
