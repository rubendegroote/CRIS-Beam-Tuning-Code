from PyQt4 import QtCore,QtGui
import pyqtgraph as pg
import multiprocessing as mp
from backend import Voltage,controlLoop
from collections import OrderedDict

MAX_OFFSET = 5

class ControlsGroup(QtGui.QWidget):
    def __init__(self):
        super(ControlsGroup, self).__init__()
        self.controls = {}

        self.manager = mp.Manager()
        self.voltages = OrderedDict()
        self.readback = self.manager.dict()
        for i in range(10):
            name = 'Control {}'.format(str(i))
            self.voltages[name] = Voltage(name=name)
            self.readback[name] = 0

        self.iQ = mp.Queue()
        self.makeControlProcess()

        self.init_UI()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def init_UI(self):
        self.layout = QtGui.QGridLayout(self)

        for i,(n,v) in enumerate(self.voltages.items()):
            control = Control(v)
            self.controls[n] = control
            self.layout.addWidget(control,i%2,i//2)

    def save(self):
        for control in self.controls:
            print(control.name,control.set.value())

    def load(self):
        pass

    def optimize(self):
        subset = {n:self.voltages[n] for (n,c) in self.controls.items() if c.checked()}
        self.showOptimizer(subset)

    def showOptimizer(self,voltages):
        from optimizer import Optimizer

        ok,optimized = Optimizer.optimize(parent=self,voltages=voltages)
        if ok:
            print(optimized)

    def update(self):

        self.sendInstructions()

        for n,v in self.readback.items():
            self.voltages[n].readback=v

        for c in self.controls.values():
            c.update()

    def makeControlProcess(self):
        self.controlProcess = mp.Process(target = controlLoop, 
            args = (self.iQ,self.readback))
        self.controlProcess.start()

    def sendInstructions(self):
        instruction = {n:v.setpoint for n,v in self.voltages.items() if v.changed}
        if len(instruction)>0:
            self.iQ.put(instruction)
            for n in instruction:
                self.voltages[n].changed = False

    def keyPressed(self,key):
        if key =='R':
            self.controls[self.controls.keys()[0]].set.setValue(
                self.controls[self.controls.keys()[0]].set.value() + 1)
        elif key =='F':
            self.controls[self.controls.keys()[0]].set.setValue(
                self.controls[self.controls.keys()[0]].set.value() - 1)
        elif key =='D':
            self.controls[self.controls.keys()[1]].set.setValue(
                self.controls[self.controls.keys()[1]].set.value() - 1)
        elif key =='E':
            self.controls[self.controls.keys()[1]].set.setValue(
                self.controls[self.controls.keys()[1]].set.value() + 1)



class Control(QtGui.QWidget):
    def __init__(self,voltage):
        super(Control,self).__init__()
        self.voltage = voltage
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
