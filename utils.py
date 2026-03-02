import os
import math
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem, QWidget
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtGui import QPainter, QColor, QColorConstants

def formatBytes(value):
    units = ["bytes", "KB", "MB", "GB", "TB", "PB"]
    index = int(math.log(value)/math.log(1024)) if value > 0 else 0
    value *= 1024**(-index)
    format = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{format} {units[index]}"

class TreeItem(QTreeWidgetItem):
    def __init__(self, parent, name, size=0):
        super().__init__(parent)
        self.setTextAlignment(1, Qt.AlignmentFlag.AlignHCenter)
        self.setName(name)
        self.setSize(size)
    
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

    def getPath(item):
        path = Path()
        while item:
            path = Path(item.name)/path
            item = item.parent()
        return path
    
    def reset(self, selectedItem):
        self.takeChildren()
        self.updateSize(-self.size, selectedItem)
    
    def destroy(self, selectedItem):
        self.reset(selectedItem)
        self.parent().removeChild(self)

    def isErasable(self):
        if self.parent() is None:
            return False
        
        path = self.getPath()
        testname = path.with_name(f"{self.name}.__testdelete__")
        try:
            os.rename(path, testname)
            os.rename(testname, path)
            return True
        except (PermissionError, OSError):
            return False

class PieMaker:
    def __init__(self, parent, tree):
        self.tree = tree
        self.series = QPieSeries()
        chart = QChart()
        chart.addSeries(self.series)
        chart.legend().setVisible(False)
        chart.setBackgroundVisible(False)
        chart.setPlotAreaBackgroundVisible(False)
        chart.setBackgroundBrush(QColor(0, 0, 0, 0))
        chart.setPlotAreaBackgroundBrush(QColor(0, 0, 0, 0))

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setStyleSheet("background: transparent;")
        chart_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        parent.layout().addWidget(chart_view)

    def show(self, item):
        self.series.clear()
        self.slicesMap = {}
        totalSize = 0

        def addData(item):
            nonlocal self, totalSize
            size = max(item.size, 1)
            totalSize += size
            if size/totalSize > 0.01:
                slice = self.series.append(item.name, size)
                self.slicesMap[slice] = item

        if item.childCount() == 0:
            addData(item)
        else:
            for i in range(item.childCount()):
                addData(item.child(i))

        def selectItem(slice):
            item = self.slicesMap[slice]
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)

        for slice in self.series.slices():
            slice.clicked.connect(lambda s=slice: selectItem(s))
            if slice.angleSpan() > 3:
                slice.setLabelColor(QColorConstants.White)
                slice.setLabelVisible(True)