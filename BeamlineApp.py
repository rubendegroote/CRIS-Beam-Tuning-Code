from PyQt4 import QtCore,QtGui
import threading as th

from controls import ControlsGroup
from graph import Graph
from backend import controlLoop, Voltage, Beamline
from hotkey import HotkeyManager

from copy import deepcopy


class BeamlineApp(QtGui.QMainWindow):

    def __init__(self):
        super(BeamlineApp, self).__init__()

        self.beamline = Beamline()
        self.optimizers = []
        self.hotkeyManager = HotkeyManager(self)

        self.container = Container()
        self.controlsGroup = ControlsGroup(self)
        self.graph = Graph(self)
        self.init_UI()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    def update(self):
        for c in self.controlsGroup.controls.values():
            c.update()
        self.graph.updateGraph()

    def init_UI(self):
        self.setCentralWidget(self.container)
        self.container.layout.addWidget(self.graph,0,0)
        self.container.layout.addWidget(self.controlsGroup,1,0)

        self.makeMenuBar()

        self.show()

    def makeMenuBar(self):
        menubar = self.menuBar()

        self.saveAction = QtGui.QAction('&Save',self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.setStatusTip('Save beam tuning parameters')
        self.saveAction.triggered.connect(self.controlsGroup.save)

        self.loadAction = QtGui.QAction('&Load',self)
        self.loadAction.setShortcut('Ctrl+O')
        self.loadAction.setStatusTip('Load beam tuning parameters')
        self.loadAction.triggered.connect(self.controlsGroup.load)

        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.loadAction)

        self.optimizeAction = QtGui.QAction('&Optimize',self)
        self.optimizeAction.setShortcut('Ctrl+T')
        self.optimizeAction.setStatusTip('Optimize beam tuning parameters')
        self.optimizeAction.triggered.connect(self.optimize)

        beamMenu = menubar.addMenu('&Beamline')
        beamMenu.addAction(self.optimizeAction)

    def optimize(self):
        from optimizer import OptimizerWidget
        op = OptimizerWidget(parent=self,beamline=self.beamline)
        op.closed.connect(self.removeOptimizer)
        self.optimizers.append(op)

    def removeOptimizer(self):
        self.optimizers.remove(self.sender())

    def closeEvent(self,event):
        self.beamline.controlProcess.terminate()
        self.beamline.stop = True
        for v in self.controlsGroup.beamline.voltages.values():
            v.stopRamp = True
        event.accept()

    def keyPressEvent(self,e):
        self.controlsGroup.hotkeyManager.keyPressed(e)
        e.accept()

class Container(QtGui.QWidget):
    def __init__(self):
        super(Container,self).__init__()
        self.layout = QtGui.QGridLayout(self)
