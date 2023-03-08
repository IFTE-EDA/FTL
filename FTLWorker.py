from PyQt6 import QtCore
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from MatrixTransformer import *
from Transformation import *
from ZBend import *
from LinearTransformation import *
from FileParser import FileParser
from RenderContainer import *


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
        #main.resetView()

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
        self.main.parser.calculate_assignments()
        self.status.emit("Transformations updated.")
        self.progress.emit(100)
        self.updatingFinished.emit()
        print("Assignments updated.")
