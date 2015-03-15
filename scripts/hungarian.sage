import json, preferences
from munkres import Munkres, print_matrix

LARGE = 1000000

# Returns a square version of the given matrix constructed by adding necessary rows
# and columns, inserting default values in added cells.
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

# Returns the scalar matrix sum scalar + mat
def add(scalar, mat):
    return matMap(lambda val : scalar + val, mat)

# Returns the a copy of the matrix with all float values floored to ints.
def truncate(mat):
    return matMap(lambda val : int(val), mat)

# Returns a copy of mat with every value increased by a random value between 0
# and maxDelta inclusive.
def perturb(mat, maxDelta=1):
    return matMap(lambda val : val + randint(0, maxDelta), mat)

prefs = json.load(open('prefs.txt'))
quotas = json.load(open('quotas.txt'))
seniority = json.load(open('seniority.txt'))
max_hours_per_ta = json.load(open('max_hours.txt'))

# All constant values for a given LP configuration. Some are loaded from configuration
# files, while other constants are included as literals below.
PARAMS = {
    'min_hours_per_ta': 2,
    'max_hours_per_ta': lambda ta : min(max_hours_per_ta['max_hours'][ta], 19.5),
    'min_required_total': preferences.serialize(quotas["total"]),
    'min_required_senior': preferences.serialize(quotas["senior"]),
    'ta_preference': prefs['prefs'],
    'quarters_taught': seniority['seniority'],
    'is_senior': lambda ta : PARAMS['quarters_taught'][ta] >= 3,
    'senior_priority': 1
}

# Allow 2 more than the minimum in each time slot.
PARAMS['max_allowed_total'] = map(lambda x : x + 2, PARAMS['min_required_total'])
PARAMS['num_tas'] = len(PARAMS['ta_preference'])
PARAMS['num_time_slots'] = len(PARAMS['min_required_total'])

# Index arrays for tas and slots.
TAS = range(PARAMS['num_tas'])
SLOTS = range(PARAMS['num_time_slots'])

# Returns the senior priority coefficient a given ta (how much more to weight
# the given TA's preferences).
def senior_priority_coefficent(ta):
    return PARAMS['senior_priority'] * (PARAMS['quarters_taught'][ta] - 1) + 1

# Multiplies each TA row in the given preference matrix by the senior priority
# coefficient for that TA.
def applySeniorFactor(prefMat):
    result = []
    for ta in range(prefMat):
        coeff = senior_priority_coefficent(ta)
        result.append(map(lambda pref : coeff * pref, prefMat[ta]))
    return result

# Returns a merged copy of the two schedules, raising ValueError if such a merge
# results in the assignment of a TA to a slot twice.
def merge(asst1, asst2):
    result = []
    for ta in range(len(asst1)):
        if len(set(asst1[ta]).intersection(set(asst2[ta]))) != 0:
            raise ValueError('TA cannot work two slots at once.')
        result.append(sorted(asst1[ta] + asst2[ta]))
    return result

# Returns a list containing (ta, slot) pairs, where ta is assigned to slot in schedule.
def assignmentList(schedule):
    result = []
    for ta in range(len(schedule)):
        for slot in schedule[ta]:
            result.append((ta, slot))
    return result

# Convert 0-1 real valued preferences to 0-100 integer valued preferences, transform
# preference matrix to cost matrix, then replace all 0's (impossible time slots)
# with LARGE values. Finally, square the matrix off.
costs = PARAMS['ta_preference']
costs = mult(100, costs)
costs = truncate(costs)
costs = perturb(costs)
costs = mult(-1, costs)
costs = add(101, costs)
costs = replace(costs, 101)

# Returns a matrix constructed by including only rows indexed in taWhitelist and only
# columns indexed in slotWhitelist. Any index pair (ta, slot) in blacklist is replaced
# with LARGE.
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

# Assigns each ta in tas to one slot in slots, returning the assigned as a schedule.
# If there are more tas than slots, some tas will not be assigned. If there are more
# slots than tas, raises ValueError. Will not make (ta, slot) assignments in blacklist.
def assign(tas, slots, blacklist=[]):
    if len(tas) < len(slots):
        raise ValueError('Need more TAs.')
    result = map(lambda x : [], TAS)
    costMatrix = square(submatrix(tas, slots, blacklist))
    assts = Munkres().compute(costMatrix)
    for i, j in assts:
        if costMatrix[i][j] != LARGE:
            # Indices involved in the subproblem (only the TAs/slots that need to be
            # assigned this round) need to be translated to general TA/slot indices.
            ta = tas[i]
            slot = slots[j]
            result[ta].append(slot)
    return result

def tasToConsider(currentSchedule):
    def hoursWanted(ta):
        return PARAMS['min_hours_per_ta'] - len(currentSchedule[ta])
    return filter(lambda ta : hoursWanted(ta) > 0, TAS)

def slotsToConsider(currentSchedule):
    def slotsWanting(slot):
        required = PARAMS['min_required_total'][slot]
        filled = len(filter(lambda assigned : slot in assigned, currentSchedule))
        return required - filled
    return filter(lambda slot : slotsWanting(slot) > 0, SLOTS)

schedule = map(lambda x : [], TAS)

# Assign all senior TAs until senior quotas are met.

# Assign all TAs until all quotas are met.
for i in range(7):
    tas = tasToConsider(schedule)
    slots = slotsToConsider(schedule)
    if len(slots) == 0:
        break
    new = assign(tas, slots, assignmentList(schedule))
    schedule = merge(schedule, new)
    print 'round {0}: t{1} s{2} {2}'.format(i, len(tas), len(slots), len(filter(lambda a : len(a) != 0, new)))

# Greedily place extra hours per TA.
print tas, slots

for ta in range(len(schedule)):
    print ta, schedule[ta]