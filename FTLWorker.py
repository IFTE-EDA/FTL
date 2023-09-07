from PyQt6 import QtCore
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from MatrixTransformer import *
from Transformation import *
from ZBend import *
from LinearTransformation import *
from FileParser import FileParser
from RenderContainer import *
import subprocess
import os
from pathlib import Path
import shutil
import VMeshTools.VMeshTools as vmt
from PyQt6.QtWidgets import QFileDialog


class FTLWorker(QtCore.QObject):
    def __init__(self, main):
        super().__init__()
        self.main = main
        main.console("FTLWorker created.\n")

    progress = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)
    fileOpened = QtCore.pyqtSignal()
    parsingFinished = QtCore.pyqtSignal()
    visualizationFinished = QtCore.pyqtSignal()
    renderingFinished = QtCore.pyqtSignal()
    updatingFinished = QtCore.pyqtSignal()

    def parseFile(self, file):
        self.status.emit("Opening file...")
        self.progress.emit(0)
        main = self.main
        main.parser = FileParser(file, main.rcFP, main.rcRender, True)
        # main.parser.progress.connect(self.forwardProgress)
        main.parser.progress.connect(self.progress)
        main.parser.status.connect(self.status)
        self.parse(False)
        self.fileOpened.emit()
        print("File opened.")

    def updateModel(self):
        print("(Re)parsing...")
        main = self.main
        main.parser.parse()
        # main.visualize()
        self.status.emit("File parsed successfully.")
        self.progress.emit(100)
        print("(Re)parsed.")

    def parse(self, signal=True):
        print("(Re)parsing...")
        main = self.main
        main.parser.parse()
        main.parser.calculate_assignments()
        main.visualize()
        self.status.emit("File parsed successfully.")
        self.progress.emit(100)
        if signal:
            self.parsingFinished.emit()
        print("(Re)parsed.")

    def visualize(self):
        print("Visualizing...")
        self.main.parser.visualize()
        self.status.emit("View updated.")
        self.progress.emit(100)
        print("Visualisation finished.")
        self.visualizationFinished.emit()
        print("Visualized")

    def render(self):
        print("Rendering...")
        self.main.parser.render()
        self.status.emit("Rendering finished.")
        self.progress.emit(100)
        self.renderingFinished.emit()
        print("Rendered.")

    def updateParser(self):
        print("Updating assignments...")
        self.status.emit("Transformations updated.")
        self.progress.emit(100)
        self.updatingFinished.emit()
        print("Assignments updated.")

    def exportFile_VMAP(self, filename: str):
        meshes = self.main.parser.transformer.getTransformedMeshList()
        print("Filename:", filename)
        vmap = vmt.VMAPFileHandler(filename)
        for i, (name, mesh) in enumerate(meshes.items()):
            print(name)
            grp = vmt.VMAPMeshGroup(vmap, "/VMAP/GEOMETRY/" + str(i + 1))
            grp.writeMesh_vedo(mesh, name)
        print("VMAP export done.")
        # v.show(meshes["PCB"], meshes["Copper"])
        # v.show(v.Points(meshes["PCB"].points()))

    def exportFile_STL(self, filename_f: str):
        if "{}" not in filename_f:
            raise Exception(
                "Filename does not contain formatting brackets:", filename_f
            )
        meshes = self.main.parser.transformer.getTransformedMeshList()
        for i, (name, mesh) in enumerate(meshes.items()):
            filename = filename_f.format(name)
            print("Exporting '{}'...".format(filename))
            mesh.write(filename)
        print("STL export done.")

    def importKiCAD(self, filename: str):
        if not os.path.isfile(filename):
            raise Exception("File not found:", filename)
        self.status.emit("Converting KiCAD file...")
        self.progress.emit(10)
        subprocess.call(["python", "kicad2STL.py", filename])
        self.status.emit("Preparing project file...")
        self.progress.emit(60)
        savefile, _ = QFileDialog.getSaveFileName(
            self.main,
            "Save project file",
            filter="*.json",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        projName = Path(savefile).stem
        projDir = Path(savefile).parent
        boardFilename = projName + "_board.stl"
        coppersFilename = projName + "_coppers.stl"

        if not savefile.endswith(".json"):
            savefile = str(projDir) + "/" + projName + ".json"
        # shutil.copy2("_template_.json", savefile)
        print(
            "Saving to project '{}' in directory {}".format(projName, projDir)
        )

        search = ["{BOARDFILE}", "{COPPERFILE}"]
        replace = [boardFilename, coppersFilename]

        shutil.move("STL/board_solid.stl", str(projDir) + "/" + boardFilename)
        shutil.move(
            "STL/coppers_fuse.stl", str(projDir) + "/" + coppersFilename
        )

        with open("_template_.json", "r") as file:
            data = file.read()
            for i, token in enumerate(search):
                data = data.replace(token, replace[i])
        with open(savefile, "w") as file:
            file.write(data)
        self.main.open_file(savefile)
        self.status.emit("File imported.")
        self.progress.emit(0)
