
from multidc_common import lats
from random import random
from pylab import *

TRIALS = 100000

ms=6
lw=1
padInches=0.05

matplotlib.rcParams['figure.figsize'] = 3.5, 1.7
matplotlib.rcParams['lines.linewidth'] = lw
matplotlib.rcParams['axes.linewidth'] = lw   
matplotlib.rcParams['lines.markeredgewidth'] = lw
matplotlib.rcParams['font.size'] = 8
matplotlib.rcParams['font.weight'] = 'normal'


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

def find_closest_dc(dc):
    mindc = None
    mindctime = None
    
    for other in lats[dc]:
        if mindc is None or lats[dc][0] < mindctime:
            mindc = other
            mindctime = lats[dc][0]

    return mindc


dctimes = {}

def setup_2pc_classic():
    global dctimes
    for region in regions:
        dctimes[region] = 0

# 3rtt 2pc -- classic
def gen2pc_classic(home, others):
    prepares = []
    for preparer in others:
        if preparer == home:
            continue
        #prepare
        dctimes[preparer] += gen_delay(preparer, home)
    prepared_time = max(dctimes.values())
    for preparer in others:
        if preparer == home:
            continue
        #commit
        dctimes[preparer] = prepared_time+gen_delay(home, preparer)

    return max(dctimes.values())

dctimes = {}

def setup_2pc_decent():
    global dctimes
    for region in regions:
        dctimes[region] = 0

# 2rtt 2pc -- decentralized
def gendc2pc_decent(regions):
    global dctimes
    prev_dctimes = dctimes
    dctimes = {}
    for s1 in regions:
        committime = []
        for s2 in regions:
            if s1 == s2:
                continue
            committime.append(prev_dctimes[s2]+gen_delay(s2, s1))
        dctimes[s1] = max(prev_dctimes[s1], max(committime))

    return max(dctimes.values())


def average(lst):
    return sum(lst)/float(len(lst))


dctwopcstds = []
dctwopcthrus_decent = []

for i in range(2, len(regions)+1):
    latencies = []
    print regions[:i]
    setup_2pc_decent()
    for it in range(0, TRIALS):
        time = gendc2pc_decent(regions[:i])
    print "DECENT", len(regions), float(TRIALS)/time*1000, time/float(TRIALS)
    dctwopcthrus_decent.append(float(TRIALS)/time*1000)

plot(dctwopcthrus_decent, 's-', color="green", markeredgecolor="green", markerfacecolor='None', label="D-2PC", markersize=ms)

twopcstds = []
classictwopcthrus = []

for i in range(2, len(regions)+1):
    latencies = []
    print regions[:i]
    setup_2pc_classic()
    for it in range(0, TRIALS):
        time = gen2pc_classic("virgina", regions[:i])

    print "CLASSIC", len(regions), float(TRIALS)/time*1000, time/float(TRIALS)
    classictwopcthrus.append(float(TRIALS)/time*1000)


plot(classictwopcthrus, 'o-', color="blue", markeredgecolor="blue", markerfacecolor='None', label="C-2PC", markersize=ms)

legend(loc="upper right", numpoints=2, frameon=False, handlelength=2)

xticks(range(0, 7), ["+OR", "+CA", "+IR", "+SP", "+TO", "+SI", "+SY"])
xlabel("Participating Datacenters (+VA)")
ylabel("Maximum Throughput (txn/s)")

subplots_adjust(bottom=.1, right=0.95, top=0.9, left=.1)

savefig("multidc-twopc.pdf",  bbox_inches='tight', pad_inches=.1)
