import os
import sys
import math
import platform
import analyzer

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QModelIndex, QItemSelectionModel
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QStackedLayout
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtGui import QPainter, QColor, QColorConstants
from PyQt6 import uic

def getRoot():
    if platform.system() == "Windows":
        return os.environ.get("SystemDrive", "C:") + os.sep
    return "/"

def formatBytes(value):
    units = ["bytes", "KB", "MB", "GB", "TB", "PB"]
    index = int(math.log(value)/math.log(1024)) if value > 0 else 0
    value *= 1024**(-index)
    format = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{format} {units[index]}"

class TreeItem(QTreeWidgetItem):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTextAlignment(1, Qt.AlignmentFlag.AlignHCenter)
        self.name = None
        self.size = 0
        self.slice = None
    
    def setName(self, name):
        self.name = name
        self.setText(0, name)

    def updateSize(self, deltaSize, selectedItem):
        self.setSize(self.size+deltaSize)
        parent = self.parent()
        if type(parent) == TreeItem:
            parent.updateSize(deltaSize, selectedItem)

    def setSize(self, size):
        self.size = size
        self.setText(1, formatBytes(size))

    def setSlice(self, slice):
        self.slice = slice

class AnalyzerUI(QMainWindow):
    updateSignal = pyqtSignal(tuple)
    emptyFolderSignal = pyqtSignal(TreeItem)
    scanner = analyzer.Analyzer(4)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        uic.loadUi("gui.ui", self)
        self.fileTree.headerItem().setText(0, "")
        
        pieLayout = QStackedLayout()
        pieLayout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.pie.setLayout(pieLayout)

        self.pieSeries = self.createPie()
        self.timer = QTimer()
        self.timer.timeout.connect(self.showPie)
        self.timer.start(1000)
        
        self.root = getRoot()
        self.updateSignal.connect(lambda t: self.buildTree(*t))
        self.emptyFolderSignal.connect(lambda item: item.setSize(0))
        self.buildTree(self.fileTree, self.root, self.root)
        self.selectTopItem()

    def buildTree(self, parent, folder, name, size=None):
        item = TreeItem(parent)
        item.setName(name)

        selected = self.fileTree.selectedItems()
        selected = selected[0] if len(selected) > 0 else None
        if size:
            item.updateSize(size, selected)
        else:
            subpath = os.path.join(folder, name)
            self.scanner.scan(subpath, item, self.updateSignal, self.emptyFolderSignal)

    def selectTopItem(self):
        model = self.fileTree.model()
        index = model.index(0, 0, QModelIndex())
        self.fileTree.setCurrentIndex(index)
        self.fileTree.selectionModel().select(
            index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect |
            QItemSelectionModel.SelectionFlag.Rows
        )

    def showPie(self):
        items = self.fileTree.selectedItems()
        if len(items) > 0:
            self.makePie(items[0])

    def makePie(self, item):
        self.pieSeries.clear()

        for i in range(item.childCount()):
            child = item.child(i)
            child.setSlice(self.pieSeries.append(child.name, child.size))
        else:
            item.setSlice(self.pieSeries.append(item.name, 1))

        for slice in self.pieSeries.slices():
            if slice.angleSpan() > 3:
                slice.setLabelColor(QColorConstants.White)
                slice.setLabelVisible(True)

    def createPie(self):
        series = QPieSeries()
        chart = QChart()
        chart.addSeries(series)
        chart.legend().setVisible(False)
        chart.setBackgroundVisible(False)
        chart.setPlotAreaBackgroundVisible(False)
        chart.setBackgroundBrush(QColor(0, 0, 0, 0))
        chart.setPlotAreaBackgroundBrush(QColor(0, 0, 0, 0))

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("background: transparent;")
        chart_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.pie.layout().addWidget(chart_view)
        return series

if __name__ == "__main__":
    window = QApplication(sys.argv)
    app = AnalyzerUI()
    app.show()
    sys.exit(window.exec())