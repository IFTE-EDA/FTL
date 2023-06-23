import os
import json
from PyQt6 import uic
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QApplication, QMainWindow, QDialog, QListWidgetItem, QFileDialog, QMessageBox


class FTLPreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('preferences.ui', self)

        self.pbFCPath.pressed.connect(self.chooseFC)
        self.buttonBox.accepted.connect(self.save)

        with open("preferences.json") as f:
            self.prefs = json.load(f)
        if not self.prefs:
            mb = QMessageBox(self)
            mb.setWindowTitle("No preference found")
            mb.setText("'preferences.json' not found")
            button = mb.exec()
            raise Exception("'preferences.json' not found")

        self.leFCPath.setText(self.prefs["freecadPath"])

    def chooseFC(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Path to FreeCADCmd.exe", "", filter="*.exe",
                                                  options=QFileDialog.Option.DontUseNativeDialog)
        if filename == "":
            return False
        if not os.path.isfile(filename) or not filename.endswith(".exe"):
            mb = QMessageBox(self)
            mb.setWindowTitle("File not found")
            mb.setText("File not found or is not a FreeCAD executable: " + filename)
            mb.exec()
        self.leFCPath.setText(filename)
        self.prefs["freecadPath"] = filename

    def save(self):
        json_object = json.dumps(self.prefs, indent=4)
        with open("preferences.json", "w") as outfile:
            outfile.write(json_object)
            print("Preferences saved successfully.")