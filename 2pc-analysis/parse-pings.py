
regions = ["virgina",
           "oregon",
           "california",
           "ireland",
           "singapore",
           "tokyo",
           "sydney",
           "saopaulo"]

sec_per_week=604800

def avg(d):
    return sum(d)/float(len(d))

def get_pctile(d, pct):
    if pct == 1:
        return max(d)
    return d[int(pct*len(d))]
    

def fetchTimes(f):
    results = []

    starttime = None

    for line in open(f):
        linesp = line.split()
        if linesp[1] != "64":
            #if linesp[1] != "PING":
                #print line
            continue
        time = int(linesp[0][:-1])
        if starttime is None:
            starttime = time

        results.append(float(linesp[8].split("=")[1]))

        if time-starttime >= sec_per_week:
            results.sort()
            return results

    print "DID NOT GET A WEEK OF DATA!"

def getData(locs):
    pctiles = [i/1000. for i in range(0, 1001)]

    print "lats={"
    for loca in locs:
        print '"'+loca+'":{'
        for locb in locs:
            if loca == locb:
                continue

            result = fetchTimes("%s-%s-times.txt" % (loca, locb))
            pcts = []
            for pct in pctiles:
                pcts.append(get_pctile(result, pct))
            print "\""+locb+"\":"+str(pcts)+","

            
        print "},"
    print "}"
getData(regions)



