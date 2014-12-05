
now = datetime.datetime.utcnow()
vals = [{
    "start": now,
    "end": now + datetime.timedelta(hours=1),
    "repeat_interval": 60 * 60 * 24,
    "cutoff": now + datetime.timedelta(days=3)
},      {
    "start": now + datetime.timedelta(days=1, hours=5),
    "end": now + datetime.timedelta(days=1, hours=7),
    "repeat_interval": 60 * 60 * 24,
    "cutoff": now + datetime.timedelta(days=4, hours=5)
}]

cand1 = now - datetime.timedelta(minutes=35)
cand2 = now + datetime.timedelta(minutes=35)
cand3 = now + datetime.timedelta(days=1, minutes=30)
cand4 = now + datetime.timedelta(days=1, minutes=61)
cand5 = now + datetime.timedelta(days=3, minutes=1)

def isValid(time_ref):
    curr = vals["start"]
    curr_end = vals["end"]
    while time_ref < vals["cutoff"]:
        print "iteration"
        if time_ref < curr:
            return False
        elif time_ref < curr_end:
            return True
        else:
            curr += datetime.timedelta(seconds=vals["repeat_interval"])
            curr_end += datetime.timedelta(seconds=vals["repeat_interval"])

    if time_ref > vals["cutoff"]:
        return False


assert(not isValid(cand1))
assert(isValid(cand2))
assert(isValid(cand3))
assert(not isValid(cand4))
assert(not isValid(cand5))


def isValidOpt(time_ref):
    curr = vals["start"]
    curr_end = vals["end"]
    while time_ref < vals["cutoff"]:
        print "iteration"
        if time_ref < curr:
            return False
        elif time_ref < curr_end:
            return True
        else:
            curr += datetime.timedelta(seconds=vals["repeat_interval"])
            curr_end += datetime.timedelta(seconds=vals["repeat_interval"])
            vals["start"] = curr
            vals["end"] = curr_end

    if time_ref > vals["cutoff"]:
        print "DELETE"
        return False

print ">>>>>"
assert(not isValidOpt(cand1))
assert(isValidOpt(cand2))
assert(isValidOpt(cand3))
assert(not isValidOpt(cand4))
assert(not isValidOpt(cand5))