from PyQt4 import QtCore,QtGui
from controls import Control
import threading as th
import numpy as np
import time
from graph import Graph, VoltGraph

class Optimizer(QtGui.QDialog):
    """docstring for Optimizer"""
    def __init__(self,parent,beamline,subset):
        super(Optimizer, self).__init__(parent)

        self.beamline = beamline
        self.subset = subset

        self.controls = {}
        self.voltGraphs = {}

        self.graph = Graph(self.beamline)
        self.init_UI()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        self.updateGraph = False

    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)
    
        i = 0
        for n,v in self.beamline.voltages.items():
            if n in self.subset:
                copy = Control(v)
                self.controls[n] = copy
                self.layout.addWidget(copy,1+2*(i%2),i//2)

                self.voltGraphs[n] = VoltGraph(self.beamline,n)
                self.layout.addWidget(self.voltGraphs[n],2+2*(i%2),i//2)

                i = i + 1

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons,10,i//2)

        self.scanButton = QtGui.QPushButton('Scan')
        self.layout.addWidget(self.scanButton,9,i//2)
        self.scanButton.clicked.connect(self.startScan)

        self.stopButton = QtGui.QPushButton('Stop')
        self.layout.addWidget(self.stopButton,9,i//2-1)
        self.stopButton.clicked.connect(self.stopScan)

        self.setOptimalButton = QtGui.QPushButton('Set to optimal values')
        self.setOptimalButton.clicked.connect(self.beamline.setToOptimal)
        self.layout.addWidget(self.setOptimalButton,9,i//2-2)

        self.layout.addWidget(self.graph,0,0,1,i//2)

        self.optimal = QtGui.QLabel()
        self.layout.addWidget(self.optimal,0,i//2,1,1)


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
            e.accept()

    @staticmethod
    def optimize(parent,beamline,subset):
        optimizer = Optimizer(parent,beamline,subset)
        result = optimizer.exec_()
        optimizer.cont = False
        return result==QtGui.QDialog.Accepted
