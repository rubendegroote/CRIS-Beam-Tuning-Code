from PyQt4 import QtCore,QtGui
from controls import ControlsGroup
from graph import Graph
from backend import controlLoop, Voltage, Beamline

from copy import deepcopy

class BeamlineApp(QtGui.QMainWindow):

    def __init__(self):
        super(BeamlineApp, self).__init__()

        self.beamline = Beamline()

        self.container = Container()
        self.controlsGroup = ControlsGroup(self.beamline)
        self.graph = Graph(self.beamline)
        self.init_UI()
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    def update(self):
        self.beamline.update()
        for c in self.controlsGroup.controls.values():
            c.update()
        self.graph.updateGraph()


    def init_UI(self):
        self.setCentralWidget(self.container)
        self.container.layout.addWidget(self.graph,0,0)
        self.container.layout.addWidget(self.controlsGroup,1,0)

        self.makeToolbar()

        self.show()

    def makeToolbar(self):
        self.toolbar = QtGui.QToolBar()
        self.toolbar.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.addToolBar(self.toolbar)

        self.saveAction = QtGui.QPushButton('Save',self)
        self.saveAction.clicked.connect(self.controlsGroup.save)
        self.toolbar.addWidget(self.saveAction)

        self.loadAction = QtGui.QPushButton('Load',self)
        self.loadAction.clicked.connect(self.controlsGroup.load)
        self.toolbar.addWidget(self.loadAction)

        self.optimizeAction = QtGui.QPushButton('Optimize',self)
        self.optimizeAction.clicked.connect(self.controlsGroup.optimize)
        self.toolbar.addWidget(self.optimizeAction)

    def closeEvent(self,event):
        self.beamline.controlProcess.terminate()
        for v in self.controlsGroup.beamline.voltages.values():
            v.stopRamp = True
        event.accept()

    def keyPressEvent(self,e):
        self.controlsGroup.keyPressed(e)
        e.ignore()



class Container(QtGui.QWidget):
    def __init__(self):
        super(Container,self).__init__()
        self.layout = QtGui.QGridLayout(self)
