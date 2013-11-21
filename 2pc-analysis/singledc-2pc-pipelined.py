import matplotlib
from random import random, expovariate
from pylab import *

matplotlib.rcParams['figure.figsize'] = 5, 4
matplotlib.rcParams['lines.linewidth'] = 1


TRIALS = 10000
MIN_NODES=2
MAX_NODES = 20


ms=6
lw=1
padInches=0.05

matplotlib.rcParams['figure.figsize'] = 3.5, 1.7
matplotlib.rcParams['lines.linewidth'] = lw
matplotlib.rcParams['axes.linewidth'] = lw   
matplotlib.rcParams['lines.markeredgewidth'] = lw
matplotlib.rcParams['font.size'] = 8
matplotlib.rcParams['font.weight'] = 'normal'

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

MODELS = [BobtailLatency()]#ExponentialLatency(4), ExponentialLatency(2), ExponentialLatency(1),  ExponentialLatency(.5), BobtailLatency()]



ctimes = {}

def setup_2pc(numnodes):
    global ctimes
    for node in range(0, max(NODELIST)):
        ctimes[node] = 0

# need to calculate max(sender to other + other to others) N^2-1 delays
def gen2pc_classic(numnodes, model):
    prev = max(ctimes.values())
    for i in range(1, numnodes):
        #prepared
        ctimes[i] += model.gen_delay()
    #commit
    prepared_time = max(ctimes.values())
    for i in range(1, numnodes):
        ctimes[i] = prepared_time+model.gen_delay()

    return max(ctimes.values())

def gen2pc_decent(numnodes, model):
    time = 0
    global ctimes
    prev_ctimes = ctimes
    ctimes = {}

    for i in range(0, numnodes):
        commitwait = []
        for j in range(0, numnodes):
            if i == j:
                continue
            commitwait.append(prev_ctimes[j]+model.gen_delay())
        
        ctimes[i] = max(commitwait)

    return max(ctimes.values())

def average(lst):
    return sum(lst)/float(len(lst))

for model in MODELS:
    print model.name()
    NODELIST = range(MIN_NODES, MAX_NODES)
    stds = []
    thrus = []

    for nodes in NODELIST:
        setup_2pc(nodes)
        for it in range(0, TRIALS):
            time = gen2pc_decent(nodes, model)
        thrus.append(float(TRIALS)/time*1000)

    plot([i+1 for i in NODELIST], thrus,  's-', color="green", markeredgecolor="green", markerfacecolor='None', label="2 delays", markersize=ms)

    thrus = []

    for nodes in NODELIST:
        setup_2pc(nodes)
        for it in range(0, TRIALS):
            time = gen2pc_classic(nodes, model)
        
        print nodes, time
        thrus.append(float(TRIALS)/time*1000)

    plot([i+1 for i in NODELIST], thrus,'o-', color="blue", markeredgecolor="blue", markerfacecolor='None', label="3 delays", markersize=ms)


ylabel("Maximum Throughput (txns/s)")
xlabel("Number of Servers in 2PC")
legend(loc="upper right", numpoints=2, frameon=False, handlelength=2)
savefig("singledc-twopc.pdf", transparent=False, bbox_inches='tight', pad_inches=.1)
