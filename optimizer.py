from PyQt4 import QtCore,QtGui
from controls import Control

class Optimizer(QtGui.QDialog):
    """docstring for Optimizer"""
    def __init__(self,parent,voltages):
        super(Optimizer, self).__init__(parent)

        self.voltages = voltages
        self.controls = {}

        self.init_UI()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)
    
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        for i,(n,v) in enumerate(self.voltages.items()):
            copy = Control(v)
            self.controls[n] = copy
            self.layout.addWidget(copy,i%2,i//2)

        self.layout.addWidget(buttons,100,100)

    def update(self):        
        for c in self.controls.values():
            c.update()

    def keyPressEvent(self,e):
        if e.key() == QtCore.Qt.Key_Enter:
            e.ignore()
        else:
            e.accept()


    @staticmethod
    def optimize(parent,voltages):
        optimizer = Optimizer(parent,voltages)
        result = optimizer.exec_()
        return result==QtGui.QDialog.Accepted,\
            [c.set.value() for c in optimizer.controls.values()]