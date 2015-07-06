import time
import numpy as np
import threading as th
from PyQt4 import QtCore,QtGui

RAMP = 100

class Voltage(object):
    def __init__(self,name,value=0):
        super(Voltage,self).__init__()
        self.name = name
        self.changed = False
        self.readback = 0
        self._setpoint = 0

        self.stopRamp = False
        self._ramping = False
        self._rampSet = 0
        self.status = 'green'

    @property
    def setpoint(self):
        return self._setpoint

    @setpoint.setter
    def setpoint(self,s):
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
        self._ramping = True
        while abs(self._setpoint - s) > RAMP and not self.stopRamp:
            self._setpoint = self._setpoint + \
                    np.sign(s-self._setpoint) * RAMP
            self.changed = True

            time.sleep(1.0)

        if not self.stopRamp:
            self._setpoint = s
            self.changed = True
            

        self._ramping = False



def controlLoop(iQ,readback):

    setpoints = {n:0 for n in readback.keys()}

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

        time.sleep(0.1)