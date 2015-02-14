import json, preferences

prefs = json.load(open('prefs.txt'))
quotas = json.load(open('quotas.txt'))

PARAMS = {
    'min_hours_per_ta': 2,
    'max_hours_per_ta': 19,
    'min_required_total': preferences.serialize(quotas["total"]),
    'min_required_senior': preferences.serialize(quotas["senior"]),
    'ta_preference': prefs['prefs']
}

# Allow 2 more than the minimum in each time slot.
PARAMS['max_allowed'] = map(lambda x : x + 2, PARAMS['min_required_total'])
PARAMS['num_tas'] = len(PARAMS['ta_preference'])
PARAMS['num_time_slots'] = len(PARAMS['min_required_total'])

problem = MixedIntegerLinearProgram()
slots = []
for i in range(PARAMS['num_time_slots']):
    slots.append( problem.new_variable(binary=True, name=("slot[%d]" % i)) )

# Add scheduler preferences (min/max required/allowed TAs per slot).
for i in range(len(slots)):
    totalTAsAtSlotI = sum([ slots[i][j] for j in range(PARAMS['num_tas']) ])
    problem.add_constraint(PARAMS["min_required_total"] <= totalTAsAtSlotI)
    problem.add_constraint(totalTAsAtSlotI <= PARAMS["max_required_total"])
problem.show()
