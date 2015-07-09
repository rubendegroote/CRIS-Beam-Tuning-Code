import time
import numpy as np
import threading as th
from PyQt4 import QtCore,QtGui
from collections import OrderedDict
import multiprocessing as mp
import pandas as pd
from copy import deepcopy

RAMP = 10**3

class Beamline(object):
    def __init__(self):
        super(Beamline,self).__init__()
        
        self.iQ = mp.Queue()
        self.current = mp.Value('d',0.0)
        self.stamp = mp.Value('d',0.0)
        self.voltages = Voltages()
        self.manager = mp.Manager()
        self.readback = self.manager.dict()
        for i in range(10):
            name = 'Control {}'.format(str(i))
            self.voltages[name] = Voltage(name=name)
            self.readback[name] = 0

        self.last = 0
        self.max = 0
        self.optimalTime = time.time()
        self.optimalSettings = self.voltages

        self.data = pd.DataFrame()
        
        self.makeControlProcess()

    def makeControlProcess(self):
        self.controlProcess = mp.Process(target = controlLoop, 
            args = (self.iQ,self.readback,self.current,self.stamp,))
        self.controlProcess.start()

    def update(self):
        self.sendInstructions()
        
        self.save()

        self.voltages.readback=self.readback

        if not self.current.value == self.last:
            self.last = self.current.value
            self.lastTime = self.stamp.value

        if self.last>self.max:
            self.max = self.last
            self.optimalTime = self.lastTime
            self.optimalSettings = self.voltages.readback

    def setToOptimal(self):
        self.voltages.setpoints = self.optimalSettings

    def save(self):
        data = self.voltages.asDataFrame()
        data['current'] = self.current.value
        data['time'] = self.stamp.value
        # with pd.get_store('tuning_stream.h5') as store:
        #     store.append(data)

    def sendInstructions(self):
        instruction = {n:v.setpoint for n,v in self.voltages.items() if v.changed}
        if len(instruction)>0:
            self.iQ.put(instruction)
            for n in instruction:
                self.voltages[n].changed = False

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
        self.status = 'green'

    @property
    def readback(self):
        return int(self._readback)

    @readback.setter
    def readback(self,r):
        self._readback = int(r)

    @property
    def setpoint(self):
        return int(self._setpoint)

    @setpoint.setter
    def setpoint(self,s):
        if self._ramping:
            self.stopRamp = True
            time.sleep(0.01)
        self.rampThread = th.Thread(target=self.rampTo,args=(int(s),))
        self.rampThread.start()

    @property
    def rampSet(self):
        return self._rampSet

    @property
    def ramping(self):
        return self._ramping

    def rampTo(self,s):
        self._rampSet = s
        self._ramping = True
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

def controlLoop(iQ,readback,current,stamp):

    setpoints = {n:0 for n in readback.keys()}
    r0 = np.random.randint(10**4,size=10)

    while True:
        try:
            changes = iQ.get_nowait()
            for n,c in changes.items():
                setpoints[n] = c

                #also change hardware here

        except:
            pass

        for n in readback.keys():
            readback[n] = setpoints[n] + np.random.rand()
        
        curr = 1

        for i,r in enumerate(readback.values()):
            curr *= (1 - (r-r0[i])**2/10**8)

        current.value = curr

        stamp.value = time.time()

        time.sleep(0.01)

