from PyQt4 import QtCore,QtGui
from controls import ControlsGroup
from graph import Graph

class BeamlineApp(QtGui.QMainWindow):

    def __init__(self):
        super(BeamlineApp, self).__init__()

        self.hotkeys = {QtCore.Qt.Key_F:'F',
                        QtCore.Qt.Key_R:'R',
                        QtCore.Qt.Key_D:'D',
                        QtCore.Qt.Key_E:'E'}

        self.container = Container()
        self.controlsGroup = ControlsGroup()
        self.graph = Graph()
        self.init_UI()
        
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
        self.controlsGroup.controlProcess.terminate()
        for v in self.controlsGroup.voltages.values():
            v.stopRamp = True
        event.accept()

    def keyPressEvent(self,e):
        if e.key() in self.hotkeys.keys():
            self.controlsGroup.keyPressed(self.hotkeys[e.key()])
            e.ignore()
        else:
            e.accept()


class Container(QtGui.QWidget):
    def __init__(self):
        super(Container,self).__init__()
        self.layout = QtGui.QGridLayout(self)
