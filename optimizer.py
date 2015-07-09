from PyQt4 import QtCore,QtGui
from controls import Control
import threading as th
import numpy as np
import time
from graph import Graph, VoltGraph

class Optimizer(QtGui.QMainWindow):
    """docstring for Optimizer"""
    closed = QtCore.Signal()
    def __init__(self,parent,beamline):
        super(Optimizer, self).__init__(parent)

        self.beamline = beamline
        self.subset = []

        self.controls = {}
        self.hotkeyManager = parent.hotkeyManager
        self.voltGraphs = {}

        self.graph = Graph(self.beamline)
        self.init_UI()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        self.updateGraph = False

        self.chooseControls()

    def init_UI(self):
        widget = QtGui.QWidget()
        self.setCentralWidget(widget)
        self.layout = QtGui.QGridLayout(widget)
    
        self.optimal = QtGui.QLabel()
        self.layout.addWidget(self.optimal,0,1,1,1)
        self.layout.addWidget(self.graph,0,0,1,1)

        self.makeMenuBar()
        self.show()

    def makeMenuBar(self):
        menubar = self.menuBar()

        self.chooseAction = QtGui.QAction('&Choose Controls',self)
        self.chooseAction.setShortcut('Ctrl+C')
        self.chooseAction.triggered.connect(self.chooseControls)

        self.setOptimalAction = QtGui.QAction('Set to &Optimal',self)
        self.setOptimalAction.setShortcut('Ctrl+O')
        self.setOptimalAction.triggered.connect(self.beamline.setToOptimal)

        optimizerMenu = menubar.addMenu('&Optimizer')
        optimizerMenu.addAction(self.chooseAction)
        optimizerMenu.addAction(self.setOptimalAction)


        self.scanAction = QtGui.QAction('&Scan',self)
        self.scanAction.setShortcut('Ctrl+S')
        self.scanAction.triggered.connect(self.startScan)

        self.stopAction = QtGui.QAction('S&top',self)
        self.stopAction.setShortcut('Ctrl+T')
        self.stopAction.triggered.connect(self.stopScan)

        scanMenu = menubar.addMenu('&Scanning')
        scanMenu.addAction(self.scanAction)
        scanMenu.addAction(self.stopAction)
        
    def chooseControls(self):
        ok,controls = controlsPrompt.controls(self,
            [n for n in self.beamline.voltages.keys()])

        self.subset = controls

        self.addControls()

    def addControls(self):
        try:
            self.layout.removeWidget(self.controlsWidget)
            self.controlsWidget.setParent(None)
        except:
            pass

        self.controlsWidget = QtGui.QWidget()
        controlsLayout = QtGui.QGridLayout(self.controlsWidget)

        i = 0
        for n,v in self.beamline.voltages.items():
            if n in self.subset:
                copy = Control(v)
                self.controls[n] = copy
                controlsLayout.addWidget(copy,1+2*(i%2),i//2)

                self.voltGraphs[n] = VoltGraph(self.beamline,n)
                controlsLayout.addWidget(self.voltGraphs[n],2+2*(i%2),i//2)

                i = i + 1

        self.layout.addWidget(self.controlsWidget,1,0,1,2)

    def update(self):        
        for c in self.controls.values():
            c.update()

        if self.updateGraph:
            self.graph.updateGraph()

        for g in self.voltGraphs.values():
            g.updateGraph()

        text = [n + ': ' + str(v) for n,v in self.beamline.optimalSettings.items()]
        text = "\n".join(text)
        self.optimal.setText(text)

    def startScan(self):
        self.cont = True
        self.graph.clearPlot()
        self.scanThread = th.Thread(target = self.scan)
        self.scanThread.start()

    def stopScan(self):
        self.cont = False

    def scan(self):
        self.updateGraph = True
        ra = np.linspace(0,10**4,100)
        for n,v in self.beamline.voltages.items():
            if n in self.subset:
                for r in ra:
                    if self.cont:
                        v.setpoint = r
                        time.sleep(0.5)
                    else:
                        break
                if not self.cont:
                    break
                self.beamline.setToOptimal()

        self.updateGraph = False


    def keyPressEvent(self,e):
        if e.key() == QtCore.Qt.Key_Enter:
            e.ignore()
        else:
            self.hotkeyManager.keyPressed(e)
            e.ignore()



    def closeEvent(self,event):
        self.cont = False
        self.closed.emit()
        super(Optimizer,self).close()

class controlsPrompt(QtGui.QDialog):
    """docstring for controlsPrompt"""
    def __init__(self,parent,names):
        super(controlsPrompt, self).__init__(parent)

        self.layout = QtGui.QGridLayout(self)

        self.checks = {}

        for i,n in enumerate(names):
            self.checks[n] = QtGui.QCheckBox(n)
            self.layout.addWidget(self.checks[n],i,0)
    
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons,100,100)

    @staticmethod
    def controls(parent,names):
        ctrls = controlsPrompt(parent,names)
        result = ctrls.exec_()
        return result == QtGui.QDialog.Accepted, \
                [n for n,c in ctrls.checks.items() if c.checkState()]
