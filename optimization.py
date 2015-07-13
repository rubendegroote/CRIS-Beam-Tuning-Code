import numpy as np
import lmfit as lm
import time
from bayes_opt import BayesianOptimization

class Optimizer(object):
    def __init__(self,beamline):
        super(Optimizer,self).__init__()
        self.beamline = beamline

    def start(self,subset,method):
        if method == 'chisq':
            self.defineParameters(subset)
            self.optimizeChisq()
        else:
            self.defineBounds(subset)
            self.optimizeBayes()       

    def defineParameters(self,subset):
        self.p = lm.Parameters()
        for n in subset:
            self.p.add(n, value = self.beamline.voltages[n].setpoint,
                                    min = self.beamline.voltages[n].scanStart,
                                    max = self.beamline.voltages[n].scanStop,
                                    vary = True)

    def optimizeChisq(self):
        result = lm.minimize(self.optimizationFunctionChisq, self.p,method='Nelder-Mead')
        lm.report_fit(self.p)

    def defineBounds(self,subset):
        self.bounds = {}
        for n in subset:
            self.bounds[n] = (self.beamline.voltages[n].scanStart,self.beamline.voltages[n].scanStop)

    def optimizeBayes(self):
        self.bayesianOptimizer = BayesianOptimization(self.optimizationFunctionBayes, self.bounds)
        self.bayesianOptimizer.maximize(n_iter=100)

    def optimizationFunctionChisq(self,p):
        for par in p.values():
            self.beamline.voltages[par.name].setpoint = par.value
        
        self.beamline.wait()
        self.beamline.wait() # Not sure wy, but convergence works better with two waits?

        current = 1-self.beamline.current.value

        print(current)

        return current

    def optimizationFunctionBayes(self,p):
        for n,par in p.items():
            self.beamline.voltages[n].setpoint = par
        
        self.beamline.wait()
        self.beamline.wait() # Not sure why, but convergence works better with two waits?

        current = self.beamline.current.value

        print(current)

        return current