from PyQt4 import QtCore,QtGui
import pyqtgraph as pg

class Graph(pg.PlotWidget):
    """docstring for Graph"""
    def __init__(self):
        super(Graph, self).__init__()
        