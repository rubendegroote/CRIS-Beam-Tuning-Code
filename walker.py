import numpy as np
import pylab as pl
from scipy.stats import norm

def compare(X,Y):
    mu = -(X[1]-Y[1])
    sigma = (Y[1]**2 + X[1]**2)**0.5
    return np.random.rand() > (1 - norm.cdf(mu / sigma))

def compare_2(X,Y):
    return (X[1]-Y[1]) > 0

class Walker:
    def __init__(self,p0,step,f):
        self.points = [p0]
        self.attempts = [p0]
        self.step = step
        self.dim = len(p0)
        self.f = f
    
        self.no_of_steps = 0

        self.maxima = [self.f(self.points[-1])]
        self.evals = []
        self.best = self.maxima[-1]

        self.compare = compare
    
    def walk(self):
        self.p = self.points[-1] + self.random_step()
        self.no_of_steps += 1
        self.decide()

    def random_step(self):
        return np.random.normal(0,self.step,size=self.dim)

    def decide(self):
        self.new = self.f(self.p)
        self.attempts = np.concatenate((self.attempts,[self.p]),axis=0)
        self.evals.append(self.new)

        if self.compare(self.new,self.best):
            self.reject()
        else:
            self.best = self.new
            self.accept()

    def accept(self):
        self.maxima.append(self.new)
        self.add_point(self.p)
        self.acceptance = len(self.maxima) / self.no_of_steps

    def reject(self):
        self.acceptance = len(self.maxima) / self.no_of_steps
        
    def add_point(self,p):
        self.points = np.concatenate((self.points,[p]),axis=0)

    def jump_to_other(self,walker):
        self.add_point(walker.points[-1])
        # self.step = walker.step

class Walkers(list):
    def __init__(self,number,p0,size,step,func):
        super(Walkers,self).__init__()
        for i in range(number):
            p = np.random.randint(-size,size,size=len(p0)) + p0
            s = abs(np.random.normal(0,step))
            self.append(Walker(p,s,func))
            if i%2 == 0:
                self[-1].compare = compare_2
        self.maximum = (0,0)
        self.steps = 0 

    def walk_all(self):
        self.steps += 1
        for w in self:
            w.walk()

        best = max([w.best for w in self])
        if compare(best,self.maximum):
            self.maximum = best
        
        self.jump_walkers()

        # if self.steps % 100 == 0:
        #     attempts = self.attempts()
        #     for i in range(len(attempts.T)):
        #         pl.hist(attempts.T[i],bins = 40)
        #     pl.show()

    def best_walker(self):
        return self[np.argmax([w.best[0] for w in self])]

    def points(self):
        return np.concatenate([w.points for w in self])

    def attempts(self):
        return np.concatenate([w.attempts for w in self])

    def jump_walkers(self):
        print('jumping')
        best_walker = self.best_walker()
        for w in self:
            if compare(best_walker.best,w.best):
                w.jump_to_other(best_walker)


