import os
import sys
import platform
import analyzer
from utils import TreeItem, PieMaker

from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedLayout, QMenu
from PyQt6 import uic

def getRoot():
    if platform.system() == "Windows":
        return os.environ.get("SystemDrive", "C:") + os.sep
    return "/"

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
        self.pieMaker = PieMaker(self.pie, self.fileTree)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)
        
        self.root = getRoot()
        self.treeQueue = []
        self.updateSignal.connect(lambda t: self.treeQueue.append(t))
        self.emptyFolderSignal.connect(lambda item: item.setSize(0))
        self.buildTree(self.fileTree, self.root, self.root)
        self.selectTopItem()

    def update(self):
        updatePie = len(self.treeQueue) > 0
        while len(self.treeQueue) > 0:
            t = self.treeQueue.pop(0)
            self.buildTree(*t)
        
        if updatePie:
            self.showPie()

    def buildTree(self, parent, folder, name, size=None):
        item = TreeItem(parent, name)
        if size:
            selected = self.fileTree.currentItem()
            item.updateSize(size, selected)
        else:
            subpath = os.path.join(folder, name)
            self.scanner.scan(subpath, item, self.updateSignal, self.emptyFolderSignal)

    def selectTopItem(self):
        item = self.fileTree.topLevelItem(0)
        self.fileTree.setCurrentItem(item)

    def showPie(self):
        item = self.fileTree.currentItem()
        self.pieMaker.show(item)

    def showContextMenu(self, position):
        item = self.fileTree.itemAt(position)
        if item is None:
            return

        menu = QMenu()
        update = menu.addAction("Update")
        delete = menu.addAction("Delete")
        delete.setEnabled(item.isErasable())
        action = menu.exec(self.fileTree.viewport().mapToGlobal(position))

        if action == delete:
            path = item.getPath()
            os.remove(path)
            item.destroy(self.fileTree.currentItem())
        elif action == update:
            item.reset(self.fileTree.currentItem())
            self.scanner.scan(item.getPath(), item, self.updateSignal, self.emptyFolderSignal)

if __name__ == "__main__":
    window = QApplication(sys.argv)
    app = AnalyzerUI()
    app.show()
    sys.exit(window.exec())