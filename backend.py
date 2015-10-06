import time
import numpy as np
import threading as th
from PyQt4 import QtCore,QtGui
from collections import OrderedDict, deque
import multiprocessing as mp
import pandas as pd
from copy import deepcopy
from optimization import Optimizer

RAMP = 10**4

class Beamline(object):
    def __init__(self):
        super(Beamline,self).__init__()
        self.voltages = Voltages()
        
        self.manager = mp.Manager()
        self.current = mp.Value('d',0.0)
        self.current_std = mp.Value('d',0.0)
        self.stamp = mp.Value('d',0.0)
        self.readback = self.manager.dict()
        self.setpoints = self.manager.dict()
        for i in range(10):
            name = 'Control_{}'.format(str(i))
            self.voltages[name] = Voltage(name=name)
            self.readback[name] = 0
            self.setpoints[name] = 0

        self.last = 0
        self.max = 0
        self.optimalTime = time.time()
        self.optimalSettings = self.voltages.setpoints

        self.continueScanning = False

        self.data = pd.DataFrame()

        self.optimizer = Optimizer(self)
        
        self.makeControlProcess()

        th.Timer(0,self.update).start()
        self.stop = False

    def makeControlProcess(self):
        self.controlProcess = mp.Process(target = controlLoop, 
            args = (self.setpoints,self.readback,self.current,self.current_std,self.stamp,))
        self.controlProcess.start()

    def update(self):
        for n,v in self.voltages.setpoints.items():
            self.setpoints[n]=v
            
        self.voltages.readback=self.readback

        self.save()
        if not self.current.value == self.last:
            self.last = self.current.value
            self.lastTime = self.stamp.value

        if self.last>self.max:
            self.max = self.last
            self.optimalTime = self.lastTime
            self.optimalSettings = self.voltages.readback

        if not self.stop:
            th.Timer(0.01,self.update).start()

    def wait(self):
        while any([v.ramping for v in self.voltages.values()]):
            time.sleep(0.001)

    def setToOptimal(self):
        self.voltages.setpoints = self.optimalSettings
        while any([v.ramping for v in self.voltages.values()]):
            time.sleep(0.05)

    def save(self):
        data = self.voltages.asDataFrame()
        data['current'] = self.current.value
        data['time'] = self.stamp.value
        # with pd.get_store('tuning_stream.h5') as store:
        #     store.append(data)

    def saveSettings(self,fileName):
        # Saves the settings to a .txt so they can easily be loaded next time.
        with open(fileName,'w') as f:
            for n,s in self.voltages.setpoints.items():
                f.write(n + ';' + str(s))
                f.write('\n')

    def loadSettings(self,filename):
        with open(filename,'r') as f:
            for line in f.readlines():
                name,value = line.split(';')
                self.voltages[name].setpoint = float(value)

    def startScan(self, subset):
        self.scanThread = th.Thread(target=self.scan,args=(subset,))
        self.scanThread.start()

    def stopScan(self):
        self.continueScanning = False
        for v in self.voltages.values():
            v.stopScan()

    def scan(self,subset):
        self.continueScanning = True
        for n,v in self.voltages.items():
            if not self.continueScanning:
                break

            if n in subset:
                self.scanVThread = th.Thread(target=v.scan)
                self.scanVThread.start()
                v.scanning = True
                while v.scanning:
                    time.sleep(0.1)
                self.setToOptimal()

    def optimize(self,subset,method):
        self.continueScanning = True
        self.optimizeThread = th.Thread(target=self.optimizer.start, args = (subset,method,))
        self.optimizeThread.start()

class Voltages(OrderedDict):
    def __init__(self):
        super(Voltages,self).__init__()

    @property
    def setpoints(self):
        return {n:v.setpoint for n,v in self.items()}

    @setpoints.setter
    def setpoints(self,setpoints):
        for n,r in setpoints.items():
            self[n].setpoint = r

    @property
    def readback(self):
        return {n:v.readback for n,v in self.items()}

    @readback.setter
    def readback(self,readback):
        for n,r in readback.items():
            self[n].readback = r

    def asDataFrame(self):
        data = []
        columns = []
        for k in self.keys():
            data.append(self.setpoints[k])
            columns.append(k + ' set')
            data.append(self.readback[k])
            columns.append(k + ' read')

        data = np.array(data).reshape((-1, len(columns)))

        return pd.DataFrame(data,columns=columns)

class Voltage(object):
    def __init__(self,name,value=0):
        super(Voltage,self).__init__()
        self.name = name
        self.changed = False
        self._readback = 0
        self._setpoint = value

        self.stopRamp = False
        self._ramping = False
        self._rampSet = 0

        self.scanning = False
        self.continueScanning = False
        self.scanStart = 0
        self.scanStop = 0
        self.scanStepsize = 0

        self.hasHotkeys = False
        self.step = 1

    @property
    def readback(self):
        return self._readback

    @readback.setter
    def readback(self,r):
        self._readback = r

    @property
    def setpoint(self):
        return self._setpoint

    @setpoint.setter
    def setpoint(self,s):
        if self._ramping:
            self.stopRamp = True
            time.sleep(0.01)
        self._ramping = True
        self.rampThread = th.Thread(target=self.rampTo,args=(s,))
        self.rampThread.start()

    @property
    def rampSet(self):
        return self._rampSet

    @property
    def ramping(self):
        return self._ramping

    def rampTo(self,s):
        self._rampSet = s
        self.stopRamp = False
        t0 = time.time()
        while abs(self._setpoint - s) > RAMP and not self.stopRamp:
            if time.time()-t0 > 1.0:
                self._setpoint = self._setpoint + \
                        np.sign(s-self._setpoint) * RAMP
                self.changed = True

                t0 = time.time()
    
            time.sleep(0.01)

        if not self.stopRamp:
            self._setpoint = s
            self.changed = True

        self._ramping = False

    def scan(self):
        self.continueScanning = True
        for r in np.arange(self.scanStart,self.scanStop,self.scanStepsize):
            if not self.continueScanning:
                break

            self.setpoint = r
            while self._ramping and self.continueScanning:
                time.sleep(0.05)
            time.sleep(1.0)

        self.scanning = False

    def stopScan(self):
        self.continueScanning = False

    def increase(self):
        self.setpoint = self.setpoint + self.step
    
    def decrease(self):
        self.setpoint = self.setpoint - self.step

    def increaseStep(self):
        self.step =  min(10**3,self.step*10)
    
    def decreaseStep(self):
        self.step = max(1,self.step/10)
