import numpy as np
import lmfit as lm
import time


class Optimizer(object):
    def __init__(self,beamline):
        super(Optimizer,self).__init__()
        self.beamline = beamline

    def start(self,subset):
        self.defineParameters(subset)

    def defineParameters(self,subset):
        self.p = lm.Parameters()
        for n in subset:
            self.p.add(n, value = self.beamline.voltages[n].setpoint,
                                    min = self.beamline.voltages[n].scanStart,
                                    max = self.beamline.voltages[n].scanStop,
                                    vary = True)

        result = lm.minimize(self.optimizationFunction, self.p,method='Nelder-Mead')
        lm.report_fit(self.p)

    def optimizationFunction(self,p):
        for par in p.values():
            self.beamline.voltages[par.name].setpoint = par.value
        
        self.beamline.wait()

        current = 1-self.beamline.current.value
        # current = 1
        # for i,r in enumerate(self.beamline.voltages.setpoints.values()):
        #     current *= (1 - (r-5000)**2/10**8)

        print(current)

        return current