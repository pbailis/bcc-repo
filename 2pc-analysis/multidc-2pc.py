
from multidc_common import lats
from random import random
from pylab import *

TRIALS = 10000


matplotlib.rcParams['figure.figsize'] = 5, 4
matplotlib.rcParams['lines.linewidth'] = 1


regions = ["virgina",
           "oregon",
           "california",
           "ireland",
           "saopaulo",
           "tokyo",
           "singapore",
           "sydney"]

pctile =  [i/1000. for i in range(0, 1001)]

def gen_delay(from_region, to_region):
    chosen_pct = random()
    chosen_bin = len(pctile)-1
    for i in range(0, len(pctile)):
        if pctile[i] > chosen_pct:
            chosen_bin = i-1
            break
            
    minpct = pctile[chosen_bin]
    maxpct = pctile[chosen_bin+1]
    minpctvalue = lats[from_region][to_region][chosen_bin]
    maxpctvalue = lats[from_region][to_region][chosen_bin+1]
        
    maxpctproportion = (chosen_pct-minpct)/float(maxpct-minpct)
    return minpctvalue*(1-maxpctproportion)+maxpctvalue*maxpctproportion

def gen2pc(home, others):
    time = 0
    prepares = []
    for other in others:
        if other == home:
            continue
        prepares.append(gen_delay(home, other)+gen_delay(other, home))
    time += max(prepares)
    commits = []
    for other in others:
        if other == home:
            continue
        commits.append(gen_delay(home, other))
    time += max(commits)
    return time

def find_closest_dc(dc):
    mindc = None
    mindctime = None
    
    for other in lats[dc]:
        if mindc is None or lats[dc][0] < mindctime:
            mindc = other
            mindctime = lats[dc][0]

    return mindc

def gendc2pc(home, others):
    prepares = []
    for preparer in others:
        if home==preparer:
            preparetime = 0
        else:
            preparetime = gen_delay(home, preparer)

        for committer in others:
            if preparer != committer:
                prepares.append(preparetime+gen_delay(preparer, committer))
    return max(prepares)

def average(lst):
    return sum(lst)/float(len(lst))


dctwopcstds = []
dctwopcthrus = []

for i in range(2, len(regions)+1):
    latencies = []
    print regions[:i]
    for it in range(0, TRIALS):
        latencies.append(gendc2pc("virgina", regions[:i]))
        
    dctwopcthrus.append(1000./average(latencies))
    dctwopcstds.append(1000./std(latencies))

plot(dctwopcthrus, 's-', label="2 delays")

twopcstds = []
twopcthrus = []

for i in range(2, len(regions)+1):
    latencies = []
    print regions[:i]
    for it in range(0, TRIALS):
        latencies.append(gen2pc("virgina", regions[:i]))
        
    twopcthrus.append(1000./average(latencies))
    twopcstds.append(1000./std(latencies))

plot(twopcthrus, 'o-', label="3 delays")

legend(loc="upper right")

xticks(range(0, 7), ["+OR", "+CA", "+IR", "+SP", "+TO", "+SI", "+SY"])
xlabel("Participating Datacenters (+VA)")
ylabel("Maximum Throughput (txn/s)")
title("Multi-Datacenter Throughput")

savefig("multidc-twopc.pdf",  bbox_inches='tight', pad_inches=.1)
