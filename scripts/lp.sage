import json, preferences

prefs = json.load(open('prefs.txt'))
quotas = json.load(open('quotas.txt'))
seniority = json.load(open('seniority.txt'))

# All constant values for a given LP configuration. Some are loaded from
# configuration files, while other constants are included as literals below.
PARAMS = {
    'min_hours_per_ta': 2,
    'max_hours_per_ta': 19,
    'min_required_total': preferences.serialize(quotas["total"]),
    'min_required_senior': preferences.serialize(quotas["senior"]),
    'ta_preference': prefs['prefs'],
    'quarters_taught': seniority['seniority'],
    'is_senior': lambda quarters : quarters >= 3
}

# Allow 2 more than the minimum in each time slot.
PARAMS['max_allowed_total'] = map(lambda x : x + 2, PARAMS['min_required_total'])
PARAMS['num_tas'] = len(PARAMS['ta_preference'])
PARAMS['num_time_slots'] = len(PARAMS['min_required_total'])

# Let decision variable slots[i][j] be 1 if TA j works time slot i, and be 0
# otherwise.
problem = MixedIntegerLinearProgram()
slots = []
for i in range(PARAMS['num_time_slots']):
    slots.append( problem.new_variable(binary=True, name=("slot[%d]" % i)) )

# Index ranges for both time slots and tas.
slotIndicies = range(PARAMS['num_time_slots'])
taIndicies = range(PARAMS['num_tas'])

# Returns an Sage expression representing, in terms of all relevant decision
# variables, the total number of hours worked by given 'ta' index.
def totalHours(ta):
    return sum([ slots[i][ta] for i in slotIndicies ])

# Returns an Sage expression representing, in terms of all relevant decision
# variables, the total number of tas working at given time 'slot'. If
# 'onlySenior' is set to true, returned expression includes only senior TAs.
def totalTAsWorking(slot, onlySenior=False):
    indicies = taIndicies
    if onlySenior:
        indices = filter(PARAMS['is_senior'], indicies)
    return sum([ slots[slot][i] for i in indicies ])

# Add scheduler preferences for min/max required/allowed TAs per slot.
for i in range(len(slots)):
    working = totalTAsWorking(i)
    problem.add_constraint(PARAMS["min_required_total"][i] <= working)
    problem.add_constraint(working <= PARAMS["max_allowed_total"][i])

# Add scheduler preferences for min/max required/allowed senior TAs per slot.
for i in range(len(slots)):
    working = totalTAsWorking(i, True)
    problem.add_constraint(PARAMS["min_required_senior"][i] <= working)

# Add TA constraints.
for i in range(PARAMS['num_tas']):
    hours = totalHours(i)
    problem.add_constraint(PARAMS['min_hours_per_ta'] <= hours)
    problem.add_constraint(hours <= PARAMS['max_hours_per_ta'])

# Maximize total adherence to TA preference, weighted by TA seniority.
adherence = lambda ta : sum([ PARAMS['ta_preference'][ta][j] * slots[j][ta] for j in slotIndicies ])
problem.set_objective(sum([ PARAMS['quarters_taught'][i] * adherence(i) for i in taIndicies ]))

# Print solution schedule assignment.
problem.solve()
for s in slotIndicies:
    print s, filter(lambda ta : problem.get_values(slots[s])[ta] != 0, taIndicies)