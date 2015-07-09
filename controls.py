from PyQt4 import QtCore,QtGui
import pyqtgraph as pg
import multiprocessing as mp
import os
from hotkey import HotkeyManager

MAX_OFFSET = 5

class ControlsGroup(QtGui.QWidget):
    def __init__(self,beamline):
        super(ControlsGroup, self).__init__()
        self.beamline = beamline

        self.controls = {}
        self.hotkeyManager = HotkeyManager(self)
        self.optimizers = []

        self.init_UI()

    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)

        for i,(n,v) in enumerate(self.beamline.voltages.items()):
            control = Control(v)
            control.newHotKeys.connect(self.hotkeyManager.defineHotkeys)
            self.controls[n] = control
            self.layout.addWidget(control,i%2,i//2)

    def save(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, 
            'Select file', os.getcwd(),"CSV (*.csv)")
        self.beamline.saveSettings(fileName)
            
    def load(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 
            'Select file', os.getcwd(),"CSV (*.csv)")
        self.beamline.loadSettings(fileName)

    def optimize(self):
        from optimizer import Optimizer
        op = Optimizer(parent=self,beamline=self.beamline)
        op.closed.connect(self.removeOptimizer)
        self.optimizers.append(op)

    def removeOptimizer(self):
        self.optimizers.remove(self.sender())

class Control(QtGui.QWidget):
    newHotKeys = QtCore.Signal(dict)
    def __init__(self,voltage):
        super(Control,self).__init__()
        self.voltage = voltage
        self.step = 1
        
        self.label = QtGui.QLabel(str(voltage.name))
        
        self.hotkeyButton = QtGui.QPushButton('H')
        self.hotkeyButton.setMaximumWidth(25)
        self.hotkeyButton.clicked.connect(self.makeHotkeys)

        self.set = pg.SpinBox(value=voltage.setpoint,
                              min = 0, max = 10**4,
                              step = 1)
        self.set.sigValueChanging.connect(self.valueChanged)
        
        self.readback = QtGui.QLineEdit(str(voltage.readback))
        
        self.init_UI()

    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(self.label,0,0,1,1)
        self.layout.addWidget(self.hotkeyButton,0,1,1,1)
        self.layout.addWidget(self.set,1,0,1,2)
        self.layout.addWidget(self.readback,2,0,1,2)

    def increase(self):
        self.set.setValue(self.set.value() + self.step)
    
    def decrease(self):
        self.set.setValue(self.set.value() - self.step)

    def increaseStep(self):
        self.step =  min(10**3,self.step*10)
    
    def decreaseStep(self):
        self.step = max(1,self.step/10)

    def valueChanged(self):
        self.voltage.setpoint = self.set.value()

    def update(self):
        if self.voltage.ramping:
            self.set.setValue(self.voltage.rampSet)
        else:
            self.set.setValue(self.voltage.setpoint)

        self.readback.setText(str(self.voltage.readback))
                
        if abs(self.voltage.setpoint - self.voltage.readback) > MAX_OFFSET:
            self.setStyleSheet("QLineEdit { background-color: red; }")
        elif abs(self.voltage.rampSet - self.voltage.readback) > MAX_OFFSET:
            self.setStyleSheet("QLineEdit { background-color: yellow; }")
        else:
            self.setStyleSheet("QLineEdit { background-color: green; }")

        if self.voltage.hasHotkeys:
            self.hotkeyButton.setStyleSheet("QPushButton {background-color: green;}")
        else:
            self.hotkeyButton.setStyleSheet("")

    def makeHotkeys(self,e):
        from hotkey import HotkeyPrompt
        hotkeys = HotkeyPrompt.hotkeys(parent=self)
        hotkeys = dict(zip(hotkeys.values(),hotkeys.keys()))
        self.newHotKeys.emit(hotkeys)
        self.voltage.hasHotkeys = True
