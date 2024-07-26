# from pathlib import Path
# import sys
# import os

# sys.path.append("../FTL")
# sys.path.append(os.path.abspath(os.getcwd()))
from FTL.core.FPC import FPC, Material, FPCLayer


class Test_FPC:
    def setup_class(self):
        self.copper = Material("Copper", 5.8e7, 1.0, 0.0)
        self.PI = Material("PI", 0.0, 3.0, 0.1)

    # @pytest.mark.skip
    def test_fpc_default_empty_name(self):
        fpc = FPC()
        assert fpc.name == ""

    def test_fpc_name(self):
        fpc = FPC("MyFPC")
        assert fpc.name == "MyFPC"

    def test_fpc_layers_default_empty(self):
        fpc = FPC("MyFPC")
        assert fpc.layers == []

    def test_fpc_layers(self):
        fpc = FPC("MyFPC")
        layer1 = FPCLayer("Layer1", 0.035, self.copper)
        layer2 = FPCLayer("Layer2", 0.100, self.PI)
        layer3 = FPCLayer("Layer3", 0.035, self.copper)
        fpc.layers = [layer1, layer2, layer3]
        assert fpc.layers == [layer1, layer2, layer3]
