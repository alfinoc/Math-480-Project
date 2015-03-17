import json, preferences
from munkres import Munkres, print_matrix
import preferences
from problem import getConfig

LARGE = 1000000
PARAMS = getConfig()

# Returns a square version of the given matrix constructed by adding necessary
# rows and columns, inserting default values in added cells.
def square(mat, default=LARGE):
    if len(mat) == 0:
        return mat
    numRows = len(mat)
    numCols = len(mat[0])
    diff = abs(numRows - numCols)
    if numRows > numCols:
        mat = map(lambda row : row + [LARGE] * diff, mat)
    elif numRows < numCols:
        mat += map(lambda x : [LARGE] * numCols, range(diff))
    return mat

# Returns a new copy of mat with fn applied to every cell.
def matMap(fn, mat):
    return map(lambda row : map(fn, row), mat)

# Returns a new copy of mat with occurances of a replaced with b.
def replace(mat, a, b=LARGE):
    return matMap(lambda val : val if val != a else b, mat)

# Returns the scalar matrix product scalar * mat.
def mult(scalar, mat):
    return matMap(lambda val : scalar * val, mat)

# Returns the scalar matrix sum scalar + mat.
def add(scalar, mat):
    return matMap(lambda val : scalar + val, mat)

# Returns the a copy of the matrix with all float values floored to ints.
def truncate(mat):
    return matMap(lambda val : int(val), mat)

# Returns a copy of mat with every value increased by a random value between 0
# and maxDelta inclusive.
def perturb(mat, maxDelta=1):
    return matMap(lambda val : val + randint(0, maxDelta), mat)

# Index arrays for tas and slots.
TAS = range(PARAMS['num_tas'])
SLOTS = range(PARAMS['num_time_slots'])

# Returns the senior priority coefficient a given ta (how much more to weigh the
# given TA's preferences).
def senior_priority_coefficent(ta):
    return PARAMS['senior_priority'] * (PARAMS['quarters_taught'][ta] - 1) + 1

# Multiplies each TA row in the given preference matrix by the senior priority
# coefficient for that TA.
def applySeniorFactor(prefMat):
    result = []
    for ta in range(len(prefMat)):
        coeff = senior_priority_coefficent(ta)
        result.append(map(lambda pref : coeff * pref, prefMat[ta]))
    return result

# Returns a merged copy of the two schedules, raising ValueError if such a merge
# results in the assignment of a single TA to a slot twice.
def merge(asst1, asst2):
    result = []
    for ta in range(len(asst1)):
        if len(set(asst1[ta]).intersection(set(asst2[ta]))) != 0:
            raise ValueError('TA cannot work two slots at once.')
        result.append(sorted(asst1[ta] + asst2[ta]))
    return result

# Returns a list containing (ta, slot) pairs, where ta is assigned to slot in
# schedule.
def assignmentList(schedule):
    result = []
    for ta in range(len(schedule)):
        for slot in schedule[ta]:
            result.append((ta, slot))
    return result

# Convert 0-1 real valued preferences to 0-100 integer valued preferences,
# transform preference matrix to cost matrix, then replace all 0's (impossible
# time slots) with LARGE values. Scale preferences by senior priority factor.
# Finally, square the matrix off.
costs = PARAMS['ta_preference']
costs = applySeniorFactor(costs)
costs = mult(100, costs)
costs = truncate(costs)
costs = perturb(costs)
costs = mult(-1, costs)
costs = add(101, costs)
costs = replace(costs, 101)

# Returns a cost matrix constructed by including only rows indexed in
# taWhitelist and only columns indexed in slotWhitelist. Any index pair
# (ta, slot) in blacklist is given a LARGE cost.
def submatrix(taWhitelist, slotWhitelist, blacklist):
    def getCost(ta, slot):
        if (ta, slot) in blacklist:
            return LARGE
        else:
            return costs[ta][slot]

    result = []
    for ta in taWhitelist:
        result.append(map(lambda slot : getCost(ta, slot), slotWhitelist))
    return result

# Assigns each ta in tas to one slot in slots, returning the assigned as a
# schedule. If there are more tas than slots, some tas will not be assigned. If
# there are more slots than tas, raises ValueError. Will not make (ta, slot)
# assignments in blacklist.
def assign(tas, slots, blacklist=[]):
    if len(tas) < len(slots):
        raise ValueError('Need more TAs: {0}, {1}'.format(len(tas), len(slots)))
    result = map(lambda x : [], TAS)
    costMatrix = square(submatrix(tas, slots, blacklist))
    assts = Munkres().compute(costMatrix)
    for i, j in assts:
        if costMatrix[i][j] != LARGE:
            # Indices involved in the subproblem (only the TAs/slots that need
            # to be assigned this round) need to be translated to general
            # TA/slot indices.
            ta = tas[i]
            slot = slots[j]
            result[ta].append(slot)
    return result

# Returns a list of TA indices to consider for assignment, including only
# seniors if senior is true and all TAs otherwise. Includes only TAs whose
# scheduled hours do not meet the minimum required.
def tasToConsider(currentSchedule, senior=False):
    def hoursWanted(ta):
        return PARAMS['min_hours_per_ta'] - len(currentSchedule[ta])
    tas = filter(PARAMS['is_senior'], TAS) if senior else TAS
    return filter(lambda ta : hoursWanted(ta) > 0, TAS)

# Returns a list of slot indices to consider for assignment, including only
# slots that do not have satisfied quotas. If senior is true, only senior quotas
# are used; otherwise, total TA quotas are used.
def slotsToConsider(currentSchedule, senior=False):
    def slotsWanting(slot):
        quotas = PARAMS['min_required_senior'] if senior else PARAMS['min_required_total']
        filled = len(filter(lambda assigned : slot in assigned, currentSchedule))
        return quotas[slot] - filled
    return filter(lambda slot : slotsWanting(slot) > 0, SLOTS)

# Apply the Hungarian method repeatedly until all quotas are filled. If senior
# is True, consider only senior quotas; otherwise, consider total quotas.
# Attempt at most attempts times. Returns the result of merging the
# priorSchedule with the newly generated assignments.
def repeatHungarian(priorSchedule, senior=False, attempts=10):
    schedule = priorSchedule
    for i in range(attempts):
        tas = tasToConsider(schedule, senior)
        slots = slotsToConsider(schedule, senior)
        if len(slots) == 0:
            break
        new = assign(tas, slots, assignmentList(schedule))
        schedule = merge(schedule, new)
        print schedule
    print 'Solution found in {0} Hungarian applications.'.format(i)
    return schedule

# Returns all the TAs scheduled for the given slot in the given schedule.
def scheduledFor(slot, schedule):
    result = []
    for ta in range(len(schedule)):
        if slot in schedule[ta]:
            result.append(ta)
    return result

schedule = map(lambda x : [], TAS)

# Assign all senior TAs until senior quotas are met.
schedule = repeatHungarian(schedule, True, 10)

# Assign all TAs until all quotas are met.
schedule = repeatHungarian(schedule, False, 10)

# Greedily place extra hours per TA.
extra = filter(lambda ta : len(schedule[ta]) < PARAMS['max_hours_per_ta'](ta), TAS)
for ta in extra:
    ranked = sorted(zip(SLOTS, PARAMS['ta_preference'][ta]), key=lambda p : p[1])
    numDesired = PARAMS['max_hours_per_ta'](ta) - len(schedule[ta])
    while len(ranked) > 0 and numDesired > 0:
        slot, pref = ranked.pop()
        alreadyWorking = scheduledFor(slot, schedule)
        understaffed = len(alreadyWorking) < PARAMS['max_allowed_total'][slot]
        if ta not in alreadyWorking and understaffed:
            schedule[ta].append(slot)
            numDesired -= 1

# Report solution schedule as map from TA to slots.
for ta in range(len(schedule)):
    print ta, schedule[ta]
