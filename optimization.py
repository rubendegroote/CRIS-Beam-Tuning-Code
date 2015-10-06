import numpy as np
import lmfit as lm
import time
import emcee
from bayes_opt import BayesianOptimization

class Optimizer(object):
    def __init__(self,beamline):
        super(Optimizer,self).__init__()
        self.beamline = beamline

    def start(self,subset,method):
        if method == 'bayes':
            self.defineBounds(subset)
            self.optimizeBayes()       
        elif method == 'my mcmc':
            self.defineParameters(subset)
            self.optimizeMyMCMC()  
        else:
            self.defineParameters(subset)
            self.optimizeMCMC()  

    def defineParameters(self,subset):
        self.p = lm.Parameters()
        for n in subset:
            self.p.add(n, value = self.beamline.voltages[n].setpoint,
                                    min = self.beamline.voltages[n].scanStart,
                                    max = self.beamline.voltages[n].scanStop,
                                    vary = True)

    def defineBounds(self,subset):
        self.bounds = {}
        for n in subset:
            self.bounds[n] = (self.beamline.voltages[n].scanStart,self.beamline.voltages[n].scanStop)

    def optimizeBayes(self):
        self.bayesianOptimizer = BayesianOptimization(self.optimizationFunctionBayes, self.bounds)
        self.bayesianOptimizer.maximize(n_iter=200,nugget = 0.02)

    def optimizeMCMC(self):
        ndim, nwalkers = len(self.p),2*len(self.p)
        pos = [np.array([p.value for p in self.p.values()]) + 1e-4*np.random.rand(ndim) for i in range(nwalkers)]
        sampler = emcee.EnsembleSampler(nwalkers, ndim, self.optimizationFunctionMCMC)
        sampler.run_mcmc(pos, N = 2000)

    def optimizeMyMCMC(self):
        from walker import Walkers
        ndim, nwalkers = len(self.p),10*len(self.p)
        pos = [p.value for p in self.p.values()]
        w = Walkers(nwalkers,pos,10,1,self.optimizationFunctionMyMCMC)
        print('done')
        while self.beamline.continueScanning:
            w.walk_all()


    def optimizationFunctionBayes(self,vrs,):
        
        for n,v in zip(self.p.keys(),vrs):
            self.beamline.voltages[n].setpoint = v
        
        self.beamline.wait()
        self.beamline.wait() # Not sure why, but convergence works better with two waits?

        current = self.beamline.current.value

        print(current)

        return current

    def optimizationFunctionMCMC(self,vrs,):
        for v in vrs:
            if v < 0 or v > 10**4:
                return -np.inf

        for n,v in zip(self.p.keys(),vrs):
            self.beamline.voltages[n].setpoint = v

        
        self.beamline.wait()
        self.beamline.wait() # Not sure why, but convergence works better with two waits?

        time.sleep(0.05)

        current = self.beamline.current.value

        if current < 10**-9:
            return -np.inf

        return np.log(current)

    def optimizationFunctionMyMCMC(self,vrs,):
        for v in vrs:
            if v < 0 or v > 10**4:
                return -np.inf

        for n,v in zip(self.p.keys(),vrs):
            self.beamline.voltages[n].setpoint = v

        
        self.beamline.wait()
        self.beamline.wait() # Not sure why, but convergence works better with two waits?

        time.sleep(0.05)

        current = self.beamline.current.value
        std = self.beamline.current_std.value 

        return (current,std)