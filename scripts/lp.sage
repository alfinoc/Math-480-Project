import json, preferences

# Load parameter configurations.
prefs = json.load(open('prefs.txt'))
quotas = json.load(open('quotas.txt'))

# Store all constant values in LP formulation.
PARAMS = {
    'min_hours_per_ta': 2,
    'max_hours_per_ta': 19,
    'min_required_total': preferences.serialize(quotas["total"]),
    'min_required_senior': preferences.serialize(quotas["senior"]),
    'ta_preference': prefs['prefs']
}

# Allow 2 more than the minimum in each time slot.
PARAMS['max_allowed_total'] = map(lambda x : x + 2, PARAMS['min_required_total'])
PARAMS['num_tas'] = len(PARAMS['ta_preference'])
PARAMS['num_time_slots'] = len(PARAMS['min_required_total'])

# Store decision variables as an array of "slot" sage variables, where slot[i]
# is 1 if TA i works that slot.
problem = MixedIntegerLinearProgram()
slots = []
for i in range(PARAMS['num_time_slots']):
    slots.append( problem.new_variable(binary=True, name=("slot[%d]" % i)) )

slotIndicies = range(PARAMS['num_time_slots'])
def totalHours(ta):
    return sum([ slots[i][ta] for i in slotIndicies ])

taIndicies = range(PARAMS['num_tas'])
def totalTAsWorking(slot):
    return sum([ slots[slot][i] for i in taIndicies ])

# Add scheduler preferences (min/max required/allowed TAs per slot).
for i in range(len(slots)):
    working = totalTAsWorking(i)
    problem.add_constraint(PARAMS["min_required_total"][i] <= working)
    problem.add_constraint(working <= PARAMS["max_allowed_total"][i])

# Add TA constraints.
for i in range(PARAMS['num_tas']):
    hours = totalHours(i)
    problem.add_constraint(PARAMS['min_hours_per_ta'] <= hours)
    problem.add_constraint(hours <= PARAMS['max_hours_per_ta'])

preference = PARAMS['ta_preference']
problem.set_objective(sum([ sum([ preference[j][i] * slots[i][j] for j in taIndicies ]) for i in slotIndicies ]))
problem.solve()

# Report the TA assignments for each slot, one slot per line.
solution = []
for s in slotIndicies:
    print s, filter(lambda ta : problem.get_values(slots[s])[ta] != 0, taIndicies)
