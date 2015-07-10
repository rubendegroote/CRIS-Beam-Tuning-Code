from PyQt4 import QtCore,QtGui
import pyqtgraph as pg
import numpy as np
from copy import deepcopy
import time

class Graph(pg.PlotWidget):
    """docstring for Graph"""
    def __init__(self,parent):
        super(Graph, self).__init__()
        self.beamline = parent.beamline

        self.x = []
        self.y = []
        self.x0 = 0

        self.start = time.time()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.plotData)
        self.timer.start(30)

    def updateGraph(self):
        self.x.append(time.time()-self.start)
        self.y = np.append(self.y,self.beamline.current.value)
        self.x0 = self.beamline.optimalTime-self.start
        
        self.plotItem.setTitle('Current {:.2}'.format(self.beamline.current.value))

    def plotData(self):
        self.plot(np.array(self.x),np.array(self.y),clear=True,pen = 'r')
        self.plot([self.x0],[self.beamline.max],pen='b',
            symbol='o')
        try:
            self.plot([self.x[-1]],[self.y[-1]],pen='r',
                symbol='o')
        except IndexError:
            pass

    def clearPlot(self):
        self.x = []
        self.y = []
        self.clear()

class VoltGraph(Graph):
    def __init__(self,parent,voltName):
        super(VoltGraph, self).__init__(parent)
        self.voltName = voltName

    def updateGraph(self):
        self.x.append(self.beamline.voltages[self.voltName].readback)
        self.y = np.append(self.y,self.beamline.current.value)
        self.x0 = self.beamline.optimalSettings[self.voltName]
        
        title = 'Current {:.2} \t Voltage {} \t Best Voltage {}'.format(
                            self.beamline.current.value,self.x[-1],self.x0)
        self.plotItem.setTitle(title)