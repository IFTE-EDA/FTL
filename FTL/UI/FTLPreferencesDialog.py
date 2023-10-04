import os
import json
from PyQt6 import uic
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QMainWindow,
    QDialog,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
)
import FTL
from FTL.Util.FTLKiCAD import KiCADPathManager


class FTLPreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(FTL.get_uic("preferences"), self)

        self.pbFCPath.pressed.connect(self.chooseFC)
        self.pbKCPath.pressed.connect(self.chooseKC)
        self.pbKCUPath.pressed.connect(self.chooseKCU)
        self.buttonBox.accepted.connect(self.save)

        with open(FTL.get_data("preferences.json")) as f:
            self.prefs = json.load(f)
        if not self.prefs:
            mb = QMessageBox(self)
            mb.setWindowTitle("No preference found")
            mb.setText("'preferences.json' not found")
            button = mb.exec()
            print(button)
            raise Exception("'preferences.json' not found")

        self.leFCPath.setText(self.prefs["freecadPath"])
        self.leKCPath.setText(self.prefs["kicadPath"])
        self.leKCUPath.setText(self.prefs["kicadUserPath"])

        kicadMgr = KiCADPathManager(self.prefs["kicadUserPath"])
        print(kicadMgr.paths)
        print(
            kicadMgr.resolvePath(
                "${ESPRESSIF_3D_MODELS}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x03_P2.54mm_Vertical.wrl"
            )
        )

    def chooseFC(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Path to FreeCADCmd.exe",
            "",
            filter="*.exe",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if filename == "":
            return False
        if not os.path.isfile(filename) or not filename.endswith(".exe"):
            mb = QMessageBox(self)
            mb.setWindowTitle("File not found")
            mb.setText(
                "File not found or is not a FreeCAD executable: " + filename
            )
            mb.exec()
        self.leFCPath.setText(filename)
        self.prefs["freecadPath"] = filename

    def chooseKC(self):
        filename = QFileDialog.getExistingDirectory(
            self,
            "KiCAD base directory",
            "",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if filename == "":
            return False
        if not os.path.isdir(filename):
            mb = QMessageBox(self)
            mb.setWindowTitle("Path invalid")
            mb.setText(
                "Directory not found or is not a KiCAD base directory: "
                + filename
            )
            mb.exec()
        self.leKCPath.setText(filename)
        self.prefs["kicadPath"] = filename

    def chooseKCU(self):
        filename = QFileDialog.getExistingDirectory(
            self,
            "KiCAD user directory",
            "",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if filename == "":
            return False
        if not os.path.isdir(filename):
            mb = QMessageBox(self)
            mb.setWindowTitle("Path invalid")
            mb.setText(
                "Directory not found or is not a KiCAD user directory: "
                + filename
            )
            mb.exec()
        self.leKCUPath.setText(filename)
        self.prefs["kicadUserPath"] = filename

    def save(self):
        json_object = json.dumps(self.prefs, indent=4)
        with open("preferences.json", "w") as outfile:
            outfile.write(json_object)
            print("Preferences saved successfully.")
