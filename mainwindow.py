import json
import time
import os.path
# This Python file uses the following encoding: utf-8
import sys
from PyQt6 import uic
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QFileDialog, QStyle, QTreeWidgetItem
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6 import QtGui
# from PyQt6 import Qt
import sys
import PyQt6

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
# from vedo import Mesh, dataurl, Plotter
import vedo as v

from MatrixTransformer import *
from Transformation import *
from ZBend import *
from LinearTransformation import *
from FileParser import FileParser
from RenderContainer import *
from FTLWorker import *

global MODE_GUI
MODE_GUI = True


class port:
    def __init__(self, view, parent):
        self.view = view
        self.parent = parent
        self.scroll = view.verticalScrollBar()
        self.f = open("log.txt", "w")

    def write(self, *args):
        self.view.insertPlainText(*args)
        self.f.write(*args)
        self.f.flush()
        if (self.parent.autoscroll):
            self.scroll.setValue(self.scroll.maximum())

    def flush(self):
        pass


# from PySide6.QtWidgets import QApplication, QMainWindow

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
# from ui_form import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.ui = Ui_MainWindow()
        # self.ui.setupUi(self)
        self.current_model_item = None
        self.projectFilename = None
        self.twiModel_layers = None
        self.layers_render_debug = None
        self.layers_render_layers = None
        self.layers_floorplan_debug = None
        self.layers_floorplan_transformations = None
        self.layers_floorplan_layers = None
        self.docName = None
        self.layers_fp = None
        self.layers_render = None
        self.twiModel_Transformations = None
        self.layers_render_transformations = None
        self.wModel = None
        self.wParams = None
        self.wConsole = None
        self.wGrafTab = None
        self.wLayers = None
        uic.loadUi('form.ui', self)
        self.worker = FTLWorker(self)
        self.parser = None
        self.autoscroll = True

    def initUi(self):
        self.layers_fp = []
        self.layers_render = []

        """btn_icons = [   (self.actionFileNew, "SP_FileIcon"),
                        (self.actionFileOpen, "SP_DirIcon"),
                        (self.actionFileRecent, "SP_DirIcon"),
                        (self.actionFileSave, "SP_DialogSaveButton"),
                        (self.actionFileSave_as, "SP_DialogSaveButton"),
                        (self.actionFileExport, "SP_ArrowForward"),
                        (self.actionFileQuit, "SP_BrowserStop"),
                        (self.actionEditAdd_mesh_layer, "SP_MediaPlay"),
                        (self.actionEditAdd_transformation, "SP_MediaPlay"),
                        (self.actionToolsFreeCAD, "SP_TitleBarMenuButton"),
                        (self.actionToolsKiCAD, "SP_TitleBarMenuButton"),
                        (self.actionHelpAbout, "SP_MessageBoxQuestion"),
                        (self.actionHelpDocumentation, "SP_MessageBoxQuestion"),
                        (self.actionReset_View, "SP_DialogOkButton"),
                        (self.actionRender, "SP_DialogHelpButton"),
                        (self.bConsClear, "SP_BrowserStop"),
                        (self.bConsAutoscroll, "SP_ArrowDown"),
                        (self.bConsC, "SP_DialogSaveButton")]"""
        btn_icons = [(self.actionFileNew, "document-new"),
                     (self.actionFileOpen, "document-open"),
                     (self.actionFileRecent, "document-open"),
                     (self.actionFileSave, "document-save"),
                     (self.actionFileSave_as, "document-save-as"),
                     (self.actionFileExport, "document-export"),
                     (self.actionFileQuit, "window-close"),
                     (self.actionEditAdd_mesh_layer, "cursor-cross"),
                     (self.actionEditAdd_transformation, "cursor-cross"),
                     (self.actionToolsFreeCAD, "freecad.png"),
                     (self.actionToolsKiCAD, "kicadlogo.png"),
                     (self.actionHelpAbout, "help-about"),
                     (self.actionHelpDocumentation, "help-whatsthis"),
                     (self.actionReset_View, "zoom-fit-best"),
                     (self.actionRender, "run-build-install-root"),
                     (self.actionUpdate_Footprint, "run-build-configure"),
                     (self.bConsClear, "edit-clear-history"),
                     (self.bConsAutoscroll, "gnumeric-format-valign-bottom"),
                     (self.bConsC, "edit-copy")]
        tbActions = [self.actionFileNew,
                     self.actionFileOpen,
                     # self.actionFileRecent,
                     self.actionFileSave,
                     # self.actionFileSave_as,
                     # self.actionFileExport,
                     self.actionFileQuit,
                     self.actionEditAdd_mesh_layer,
                     # self.actionEditAdd_transformation,
                     self.actionToolsFreeCAD,
                     self.actionToolsKiCAD,
                     self.actionReset_View,
                     self.actionUpdate_Footprint,
                     self.actionRender
                     # self.actionToolsKiCAD
                     ]
        for item, name in btn_icons:
            if name.startswith("SP_"):
                pixmapi = getattr(QStyle.StandardPixmap, name)
                icon = self.style().standardIcon(pixmapi)
                item.setIcon(icon)
            elif "." in name:
                icon = QtGui.QIcon("icons/" + name)
                item.setIcon(icon)
            else:
                icon = QtGui.QIcon("icons/" + name + ".svg")
                item.setIcon(icon)
            # if type(item) == QtGui.QAction:
            #    self.tbMain.addAction(item)
        for action in tbActions:
            self.tbMain.addAction(action)

        self.wMainProgressBar = QtWidgets.QProgressBar()
        self.wStepProgressBar = QtWidgets.QProgressBar()

        self.statusBar().addPermanentWidget(self.wMainProgressBar)
        # self.statusBar().addPermanentWidget(self.wStepProgressBar)
        self.wMainProgressBar.setGeometry(30, 20, 200, 25)
        self.wMainProgressBar.setValue(10)
        self.wStepProgressBar.setGeometry(30, 20, 200, 25)
        self.wStepProgressBar.setValue(10)

        self.bConsClear.setText("")
        self.bConsAutoscroll.setText("")
        self.bConsAutoscroll.setChecked(True)
        self.bConsC.setText("")

        """
        #############################
        #####   SIGNALS/SLOTS   #####
        #############################
        """

        self.actionFileQuit.triggered.connect(self.close)
        self.actionFileNew.triggered.connect(self.new_file)
        self.actionFileOpen.triggered.connect(self.openFileDialog)
        self.actionFileSave.triggered.connect(self.saveFileDialog)
        self.actionFileSave_as.triggered.connect(self.saveAsFileDialog)
        self.actionReset_View.triggered.connect(self.resetView)
        # self.actionReset_View.triggered.connect(self.resetView)
        self.actionUpdate_Footprint.triggered.connect(self.worker.parse)
        self.actionRender.triggered.connect(self.render_bent)

        self.wModel.clicked.connect(self.modelItemClicked)
        self.wParams.cellChanged.connect(self.modelParameterChanged)

        self.wGrafTab.currentChanged.connect(self.onTabChange)

        self.wLayers.itemChanged[QTreeWidgetItem, int].connect(self.layerItemChanged)

        self.bConsAutoscroll.clicked.connect(self.set_console_autoscroll)

        ###     WORKER COMMUNICATION
        self.sig_parseFile.connect(self.worker.parseFile)
        self.sig_render.connect(self.worker.render)
        self.sig_visualize.connect(self.worker.visualize)
        self.sig_updateParser.connect(self.worker.updateParser)
        # self.worker.parsingFinished.connect(self.fileParsed)
        self.worker.fileOpened.connect(self.fileParsed)
        self.worker.parsingFinished.connect(self.update_layers)
        self.worker.status.connect(self.set_status)
        self.worker.progress.connect(self.set_main_progress)
        # self.worker.updatingFinished.connect(self.sig_visualize)
        self.worker.renderingFinished.connect(self.fpcRendered)
        self.worker.visualizationFinished.connect(self.update_layer_visibilities)
        # self.worker.visualizationFinished.connect(self.update_layers)


        # actionFileOpen.triggered.connect(self.new_file)

        self.console("Starting... ")

        self.wParams.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.wModel.setHeaderLabels(["Model"])
        self.wLayers.setHeaderLabels(["Visibility"])

        self.FPWidget = QVTKRenderWindowInteractor(self)
        self.wFPLayout.addWidget(self.FPWidget)
        self.FPPlt = v.Plotter(qt_widget=self.FPWidget, axes=1, interactive=False)
        self.FPPlt.parallel_projection(True)

        self.renderWidget = QVTKRenderWindowInteractor(self)
        self.wRenderLayout.addWidget(self.renderWidget)
        self.renderPlt = v.Plotter(qt_widget=self.renderWidget, axes=1)

        self.rcFP = RenderContainer(self.FPPlt)
        self.rcRender = RenderContainer(self.renderPlt)

        # sys.stdout = port(self.wConsole, self)

        if len(sys.argv) > 1:
            self.console("Got file argument from console")
            self.open_file(sys.argv[1])

        """
        se lf.wLayers
        for i in range(3):
            parent = QtWidgets.QTreeWidgetItem(tree)
            parent.setText(0, "Parent {}".format(i))
            #parent.setFlags(parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            #arent.setFlags(parent.flags() |  Qt.ItemIsUserCheckable)
            #parent.setCheckable(True)
            for x in range(5):
                child = QtWidgets.QTreeWidgetItem(parent)
                #child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setText(0, "Child {}".format(x))
                #child.setCheckable(True)
                child.setCheckState(0, Qt.CheckState.Unchecked)
        """

    """#####################################
    #######  SIGNAL/SLOT DEFINITIONS  ######
    #####################################"""

    sig_parseFile = QtCore.pyqtSignal(str)
    sig_visualize = QtCore.pyqtSignal()
    sig_render = QtCore.pyqtSignal()
    sig_updateParser = QtCore.pyqtSignal()

    def openFileDialog(self):
        file, _ = QFileDialog.getOpenFileName(self, "Pick a FTL file", "LTest_hook.json", filter="*.json",
                                              options=QFileDialog.Option.DontUseNativeDialog)
        self.open_file(file)

    def saveFileDialog(self):
        if self.docName is None:
            file, _ = QFileDialog.getSaveFileName(self, "Save file", filter="*.json",
                                                  options=QFileDialog.Option.DontUseNativeDialog)
            if not len(file):
                print("Saving aborted.")
                return
        else:
            file = self.docName
        self.save_file(file)

    def saveAsFileDialog(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save file", filter="*.json",
                                              options=QFileDialog.Option.DontUseNativeDialog)
        if len(file):
            self.save_file(file)
        else:
            print("Saving aborted.")

    def modelItemClicked(self, item):
        self.wParams.blockSignals(True)
        if item.parent().row() == -1:
            return
        # debug("Item clicked: {} in row {} with data <{}>".format(item, item.row(), item.data()))
        parent = item.parent()
        if parent.data() == "Layers":
            self.load_model_params(self.parser.j_layers[item.row()])
            self.current_model_item = self.parser.j_layers[item.row()]
        elif parent.data() == "Transformations":
            self.load_model_params(self.parser.j_transformations[item.row()])
            self.current_model_item = self.parser.j_transformations[item.row()]
            # debug("Transformation {} clicked".format(item.row()))
        else:
            raise Exception("Unknown layer type: {}".format(parent.data()))
        self.wParams.blockSignals(False)

    def resetView(self, renderonly=False):
        print("Resetting view")
        if not renderonly:
            self.rcFP.plotter.reset_camera()
            self.rcFP.plotter.look_at("xy")
            # self.rcFP.plotter.fly_to((0, 0, 50))
            self.rcRender.plotter.reset_camera()
            self.rcRender.plotter.look_at("xy")
        self.update_layer_visibilities()
        self.rcFP.render()
        self.rcRender.render()

    def update_layer_visibilities(self):
        print("Updating Layer visibilities")
        parents = []
        for parent in self.layers_fp:
            parents.append(parent)
            # print(parent.text(0))
            for j in range(parent.childCount()):
                child = parent.child(j)
                # print(child.text(0))
                # self.
                checked = child.checkState(0) == Qt.CheckState.Checked
                # print("->{}:{}".format(child.text(0), checked))
                if parent.text(0) == "Layers":
                    self.rcFP.set_item_visibility(ItemType.Layer, child.text(0), checked)
                elif parent.text(0) == "Transformations":
                    self.rcFP.set_item_visibility(ItemType.Transformation, child.text(0), checked)
                elif parent.text(0) == "Debug":
                    self.rcFP.set_item_visibility(ItemType.Debug, child.text(0), checked)
                else:
                    raise Exception("Unknown container type: {}".format(parent.text(0)))
        for parent in self.layers_render:
            parents.append(parent)
            # print(parent.text(0))
            for j in range(parent.childCount()):
                child = parent.child(j)
                # print(child.text(0))
                # self.
                checked = child.checkState(0) == Qt.CheckState.Checked
                # print("->{}:{}".format(child.text(0), checked))
                if parent.text(0) == "Layers":
                    self.rcRender.set_item_visibility(ItemType.Layer, child.text(0), checked)
                elif parent.text(0) == "Transformations":
                    self.rcRender.set_item_visibility(ItemType.Transformation, child.text(0), checked)
                elif parent.text(0) == "Debug":
                    self.rcRender.set_item_visibility(ItemType.Debug, child.text(0), checked)
                else:
                    raise Exception("Unknown container type: {}".format(parent.text(0)))

        # self.rcFP.plotter.
        print("Layer vis updated.")

    def modelParameterChanged(self, row, col):
        debug("item changed at {}/{}".format(row, col))
        label = self.wParams.item(row, 0).text()
        val = self.wParams.item(row, 1).text()
        debug("{} = {}".format(label, val))
        # debug (self.wModel.selectedItem().text(0))
        self.current_model_item[label] = val
        # TODO implement isInteger() and auto-conversion
        # self.parser.transformer.visualize()
        # self.update_parser()
        self.worker.updateModel()
        self.visualize()
        self.rcFP.render()
        # self.update_layer_visibilities()
        """
        if name == "Layers":
            self.rcFP.set_container_visibility(ItemType.Layer, checked)
        elif name == "Transformations":
            self.rcFP.set_container_visibility(ItemType.Transformation, checked)
        elif name == "Debug":
            self.rcFP.set_container_visibility(ItemType.Debug, checked)
        else:
            raise Exception("Unknown container type.")
        self.rcFP.render()


        for i in range(self.wLayers.topLevelItemCount()):
            parent = self.wLayers.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                #print(child.text(0))
                self.
        """

        self.rcFP.render()

    def onTabChange(self, i):
        if i == 0:  # "Floorplan" tab
            for branch in self.layers_render:
                branch.setHidden(True)
            for branch in self.layers_fp:
                branch.setHidden(False)
        elif i == 1:  # "Floorplan" tab
            for branch in self.layers_render:
                branch.setHidden(False)
            for branch in self.layers_fp:
                branch.setHidden(True)
        else:
            raise Exception("Error: Tab {} not found".format(i))

    def layerItemChanged(self, item, column, update=True):
        self.update_layer_visibilities()
        parent = item.parent()
        checked = item.checkState(column) == Qt.CheckState.Checked
        # print("Item changed to {}: {}/{}:     {}".format(checked, column, parent, item))
        if parent is None:
            # top layer item
            name = item.text(0)
            # print("Parent element clicked")
            if self.wGrafTab.currentIndex() == 0:
                # "Floorplan" Tab
                if name == "Layers":
                    self.rcFP.set_container_visibility(ItemType.Layer, checked)
                elif name == "Transformations":
                    self.rcFP.set_container_visibility(ItemType.Transformation, checked)
                elif name == "Debug":
                    self.rcFP.set_container_visibility(ItemType.Debug, checked)
                else:
                    raise Exception("Unknown container type.")
                if update:
                    self.rcFP.render()
            elif self.wGrafTab.currentIndex() == 1:
                # "Render" Tab
                if name == "Layers":
                    self.rcRender.set_container_visibility(ItemType.Layer, checked)
                elif name == "Transformations":
                    self.rcRender.set_container_visibility(ItemType.Transformation, checked)
                elif name == "Debug":
                    self.rcRender.set_container_visibility(ItemType.Debug, checked)
                else:
                    raise Exception("Unknown container type.")
                if update:
                    self.rcRender.render()
            else:
                raise Exception("Tab {} not found.".format(self.wGrafTab.currentIndex()))
            return
        else:
            # inner layer item; first get parent type
            cName = parent.text(0)
            if cName == "Layers":
                container = ItemType.Layer
            elif cName == "Transformations":
                container = ItemType.Transformation
            elif cName == "Debug":
                container = ItemType.Debug
            else:
                raise Exception("Unknown container type.")
            if self.wGrafTab.currentIndex() == 0:
                # print("Changing footprint Layer vis")
                self.rcFP.set_item_visibility(container, item.text(0), checked)
                if update:
                    self.rcFP.render()
            elif self.wGrafTab.currentIndex() == 1:
                # print("Changing render Layer vis")
                self.rcRender.set_item_visibility(container, item.text(0), checked)
                if update:
                    self.rcRender.render()
            else:
                raise Exception("Tab {} not found.".format(self.wGrafTab.currentIndex()))

    """##################################
    #######  STRUCTURAL FUNCTIONS  ######
    ##################################"""

    def save_model_data(self):
        for i in range(self.wModel.columnCount()):
            label = self.wModel.itemAt(i, 0)
            val = self.wModel.itemAt(i, 1)
            debug("{} = {}".format(label, val))
            # TODO really save file

    def console(self, msg):
        # self.wConsole.append(msg)
        self.wConsole.insertPlainText(msg + "\n")

    def set_progress(self, mainProg, stepProg):
        self.wMainProgressBar.setValue(mainProg)
        self.wStepProgressBar.setValue(stepProg)

    def set_main_progress(self, prog):
        self.wMainProgressBar.setValue(prog)

    def set_step_progress(self, prog):
        self.wStepProgressBar.setValue(prog)

    def set_status(self, status):
        self.statusBar().showMessage(status)

    def load_model_params(self, params):
        self.wParams.blockSignals(True)
        self.wParams.setRowCount(len(params))
        for i, param in enumerate(params):
            value = params[param]
            label = QtWidgets.QTableWidgetItem(param)
            label.setFlags(label.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # label = QtWidgets.QLabel()
            # label.setText(param)
            edit = QtWidgets.QTableWidgetItem(str(value))
            # edit.setText(value)
            self.wParams.setItem(i, 0, label)
            self.wParams.setItem(i, 1, edit)
        self.wParams.blockSignals(False)

    # @Slot()
    def new_file(self):
        self.parser = None
        self.wConsole.clear()
        self.wModel.clear()
        self.wParams.clear()
        self.wLayers.clear()
        self.layers_render = []
        self.layers_fp = []

        self.FPPlt.clear()
        self.FPPlt.render()
        self.renderPlt.clear()
        self.renderPlt.render()

        self.set_status("New file")
        self.set_main_progress(0)

        self.rcFP.clear()
        self.rcRender.clear()

        self.docName = None
        self.setWindowTitle("FoldTheLine")

    def open_file(self, file):
        self.new_file()
        if not os.path.isfile(file):
            self.console("File not found: {}".format(file))
            return
        self.console("Opening file {}...".format(file))
        self.projectFilename = file

        # self.parser.parse()
        self.sig_parseFile.emit(file)
        print("Sent signal to open file...")

    def update_layers(self):
        print("Updating layers...")
        fpStruct = self.rcFP.get_struct()
        renderStruct = self.rcRender.get_struct()
        self.wLayers.blockSignals(True)
        self.wModel.blockSignals(True)

        def checkLayerItems(container, containerString, struct):
            for label, vis in struct[containerString][0]:
                if len(self.wLayers.findItems(label, Qt.MatchFlag.MatchFixedString | Qt.MatchFlag.MatchRecursive)):
                    continue
                child = QtWidgets.QTreeWidgetItem(container)
                # child.layer = layer
                child.setText(0, label)
                if vis:
                    child.setCheckState(0, Qt.CheckState.Checked)
                else:
                    child.setCheckState(0, Qt.CheckState.Unchecked)

        def checkModelItems(container, data):
            for i, elem in enumerate(data):
                name = "{}  (#{})".format(elem["name"], i)
                if len(self.wModel.findItems(name, Qt.MatchFlag.MatchFixedString | Qt.MatchFlag.MatchRecursive)):
                    continue
                child = QtWidgets.QTreeWidgetItem(container)
                child.layer = elem
                child.setText(0, name)

        checkLayerItems(self.layers_floorplan_layers, "Layers", fpStruct)
        checkLayerItems(self.layers_floorplan_transformations, "Transformations", fpStruct)
        checkLayerItems(self.layers_floorplan_debug, "Debug", fpStruct)
        checkLayerItems(self.layers_render_layers, "Layers", renderStruct)
        checkLayerItems(self.layers_render_transformations, "Transformations", renderStruct)
        checkLayerItems(self.layers_render_debug, "Debug", renderStruct)

        checkModelItems(self.twiModel_layers, self.parser.j_layers)
        checkModelItems(self.twiModel_Transformations, self.parser.j_transformations)

        self.wModel.blockSignals(False)
        self.wLayers.blockSignals(False)
        print("Layers updated.")

    def fileParsed(self):
        self.console("SIG received, file parsed sucessfully.")
        self.docName = self.parser.filename
        self.setWindowTitle("FoldTheLine - {}".format(os.path.basename(self.docName)))
        # self.update_parser()
        # self.sig_updateParser.emit()
        # self.parser.visualize()
        # self.visualize()

        """---//   Generate "Layers" View   ///---"""

        fpStruct = self.rcFP.get_struct()
        renderStruct = self.rcRender.get_struct()

        self.wLayers.blockSignals(True)

        self.layers_floorplan_layers = QtWidgets.QTreeWidgetItem(self.wLayers)
        self.layers_floorplan_layers.setText(0, "Layers")
        self.layers_floorplan_layers.setFlags(self.layers_floorplan_layers.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.layers_fp.append(self.layers_floorplan_layers)
        if fpStruct["Layers"][1]:
            self.layers_floorplan_layers.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.layers_floorplan_layers.setCheckState(0, Qt.CheckState.Unchecked)

        self.layers_floorplan_transformations = QtWidgets.QTreeWidgetItem(self.wLayers)
        self.layers_floorplan_transformations.setText(0, "Transformations")
        self.layers_floorplan_transformations.setFlags(
            self.layers_floorplan_transformations.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.layers_fp.append(self.layers_floorplan_transformations)
        if fpStruct["Transformations"][1]:
            self.layers_floorplan_transformations.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.layers_floorplan_transformations.setCheckState(0, Qt.CheckState.Unchecked)

        self.layers_floorplan_debug = QtWidgets.QTreeWidgetItem(self.wLayers)
        self.layers_floorplan_debug.setText(0, "Debug")
        self.layers_floorplan_debug.setFlags(self.layers_floorplan_debug.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.layers_fp.append(self.layers_floorplan_debug)
        if fpStruct["Debug"][1]:
            self.layers_floorplan_debug.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.layers_floorplan_debug.setCheckState(0, Qt.CheckState.Unchecked)

        self.layers_render_layers = QtWidgets.QTreeWidgetItem(self.wLayers)
        self.layers_render_layers.setText(0, "Layers")
        self.layers_render_layers.setFlags(self.layers_render_layers.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.layers_render.append(self.layers_render_layers)
        if renderStruct["Layers"][1]:
            self.layers_render_layers.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.layers_render_layers.setCheckState(0, Qt.CheckState.Unchecked)

        self.layers_render_transformations = QtWidgets.QTreeWidgetItem(self.wLayers)
        self.layers_render_transformations.setText(0, "Transformations")
        self.layers_render_transformations.setFlags(
            self.layers_render_transformations.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.layers_render.append(self.layers_render_transformations)
        if renderStruct["Transformations"][1]:
            self.layers_render_transformations.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.layers_render_transformations.setCheckState(0, Qt.CheckState.Unchecked)

        self.layers_render_debug = QtWidgets.QTreeWidgetItem(self.wLayers)
        self.layers_render_debug.setText(0, "Debug")
        self.layers_render_debug.setFlags(self.layers_render_debug.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.layers_render.append(self.layers_render_debug)
        if renderStruct["Debug"][1]:
            self.layers_render_debug.setCheckState(0, Qt.CheckState.Checked)
        else:
            self.layers_render_debug.setCheckState(0, Qt.CheckState.Unchecked)

        for branch in self.layers_render:
            branch.setHidden(True)

        # self.wLayers.setCurrentWidget(0);

        self.wLayers.blockSignals(False)

        """---//   Generate "Model" View   ///---"""

        self.twiModel_layers = QtWidgets.QTreeWidgetItem(self.wModel)
        self.twiModel_layers.setText(0, "Layers")
        self.twiModel_layers.setFlags(self.twiModel_layers.flags() & ~Qt.ItemFlag.ItemIsSelectable)

        self.twiModel_Transformations = QtWidgets.QTreeWidgetItem(self.wModel)
        self.twiModel_Transformations.setText(0, "Transformations")
        self.twiModel_Transformations.setFlags(self.twiModel_Transformations.flags() & ~Qt.ItemFlag.ItemIsSelectable)

        self.update_layers()

        self.wModel.expandAll()
        self.wLayers.expandAll()

        self.console("\n\nResetting view...")
        #self.resetView()
        time.sleep(1)
        self.actionReset_View.trigger()
        self.console("\n\nFile parsed successfully.")

        # self.floorplanRendered()

        self.statusBar().showMessage('Ready.')

    def update_parser(self):
        # self.parser.calculate_assignments()
        self.sig_updateParser.emit()

    def floorplanRendered(self):
        print("\nFloorplan rendered, re-rendering view...")
        # self.FPPlt.remove(0)
        # self.FPPlt.show(self.parser.transformer.debugOutput)
        self.rcFP.render()
        # self.resetView()

    def fpcRendered(self):
        print("\nFPC rendered, updating Layers...")
        self.update_layers()
        self.update_layer_visibilities()
        # self.rcRender.render()
        self.rcRender.render()
        # self.resetView()
        print("\n\nRendered render window.\n")

    def render_bent(self):
        # self.FPPlt.show(self.parser.transformer.debugOutput)
        self.console("Rendering... ")
        # self.rcRender.render()
        self.sig_render.emit()
        # self.rcRender.render()

    def visualize(self):
        self.sig_visualize.emit()

    def save_file(self, file):
        self.console("Saving file {}...".format(file))
        # self.console("---Not implemented yet---".format(file))
        json_object = json.dumps(self.parser.j_data, indent=4)
        with open(file, "w") as outfile:
            outfile.write(json_object)
            print("File saved successfully")
            self.docName = file
            self.setWindowTitle("FoldTheLine - {}".format(os.path.basename(file)))

    def set_console_autoscroll(self, autoscroll=None):
        if autoscroll is None:
            #   used as a slot
            self.autoscroll = (self.bConsAutoscroll.isChecked())
        else:
            #   just a normal function
            self.autoscroll = autoscroll


app = QtWidgets.QApplication(sys.argv)
app.setStyle('Oxygen')
main = MainWindow()
thread = QtCore.QThread()
thread.start()
main.worker.moveToThread(thread)

main.initUi()
main.show()
# window = uic.loadUi("form.ui")


headerItem = QtWidgets.QTreeWidgetItem()
item = QtWidgets.QTreeWidgetItem()

main.wLayers.show()

# window.show()
# widget = MainWindow()
# widget.show()
app.exec()

thread.quit()
sys.exit()
thread.wait(5000)
