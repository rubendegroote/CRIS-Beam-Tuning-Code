from PyQt4 import QtCore,QtGui
import pyqtgraph as pg
import multiprocessing as mp
import os

MAX_OFFSET = 5

class ControlsGroup(QtGui.QWidget):
    def __init__(self,beamline):
        super(ControlsGroup, self).__init__()
        self.beamline = beamline

        self.controls = {}
        self.controlHotkeys = {}
        self.optimizers = []

        self.init_UI()

    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)

        for i,(n,v) in enumerate(self.beamline.voltages.items()):
            control = Control(v)
            control.newHotKeys.connect(self.defineHotkeys)
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
        subset = [n for (n,c) in self.controls.items() if c.checked()]
        self.showOptimizer(subset)

    def showOptimizer(self,subset):
        from optimizer import Optimizer

        self.optimizers.append(Optimizer(parent=self,beamline=self.beamline,
                    subset=subset))

    def defineHotkeys(self,hotkeys):
        toDelete = []
        for control,hk in self.controlHotkeys.items():
            for hk2 in hotkeys.keys():
                if hk2 in hk.keys():
                    toDelete.append(control)
                    QtGui.QMessageBox.warning(self, "Hotkey Conflict",
                        """Hotkey conflict. Removed keys for {}.""".format(control.voltage.name,))

                    break

        for td in toDelete:
            del self.controlHotkeys[td]

        self.controlHotkeys[self.sender()] = hotkeys

    def keyPressed(self,key):
        for control,hotkeys in self.controlHotkeys.items():
            if key.key() in hotkeys:
                if hotkeys[key.key()] == "Increase Voltage":
                    control.increase()
                elif hotkeys[key.key()] == "Decrease Voltage":
                    control.decrease()
                elif hotkeys[key.key()] == "Increase Stepsize":
                    control.increaseStep()
                elif hotkeys[key.key()] == "Decrease Stepsize":
                    control.decreaseStep()

class Control(QtGui.QWidget):
    newHotKeys = QtCore.Signal(dict)
    def __init__(self,voltage):
        super(Control,self).__init__()
        self.voltage = voltage
        self.step = 1
        self.check = QtGui.QCheckBox(str(voltage.name))
        self.set = pg.SpinBox(value=voltage.setpoint,
                              min = 0, max = 10**4,
                              step = 1)
        self.set.sigValueChanging.connect(self.valueChanged)
        self.readback = QtGui.QLineEdit(str(voltage.readback))
        self.init_UI()

    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)
        self.layout.addWidget(self.check,0,0)
        self.layout.addWidget(self.set,1,0)
        self.layout.addWidget(self.readback,2,0)

    def increase(self):
        self.set.setValue(self.set.value() + self.step)
    
    def decrease(self):
        self.set.setValue(self.set.value() - self.step)

    def increaseStep(self):
        self.step =  min(10**3,self.step*10)
    
    def decreaseStep(self):
        self.step = max(1,self.step/10)

    def checked(self):
        return self.check.checkState()

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

    def mouseDoubleClickEvent(self,e):
        from hotkey import HotkeyPrompt
        hotkeys = HotkeyPrompt.hotkeys(parent=self)
        hotkeys = dict(zip(hotkeys.values(),hotkeys.keys()))
        self.newHotKeys.emit(hotkeys)

