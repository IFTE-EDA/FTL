#from pathlib import Path
#import sys
#import os

# sys.path.append("../FTL")
#sys.path.append(os.path.abspath(os.getcwd()))
from FTL.core.FPC import FPC


class Test_FPC:
    def setup_class(self):
        pass

    # @pytest.mark.skip
    def test_fpc_default_empty_name(self):
        fpc = FPC()
        assert fpc.name == ""

    def test_fpc_name(self):
        fpc = FPC("MyFPC")
        assert fpc.name == "MyFPC"
