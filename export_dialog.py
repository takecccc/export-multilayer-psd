from http.client import OK
from .logging_util import log_info, log_warn, log_error
from PySide6.QtWidgets import *
from PySide6.QtGui import QIntValidator
from .tree_item import TreeItem, TreeModel
import substance_painter
import os
import sys
if "export_psd" in locals():
    import importlib
    importlib.reload(export_psd)
else:
    from . import export_psd

# append modules path to sys.path
sys.path.append(os.path.dirname(__file__)+"/modules")
import numpy as np
import pytoshop
from PIL import Image

def getExportMapsFromDocStruct(doc_struct:dict):
    exportMaps = TreeItem()
    for material in doc_struct["materials"]:
        materialNode = TreeItem({"type":"material", "name":material["name"]})
        # materialNode.setCheckState("name", True)
        exportMaps.appendChild(materialNode)
        for channel in material["stacks"][0]["channels"]:
            channelNode = TreeItem({"type":"channel", "name":channel})
            channelNode.setCheckState("name", True)
            materialNode.appendChild(channelNode)
    return exportMaps

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        # substance_painter.logging.info("Export Dialog __init__")
        super(ExportDialog, self).__init__(parent)
        self.setWindowTitle("Export as Multilayer PSD")
        self.resize(640, 480)
        self.cancel = False

        if not substance_painter.project.is_open():
            log_warn("project is not loaded.")
            self.cancel = True
            return

        self.documentStructure = substance_painter.js.evaluate("alg.mapexport.documentStructure()")

        log_info(self.documentStructure)
        if type(self.documentStructure) is not dict:
            log_warn("project is not loaded.")
            self.cancel = True
            return
        
        self.exportMapsFrame = QFrame(self, )
        self.exportMapsLayout = QVBoxLayout()
        self.setCheckStateBtnLayout = QHBoxLayout()
        self.checkAllBtn = QPushButton("Check All")
        self.unCheckAllBtn = QPushButton("UnCheck All")
        self.checkAllBtn.clicked.connect(self.checkAll)
        self.unCheckAllBtn.clicked.connect(self.unCheckAll)
        self.setCheckStateBtnLayout.addWidget(self.checkAllBtn)
        self.setCheckStateBtnLayout.addWidget(self.unCheckAllBtn)
        self.setCheckStateBtnLayout.addStretch()
        self.exportMapsLayout.addLayout(self.setCheckStateBtnLayout)
        
        self.exportMaps = getExportMapsFromDocStruct(self.documentStructure)
        self.exportMapsModel = TreeModel(self, self.exportMaps)
        self.exportMapsModel.addColumns(["name",])
        self.exportMapsTreeView = QTreeView()
        self.exportMapsTreeView.setModel(self.exportMapsModel)
        self.exportMapsTreeView.setHeaderHidden(True)
        self.exportMapsTreeView.expandAll()
        self.exportMapsLayout.addWidget(self.exportMapsTreeView)
        self.exportMapsFrame.setLayout(self.exportMapsLayout)

        self.exportConfigLayout = QFormLayout()

        self.exportDirLayout = QHBoxLayout()
        self.exportDirText = QLineEdit(substance_painter.js.evaluate("alg.mapexport.exportPath()"))
        self.exportDirSelectBtn = QPushButton("...")
        self.exportDirSelectBtn.clicked.connect(self.selectExportDir)
        self.exportDirLayout.addWidget(self.exportDirText)
        self.exportDirLayout.addWidget(self.exportDirSelectBtn)
        self.exportConfigLayout.addRow(QLabel("Export Path"), self.exportDirLayout)

        self.exportSize = QComboBox()
        self.exportSize.addItems(["128", "256", "512", "1024", "2048", "4096", "8192"])
        self.exportSize.setCurrentIndex(4)
        self.exportConfigLayout.addRow(QLabel("TextureSize"), self.exportSize)

        self.exportPadding = QComboBox()
        self.exportPadding.addItems(["Passthrough", "Color", "Transparent", "Diffusion", "Infinite"])
        self.exportPadding.setCurrentIndex(4)
        self.exportConfigLayout.addRow(QLabel("Padding"), self.exportPadding)

        self.exportDilation = QLineEdit()
        self.exportDilation.setValidator(QIntValidator(0, 256, self))
        self.exportDilation.setText("0")
        self.exportConfigLayout.addRow(QLabel("Dilation"), self.exportDilation)

        self.exportBitDepth = QComboBox()
        self.exportBitDepth.addItems(["8", "16", "32"])
        self.exportBitDepth.setCurrentIndex(0)
        self.exportConfigLayout.addRow(QLabel("BitDepth"), self.exportBitDepth)

        self.dialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.dialogButtonBox.accepted.connect(self.export)
        self.dialogButtonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.exportMapsFrame)
        self.layout.addLayout(self.exportConfigLayout)
        self.layout.addWidget(self.dialogButtonBox)
        self.setLayout(self.layout)
    
    def setCheckStateForAll(self, state):
        def iterateChild(item:TreeItem):
            for i in range(item.childCount()):
                childItem = item.child(i)
                if childItem.getCheckState("name") is not None:
                    childItem.setCheckState("name", state)
                iterateChild(childItem)
        iterateChild(self.exportMaps)
        self.exportMapsTreeView.update()
    
    def checkAll(self):
        self.setCheckStateForAll(True)
    
    def unCheckAll(self):
        self.setCheckStateForAll(False)
    
    def selectExportDir(self):
        path = QFileDialog.getExistingDirectory(self, "select export directory", "", QFileDialog.HideNameFilterDetails)
        self.exportDirText.setText(path)
    
    def export(self):
        exportDir = self.exportDirText.text()
        size = int(self.exportSize.currentText())
        exportConfig = {
            "padding": self.exportPadding.currentText(),
            "dilation": int(self.exportDilation.text()),
            "bitDepth": int(self.exportBitDepth.currentText()),
            "resolution": (size, size),
            "dithering": False,
            "keepAlpha": True,
        }
        
        result = export_psd.export_psd(self.documentStructure, self.exportMaps, exportDir, exportConfig, self)
        if result == export_psd.ExportResult.CANCELED:
            QMessageBox.information(
                self,
                "Information",
                "The export of the multi-layer PSD file was canceled."
                )
        else:
            self.accept()
    
    def exec_(self):
        if self.cancel:
            QMessageBox.warning(self, "Warning", "Project is not loaded.")
            return QDialog.Rejected
        super(ExportDialog, self).exec_()
