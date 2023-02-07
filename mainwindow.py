# This Python file uses the following encoding: utf-8
import sys
from PyQt6 import uic
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QFileDialog, QStyle, QTreeWidgetItem
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6 import QtGui
#from PyQt6 import Qt
import sys
import PyQt6

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
#from vedo import Mesh, dataurl, Plotter
import vedo as v

from MatrixTransformer import *
from Transformation import *
from ZBend import *
from LinearTransformation import *
from FileParser import FileParser
from RenderContainer import *

global MODE_GUI
MODE_GUI = True


class port:
    def __init__(self,view):
        self.view = view

    def write(self,*args):
        self.view.insertPlainText(*args)
    def flush(self):
        pass


#from PySide6.QtWidgets import QApplication, QMainWindow

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
#from ui_form import Ui_MainWindow

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.ui = Ui_MainWindow()
        #self.ui.setupUi(self)
        uic.loadUi('form.ui', self)

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
                     (self.bConsClear, "edit-clear-history"),
                     (self.bConsAutoscroll, "gnumeric-format-valign-bottom"),
                     (self.bConsC, "edit-copy")]
        tbActions = [   self.actionFileNew,
                        self.actionFileOpen,
                        #self.actionFileRecent,
                        self.actionFileSave,
                        #self.actionFileSave_as,
                        #self.actionFileExport,
                        self.actionFileQuit,
                        self.actionEditAdd_mesh_layer,
                        #self.actionEditAdd_transformation,
                        self.actionToolsFreeCAD,
                        self.actionToolsKiCAD,
                        self.actionReset_View,
                        self.actionRender
                        #self.actionToolsKiCAD
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
                icon = QtGui.QIcon("icons/"+name+".svg")
                item.setIcon(icon)
            #if type(item) == QtGui.QAction:
            #    self.tbMain.addAction(item)
        for action in tbActions:
            self.tbMain.addAction(action)

        self.wMainProgressBar = QtWidgets.QProgressBar()
        self.wStepProgressBar = QtWidgets.QProgressBar()

        self.statusBar().addPermanentWidget(self.wMainProgressBar)
        self.statusBar().addPermanentWidget(self.wStepProgressBar)
        self.wMainProgressBar.setGeometry(30, 20, 200, 25)
        self.wMainProgressBar.setValue(10)
        self.wStepProgressBar.setGeometry(30, 20, 200, 25)
        self.wStepProgressBar.setValue(10)

        self.bConsClear.setText("")
        self.bConsAutoscroll.setText("")
        self.bConsC.setText("")

        self.actionFileQuit.triggered.connect(self.close)
        self.actionFileNew.triggered.connect(self.new_file)
        self.actionFileOpen.triggered.connect(self.openFileDialog)
        self.actionFileSave.triggered.connect(self.saveFileDialog)
        self.actionReset_View.triggered.connect(self.resetView)

        self.wModel.clicked.connect(self.modelItemClicked)
        self.wParams.cellChanged.connect(self.modelParameterChanged)

        self.wGrafTab.currentChanged.connect(self.onTabChange)

        self.wLayers.itemChanged[QTreeWidgetItem, int].connect(self.layerItemChanged)

        #actionFileOpen.triggered.connect(self.new_file)

        self.console("Starting... ")

        self.wParams.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.wModel.setHeaderLabels(["Model"])
        self.wLayers.setHeaderLabels(["Visibility"])

        self.FPWidget = QVTKRenderWindowInteractor(self)
        self.wFPLayout.addWidget(self.FPWidget)
        self.FPPlt = v.Plotter(qt_widget=self.FPWidget, axes=1)

        self.renderWidget = QVTKRenderWindowInteractor(self)
        self.wRenderLayout.addWidget(self.renderWidget)
        self.renderPlt = v.Plotter(qt_widget=self.renderWidget, axes=1)

        self.rcFP = RenderContainer(self.FPPlt)
        self.rcRender = RenderContainer(self.renderPlt)

        #sys.stdout = port(self.wConsole)

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

    def openFileDialog(self):
        file, _ = QFileDialog.getOpenFileName(self, "Pick a FTL file", "LTest_hook.json", filter="*.json", options=QFileDialog.Option.DontUseNativeDialog)
        self.open_file(file)

    def saveFileDialog(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save file", filter="*.json", options=QFileDialog.Option.DontUseNativeDialog)
        self.save_file(file)

    def modelItemClicked(self, item):
        self.wParams.blockSignals(True)

        if item.parent().row() == -1:
            return
        #debug("Item clicked: {} in row {} with data <{}>".format(item, item.row(), item.data()))
        parent = item.parent()
        if (parent.data() == "Layers"):
            self.load_model_params(self.parser.j_layers[item.row()])
            self.current_model_item = self.parser.j_layers[item.row()]
        if (parent.data() == "Transformations"):
            self.load_model_params(self.parser.j_transformations[item.row()])
            self.current_model_item = self.parser.j_transformations[item.row()]
            #debug("Transformation {} clicked".format(item.row()))
        self.wParams.blockSignals(False)


    def resetView(self):
        self.rcFP.plotter.reset_camera()
        self.rcFP.plotter.look_at("xy")
        #self.rcFP.plotter.fly_to((0, 0, 50))
        self.rcRender.plotter.reset_camera()
        self.rcRender.plotter.look_at("xy")
        self.rcFP.plotter.render()
        self.rcRender.plotter.render()
        #self.rcFP.plotter.

    def modelParameterChanged(self, row, col):
        debug("item changed at {}/{}".format(row, col))
        label = self.wParams.item(row, 0).text()
        val = self.wParams.item(row, 1).text()
        debug("{} = {}".format(label, val))
        #debug (self.wModel.selectedItem().text(0))
        self.current_model_item[label] = val
        #if wModel.
        #self.parser.j_layers[label] = val

    def onTabChange(self, i):
        if i == 0:          #"Floorplan" tab
            for branch in self.layers_render:
                branch.setHidden(True)
            for branch in self.layers_fp:
                branch.setHidden(False)
        elif i == 1:          #"Floorplan" tab
            for branch in self.layers_render:
                branch.setHidden(False)
            for branch in self.layers_fp:
                branch.setHidden(True)
        else:
            raise Exception("Error: Tab {} not found".format(i))

    def layerItemChanged(self, item, column):
        parent = item.parent()
        checked = item.checkState(column) == Qt.CheckState.Checked
        if parent is None:
            #top layer item
            name = item.text(0)
            if self.wGrafTab.currentIndex() == 0:
                # "Floorplan" Tab
                if name == "Layers":
                    self.rcFP.set_container_visibility(ItemType.Layer, checked)
                elif name == "Transformations":
                    self.rcFP.set_container_visibility(ItemType.Transformation, checked)
                elif name == "Debug":
                    self.rcFP.set_container_visibility(ItemType.Debug, checked)
                else:
                    debug("Unknown container type.")
                    return
                self.rcFP.render()
            elif self.wGrafTab.currentIndex() == 1:
                # "Floorplan" Tab
                if name == "Layers":
                    self.rcRender.set_container_visibility(ItemType.Layer, checked)
                elif name == "Transformations":
                    self.rcRender.set_container_visibility(ItemType.Transformation, checked)
                elif name == "Debug":
                    self.rcRender.set_container_visibility(ItemType.Debug, checked)
                else:
                    debug("Unknown container type.")
                    return
                self.rcRender.render()
            else:
                raise Exception("Tab {} not found.".format(self.wGrafTab.currentIndex()))
            return
        # inner layer item; first get parent type
        cName = parent.text(0)
        if cName == "Layers":
            container = ItemType.Layer
        elif cName == "Transformations":
            container = ItemType.Transformation
        elif cName == "Debug":
            container = ItemType.Debug
        else:
            debug("Unknown container type.")
            return
        self.rcFP.set_item_visibility(container, item.text(0), checked)
        self.rcFP.render()

    """##################################
    #######  STRUCTURAL FUNCTIONS  ######
    ##################################"""

    def save_model_data(self):
        for i in range(self.wModel.columnCount()):
            label = self.wModel.itemAt(i, 0)
            val = self.wModel.itemAt(i, 1)
            debug("{} = {}".format(label, val))

    def console(self, msg):
        #self.wConsole.append(msg)
        self.wConsole.insertPlainText(msg+"\n")

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
            #label = QtWidgets.QLabel()
            #label.setText(param)
            edit = QtWidgets.QTableWidgetItem(str(value))
            #edit.setText(value)
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

        self.FPPlt.clear()
        self.FPPlt.render()
        self.renderPlt.clear()
        self.renderPlt.render()

        self.rcFP.clear()
        self.rcRender.clear()

    def open_file(self, file):
        if not os.path.isfile(file):
            self.console("File not found: {}".format(file))
            return
        self.console("Opening file {}...".format(file))
        self.projectFilename = file

        self.parser = FileParser(file, self.rcFP, self.rcRender)
        self.parser.parse()
        self.update_parser()
        self.parser.visualize()

        """---//   Generate "Layers" View   ///---"""

        fpStruct = self.rcFP.get_struct()
        renderStruct = self.rcRender.get_struct()

        self.wLayers.blockSignals(True)

        layers_floorplan_layers = QtWidgets.QTreeWidgetItem(self.wLayers)
        layers_floorplan_layers.setText(0, "Layers")
        layers_floorplan_layers.setFlags(layers_floorplan_layers.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.layers_fp.append(layers_floorplan_layers)
        if (fpStruct["Layers"][1]):
            layers_floorplan_layers.setCheckState(0, Qt.CheckState.Checked)
        else:
            layers_floorplan_layers.setCheckState(0, Qt.CheckState.Unchecked)
        for label, vis in fpStruct["Layers"][0]:
            child = QtWidgets.QTreeWidgetItem(layers_floorplan_layers)
            # child.layer = layer
            child.setText(0, label)
            if vis:
                child.setCheckState(0, Qt.CheckState.Checked)
            else:
                child.setCheckState(0, Qt.CheckState.Unchecked)

        layers_floorplan_transformations = QtWidgets.QTreeWidgetItem(self.wLayers)
        layers_floorplan_transformations.setText(0, "Transformations")
        layers_floorplan_transformations.setCheckState(0, Qt.CheckState.Unchecked)
        self.layers_fp.append(layers_floorplan_transformations)
        for label, vis in fpStruct["Transformations"][0]:
            child = QtWidgets.QTreeWidgetItem(layers_floorplan_transformations)
            # child.layer = layer
            child.setText(0, label)
            if vis:
                child.setCheckState(0, Qt.CheckState.Checked)
            else:
                child.setCheckState(0, Qt.CheckState.Unchecked)

        layers_floorplan_debug = QtWidgets.QTreeWidgetItem(self.wLayers)
        layers_floorplan_debug.setText(0, "Debug")
        layers_floorplan_debug.setCheckState(0, Qt.CheckState.Unchecked)
        self.layers_fp.append(layers_floorplan_debug)
        for label, vis in fpStruct["Debug"][0]:
            child = QtWidgets.QTreeWidgetItem(layers_floorplan_debug)
            # child.layer = layer
            child.setText(0, label)
            if vis:
                child.setCheckState(0, Qt.CheckState.Checked)
            else:
                child.setCheckState(0, Qt.CheckState.Unchecked)

        layers_render_layers = QtWidgets.QTreeWidgetItem(self.wLayers)
        layers_render_layers.setText(0, "Layers")
        layers_render_layers.setFlags(layers_render_layers.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        self.layers_render.append(layers_render_layers)
        if (renderStruct["Layers"][1]):
            layers_render_layers.setCheckState(0, Qt.CheckState.Checked)
        else:
            layers_render_layers.setCheckState(0, Qt.CheckState.Unchecked)
        for label, vis in fpStruct["Layers"][0]:
            child = QtWidgets.QTreeWidgetItem(layers_render_layers)
            # child.layer = layer
            child.setText(0, label)
            if vis:
                child.setCheckState(0, Qt.CheckState.Checked)
            else:
                child.setCheckState(0, Qt.CheckState.Unchecked)

        layers_render_transformations = QtWidgets.QTreeWidgetItem(self.wLayers)
        layers_render_transformations.setText(0, "Transformations")
        layers_render_transformations.setCheckState(0, Qt.CheckState.Unchecked)
        self.layers_render.append(layers_render_transformations)
        for label, vis in renderStruct["Transformations"][0]:
            child = QtWidgets.QTreeWidgetItem(layers_render_transformations)
            # child.layer = layer
            child.setText(0, label)
            if vis:
                child.setCheckState(0, Qt.CheckState.Checked)
            else:
                child.setCheckState(0, Qt.CheckState.Unchecked)

        layers_render_debug = QtWidgets.QTreeWidgetItem(self.wLayers)
        layers_render_debug.setText(0, "Debug")
        layers_render_debug.setCheckState(0, Qt.CheckState.Unchecked)
        self.layers_render.append(layers_render_debug)
        for label, vis in renderStruct["Debug"][0]:
            child = QtWidgets.QTreeWidgetItem(layers_render_debug)
            # child.layer = layer
            child.setText(0, label)
            if vis:
                child.setCheckState(0, Qt.CheckState.Checked)
            else:
                child.setCheckState(0, Qt.CheckState.Unchecked)

        for branch in self.layers_render:
            branch.setHidden(True)

        self.wLayers.blockSignals(False)

        """---//   Generate "Model" View   ///---"""

        twiModel_layers = QtWidgets.QTreeWidgetItem(self.wModel)
        twiModel_layers.setText(0, "Layers")
        for i, layer in enumerate(self.parser.j_layers):
            child = QtWidgets.QTreeWidgetItem(twiModel_layers)
            child.layer = layer
            child.setText(0, "{}  (#{})".format(layer["name"], i))

        twiModel_Transformations = QtWidgets.QTreeWidgetItem(self.wModel)
        twiModel_Transformations.setText(0, "Transformations")
        for i, tr in enumerate(self.parser.j_transformations):
            child = QtWidgets.QTreeWidgetItem(twiModel_Transformations)
            child.setText(0, "{}  (#{})".format(tr["name"], i))

        self.wModel.expandAll()
        self.wLayers.expandAll()

        self.console("\n\nFile parsed successfully.")

        self.render_floorplan()
        self.resetView()

        self.statusBar().showMessage('Ready.')


    def update_parser(self):
        self.parser.calculate_assignments()

    def render_floorplan(self):
        #self.FPPlt.remove(0)
        #self.FPPlt.show(self.parser.transformer.debugOutput)
        self.rcFP.render()

    def save_file(self, file):
        self.console("Saving file {}...".format(file))
        self.console("---Not implemented yet---".format(file))

    def set_console_autoscroll(self, autoscroll):
        self.autoscroll = autoscroll




app = QtWidgets.QApplication(sys.argv)
app.setStyle('Oxygen')
main = MainWindow()
main.show()
#window = uic.loadUi("form.ui")


headerItem  = QtWidgets.QTreeWidgetItem()
item = QtWidgets.QTreeWidgetItem()


main.wLayers.show()


#window.show()
#widget = MainWindow()
#widget.show()
sys.exit(app.exec())
