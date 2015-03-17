import json, preferences
from problem import getConfig

PARAMS = getConfig()

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

# Returns the senior priority coefficient a given ta.
def senior_priority_coefficent(ta):
    return PARAMS['senior_priority'] * (PARAMS['quarters_taught'][ta] - 1) + 1

# Add scheduler preferences for min/max required/allowed TAs per slot.
for i in range(len(slots)):
    working = totalTAsWorking(i)
    problem.add_constraint(PARAMS["min_required_total"][i] <= working)
    problem.add_constraint(working <= PARAMS["max_allowed_total"][i])

# Add scheduler preferences for min required senior TAs per slot.
for i in range(len(slots)):
    working = totalTAsWorking(i, True)
    problem.add_constraint(PARAMS["min_required_senior"][i] <= working)

# Add TA constraints.
for i in range(PARAMS['num_tas']):
    hours = totalHours(i)
    problem.add_constraint(PARAMS['min_hours_per_ta'] <= hours)
    problem.add_constraint(hours <= PARAMS['max_hours_per_ta'](i))

# Add constraints for hours that TAs absolutely cannot work.
for i in range(PARAMS['num_tas']):
    for j in range(len(slots)):
        if (PARAMS['ta_preference'][i][j] == 0.0):
            problem.add_constraint(slots[j][i] == 0)

# Maximize total adherence to TA preference, weighted by TA seniority.
adherence = lambda ta : sum([ PARAMS['ta_preference'][ta][j] * slots[j][ta] for j in slotIndicies ])
problem.set_objective(sum([ senior_priority_coefficent(i) * adherence(i) for i in taIndicies ]))

# Print solution schedule assignment.
print 'Objective Value:', problem.solve()
for s in slotIndicies:
    print s, filter(lambda ta : problem.get_values(slots[s])[ta] != 0, taIndicies)
