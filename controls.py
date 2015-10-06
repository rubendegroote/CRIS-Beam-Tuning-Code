from PyQt4 import QtCore,QtGui
import pyqtgraph as pg
import multiprocessing as mp
import os
import time

MAX_OFFSET = 5

class ControlsGroup(QtGui.QWidget):
    def __init__(self,parent):
        super(ControlsGroup, self).__init__()
        self.beamline = parent.beamline

        self.controls = {}
        self.hotkeyManager = parent.hotkeyManager

        self.init_UI()

    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)

        for i,(n,v) in enumerate(self.beamline.voltages.items()):
            control = Control(v)
            control.newHotKeys.connect(self.hotkeyManager.defineHotkeys)
            control.newValue.connect(self.beamline.wait)
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

class Control(QtGui.QWidget):
    newHotKeys = QtCore.Signal(dict)
    newValue = QtCore.Signal()
    def __init__(self,voltage):
        super(Control,self).__init__()
        self.voltage = voltage
        
        self.label = QtGui.QLabel(str(voltage.name))
        
        self.hotkeyButton = QtGui.QPushButton('H')
        self.hotkeyButton.setMaximumWidth(25)
        self.hotkeyButton.clicked.connect(self.makeHotkeys)

        self.set = Spin(text=str(voltage.setpoint))
        self.set.sigValueChanging.connect(self.valueChanged)
        
        self.readback = ReadBack(str(voltage.readback))
        
        self.init_UI()

    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(self.label,0,0,1,1)
        self.layout.addWidget(self.hotkeyButton,0,1,1,1)
        self.layout.addWidget(self.set,1,0,1,2)
        self.layout.addWidget(self.readback,2,0,1,2)

    def valueChanged(self):
        self.voltage.setpoint = self.set.value
        self.newValue.emit()

    def update(self):
        if self.voltage.ramping:
            if not self.set.value == self.voltage.rampSet:
                self.set.value = self.voltage.rampSet
        else:
            if not self.set.value == self.voltage.setpoint:
                self.set.value = self.voltage.setpoint

        self.readback.setText(str(self.voltage.readback))
                
        if abs(self.voltage.setpoint - self.voltage.readback) > MAX_OFFSET:
            self.setStyleSheet("ReadBack { background-color: red; }")
        elif abs(self.voltage.rampSet - self.voltage.readback) > MAX_OFFSET:
            self.setStyleSheet("ReadBack { background-color: yellow; }")
        else:
            self.setStyleSheet("ReadBack { background-color: green; }")

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

class ScanControl(QtGui.QWidget):
    def __init__(self,voltage):
        super(ScanControl,self).__init__()
        self.voltage = voltage

        self.name = QtGui.QLabel(self.voltage.name)

        self.startBox = pg.SpinBox(value=0,
                              min = 0, max = 10**4,
                              step = 1)
        self.stopBox = pg.SpinBox(value=10**4,
                              min = 0, max = 10**4,
                              step = 1)
        self.stepSizeBox = pg.SpinBox(value=100,
                              min = 0, max = 10**4,
                              step = 1)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(self.name,0,0)
        layout.addWidget(QtGui.QLabel("From:"),1,0)
        layout.addWidget(self.startBox,2,0)
        layout.addWidget(QtGui.QLabel("To:"),1,1)
        layout.addWidget(self.stopBox,2,1)
        layout.addWidget(QtGui.QLabel("Steps:"),1,2)
        layout.addWidget(self.stepSizeBox,2,2)


    def update(self):
        if self.voltage.scanning:
            self.setStyleSheet("ScanControl {border: 20px solid black;}")
        else:
            self.setStyleSheet("")

    def defineScan(self):
        self.voltage.scanStepsize = self.stepSizeBox.value()
        self.voltage.scanStart = self.startBox.value()
        self.voltage.scanStop = self.stopBox.value() + self.voltage.scanStepsize



class Spin(QtGui.QLineEdit):
    sigValueChanging = QtCore.pyqtSignal()
    def __init__(self,*args,**kwargs):
        super(Spin,self).__init__(*args,**kwargs)

        self._value = int(self.text())

        self.min = 0
        self.max = 10**4

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self,val):
        val = int(val)
        val = max(self.min,val)
        val = min(self.max,val)
        self._value = val

        l = len(self.text())
        pos = self.cursorPosition()
        self.setText(str(self.value))
        if l < len(self.text()):
            pos = pos + 1
        elif l < len(self.text()): 
            pos = pos - 1
        self.setCursorPosition(pos)

    def setText(self,text):
        self._value = int(text)
        super(Spin,self).setText(text)

    def keyPressEvent(self,e):
        text = self.text()
        if e.key() == QtCore.Qt.Key_Up or e.key() == QtCore.Qt.Key_Down:
            pos = self.cursorPosition()
            change = 10**(len(self.text())-pos)
            if e.key() == QtCore.Qt.Key_Down:
                change = - change

            self.value = self.value + change
        
        else:
            super(Spin,self).keyPressEvent(e)

        if not text == self.text():
            self.value = self.text()
            self.sigValueChanging.emit()

class ReadBack(QtGui.QLineEdit):
    def __init__(self,*args,**kwargs):
        super(ReadBack,self).__init__(*args,**kwargs)