import sys
import os

# sys.path.append("../FTL")
sys.path.append(os.path.abspath(os.getcwd()))
from FTL.Util.FTLKiCAD import KiCADPathManager
import os


class Test_KiCADPathManager:
    def setup_class(self):
        self.pathMgr = KiCADPathManager("data")

    def test_workin_dir(self):
        assert (
            str(self.pathMgr.getWorkingDir())
            == "C:\\Program Files\\KiCad\\7.0"
        )

    def test_paths(self):
        assert str(self.pathMgr.paths) == str(
            {
                "ESPRESSIF_3D_MODELS": "C:\\Program Files\\KiCad\\7.0\\share\\kicad\\3dmodels\\Espressif.3dshapes",
                "SNAPEDA_3D": "C:\\Users\\USER\\SnapEDA Kicad Plugin\\KiCad Library\\SnapEDA 3D Models",
            }
        )

    def test_getPath(self):
        assert (
            str(self.pathMgr.getPath("ESPRESSIF_3D_MODELS"))
            == "C:\\Program Files\\KiCad\\7.0\\share\\kicad\\3dmodels\\Espressif.3dshapes"
        )
        assert (
            str(self.pathMgr.getPath("SNAPEDA_3D"))
            == "C:\\Users\\USER\\SnapEDA Kicad Plugin\\KiCad Library\\SnapEDA 3D Models"
        )
        try:
            self.pathMgr.getPath("NOT_EXISTING")
            assert False
        except IndexError:
            assert True
