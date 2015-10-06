from PyQt4 import QtCore,QtGui
from controls import Control, ScanControl
import threading as th
import numpy as np
import time
from graph import Graph, VoltGraph

class OptimizerWidget(QtGui.QMainWindow):
    """docstring for OptimizerWidget"""
    closed = QtCore.Signal()
    def __init__(self,parent,beamline):
        super(OptimizerWidget, self).__init__(parent)

        self.beamline = beamline
        self.subset = []
        self.cont = False

        self.controls = {}
        self.hotkeyManager = parent.hotkeyManager
        self.voltGraphs = {}

        self.init_UI()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        ok = self.chooseControls()
        if ok:
            self.show()
        else:
            self.close()

    def init_UI(self):
        widget = QtGui.QWidget()
        self.setCentralWidget(widget)
        self.layout = QtGui.QGridLayout(widget)

        self.makeMenuBar()

    def makeMenuBar(self):
        menubar = self.menuBar()

        self.chooseAction = QtGui.QAction('&Choose Controls',self)
        self.chooseAction.setShortcut('Ctrl+C')
        self.chooseAction.triggered.connect(self.chooseControls)

        self.setOptimalAction = QtGui.QAction('Set to &Optimal',self)
        self.setOptimalAction.setShortcut('Ctrl+O')
        self.setOptimalAction.triggered.connect(self.beamline.setToOptimal)

        settingsMenu = menubar.addMenu('&Settings')
        settingsMenu.addAction(self.chooseAction)
        settingsMenu.addAction(self.setOptimalAction)

        self.scanAction = QtGui.QAction('&Scan',self)
        self.scanAction.setShortcut('Ctrl+S')
        self.scanAction.triggered.connect(self.startScan)

        self.stopAction = QtGui.QAction('S&top',self)
        self.stopAction.setShortcut('Ctrl+T')
        self.stopAction.triggered.connect(self.stopScan)

        scanMenu = menubar.addMenu('&Scanning')
        scanMenu.addAction(self.scanAction)
        scanMenu.addAction(self.stopAction)

        self.optimizeBayesAction = QtGui.QAction('&Bayesian Optimize',self)
        self.optimizeBayesAction.setShortcut('Ctrl+B')
        self.optimizeBayesAction.triggered.connect(self.optimize)

        self.optimizeMCMCAction = QtGui.QAction('&MCMC Optimize',self)
        self.optimizeMCMCAction.setShortcut('Ctrl+M')
        self.optimizeMCMCAction.triggered.connect(self.optimize)

        self.optimizeMyMCMCAction = QtGui.QAction('&My MCMC Optimize',self)
        self.optimizeMyMCMCAction.setShortcut('Ctrl+N')
        self.optimizeMyMCMCAction.triggered.connect(self.optimize)

        optimizeMenu = menubar.addMenu('&Optimizer')
        optimizeMenu.addAction(self.optimizeBayesAction)
        optimizeMenu.addAction(self.optimizeMCMCAction)
        optimizeMenu.addAction(self.optimizeMyMCMCAction)


    def chooseControls(self):
        ok,mode,controls = modePrompt.mode(self,
            [n for n in self.beamline.voltages.keys()],self.subset)

        self.subset = controls

        self.addControls(mode)

        return ok

    def addControls(self,mode):
        try:
            self.layout.removeWidget(self.controlsWidget)
            self.controlsWidget.setParent(None)
            self.controls = {}
            self.voltGraphs = {}
        except:
            pass

        self.controlsWidget = QtGui.QWidget()
        controlsLayout = QtGui.QGridLayout(self.controlsWidget)

        i = 0
        for n,v in self.beamline.voltages.items():
            if n in self.subset:
                control = ScanControl(v)
                self.controls[n] = control
                controlsLayout.addWidget(control,2*(i%2),i//2)

                self.voltGraphs[n] = VoltGraph(self,n)
                controlsLayout.addWidget(self.voltGraphs[n],1+2*(i%2),i//2)

                i = i + 1

        self.layout.addWidget(self.controlsWidget,0,1,1,2)

    def update(self):        
        for c in self.controls.values():
            c.update()

        for g in self.voltGraphs.values():
            g.updateGraph()

    def startScan(self):
        for c in self.controls.values():
            c.defineScan()

        self.beamline.startScan(self.subset)

    def stopScan(self):
        self.beamline.stopScan()

    def optimize(self):
        for c in self.controls.values():
            c.defineScan()

        if self.sender() == self.optimizeBayesAction:
            self.beamline.optimize(self.subset,'bayes')
        elif self.sender() == self.optimizeMyMCMCAction:
            self.beamline.optimize(self.subset,'my mcmc')
        else:
            self.beamline.optimize(self.subset,'mcmc')


    def keyPressEvent(self,e):
        self.hotkeyManager.keyPressed(e)
        super(QtGui.QMainWindow,self).keyPressEvent(e)

    def closeEvent(self,event):
        self.stopScan()
        self.closed.emit()
        super(OptimizerWidget,self).close()

class modePrompt(QtGui.QDialog):
    """docstring for modePrompt"""
    def __init__(self,parent,names,subset):
        super(modePrompt, self).__init__(parent)
        self.names = names

        layout = QtGui.QGridLayout(self)

        self.modes = QtGui.QComboBox()
        self.modes.addItems(['Optimizer'])
        layout.addWidget(self.modes,0,0)

        self.modeWidget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout(self.modeWidget)
        layout.addWidget(self.modeWidget,1,0)

    
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons,2,0)

        self.checks = {}

        for i,n in enumerate(self.names):
            self.checks[n] = QtGui.QCheckBox(n)
            if n in subset:
                self.checks[n].setChecked(True)
            self.layout.addWidget(self.checks[n],i,0)

    @staticmethod
    def mode(parent,names, subset):
        modes = modePrompt(parent,names,subset)
        result = modes.exec_()
        return result == QtGui.QDialog.Accepted, modes.modes.currentIndex(),\
                [n for n,c in modes.checks.items() if c.checkState()]
