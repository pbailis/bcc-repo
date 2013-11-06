import matplotlib
from random import random, expovariate
from pylab import *

matplotlib.rcParams['figure.figsize'] = 5, 4
matplotlib.rcParams['lines.linewidth'] = 1


TRIALS = 10000
MIN_NODES=1
MAX_NODES = 20

class ExponentialLatency:
    def __init__(self, lmbda):
        self.lmbda = lmbda

    def name(self):
        return "Exponential, mean="+str(1./self.lmbda)+"ms"
    
    def gen_delay(self):
        return expovariate(self.lmbda)


class BobtailLatency:
    lats = [.28,.38, .43, .46, .5, .52, .54, .57, .6, .76, .85, 2.9, 3.4, 3.9, 4.6, 5.5, 6.6, 8, 10.2, 18, 30, 100]
    pctile = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, .95, .99, .991, .992, .993, .994, .995, .996, .997, .998, .999, 1]

    def name(self):
        return "Bobtail Intra-DC EC2"

    def gen_delay(self):
        chosen_pct = random()
        chosen_bin = len(self.pctile)
        for i in range(0, len(self.pctile)):
            if self.pctile[i] > chosen_pct:
                chosen_bin = i-1
                break

        minpct = self.pctile[chosen_bin]
        maxpct = self.pctile[chosen_bin+1]
        minpctvalue = self.lats[chosen_bin]
        maxpctvalue = self.lats[chosen_bin+1]
        
        maxpctproportion = (chosen_pct-minpct)/float(maxpct-minpct)
        return minpctvalue*(1-maxpctproportion)+maxpctvalue*maxpctproportion

MODELS = [ExponentialLatency(4), ExponentialLatency(2), ExponentialLatency(1),  ExponentialLatency(.5), BobtailLatency()]


# need to calculate max(sender to other + other to others) N^2-1 delays

def gen2pc(numnodes, model):
    time = 0
    prepares = []
    for i in range(0, numnodes):
        basedelay = model.gen_delay()
        for i in range(0, numnodes+1):
            prepares.append(basedelay+model.gen_delay())
    return max(prepares)

def average(lst):
    return sum(lst)/float(len(lst))

for model in MODELS:
    print model.name()
    NODELIST = range(MIN_NODES, MAX_NODES)
    stds = []
    thrus = []

    for nodes in NODELIST:
        latencies = []
        for it in range(0, TRIALS):
            latencies.append(gen2pc(nodes, model))
        print nodes, average(latencies), 1000./average(latencies), 1000./std(latencies)
        thrus.append(1000./average(latencies))
        stds.append(1000./std(latencies))
        
    plot([i+1 for i in NODELIST], thrus, label=model.name())

ylabel("Maximum Throughput (txns/s)")
xlabel("Number of Servers in 2PC")
legend(loc="upper right")
savefig("2md-thrus.png", transparent=True, bbox_inches='tight', pad_inches=.1)
