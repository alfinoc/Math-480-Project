tas = range(len(PARAMS['ta_preference']))
seniors = filter(lambda ta : PARAMS['is_senior'](PARAMS['quarters_taught'][ta]), tas)
senior_quotas = PARAMS['min_required_senior']
total_quotas = PARAMS['min_required_total']
regular_quotas = map(lambda i : total_quotas[i] - senior_quotas[i], range(len(total_quotas)))

schedule = [ [] for i in total_quotas ]
to_place = [PARAMS['min_hours_per_ta']] * len(tas)

# Returns true if all elements of l are 0, false otherwise.
def all_zero(l):
    return len(filter(lambda val : val != 0, l)) == 0

# Returns the index of the first non-zero element in l.
def first_non_zero(l):
    if all_zero(l):
        raise ValueError()
    i = 0
    while l[i] == 0:
        i += 1
    return i

# Adds the ta to the given slot in the schedule.
def add_to_schedule(ta, slot):
    schedule[slot].append(ta)

# Assigns the ta with prefs to their top choice available, respecting quotas
# only if a quotas list is provided.
def make_best_choice(prefs, ta, quotas=None):
    choices = sorted(zip(range(len(prefs)), prefs), key=lambda pair : pair[1])
    choices = filter(lambda val : val != 0, choices)
    while len(choices) > 0:
        slot, pref = choices.pop()
        if (quotas == None or quotas[slot] > 0) and ta not in schedule[slot]:
            add_to_schedule(ta, slot)
            if quotas != None:
                quotas[slot] -= 1
            return True
    return False

# Returns the index of the best senior for the spot (the one who prefers it
# most and is eligible).
def find_best_senior(slot):
    # only consider seniors that are not already working minimum hours
    best = filter(lambda ta : to_place[ta] > 0, seniors)
    # who are not already scheduled in this slot
    best = filter(lambda ta : not ta in schedule[slot], best)
    # sorted by preference
    best = zip(best, map(lambda s : PARAMS['ta_preference'][s][slot], best))
    best = sorted(best, key=lambda pair : pair[1])
    if len(best) == 0:
        raise ValueError('Cannot fill senior slot.')
    return best[-1][0]

def attempt_place(ta, quotas=None):
    return make_best_choice(PARAMS['ta_preference'][ta], ta, quotas)

# Fill senior slots.
while not all_zero(senior_quotas):
    slot = first_non_zero(senior_quotas)
    ta = find_best_senior(slot)
    senior_quotas[slot] -= 1
    to_place[ta] -= 1
    add_to_schedule(ta, slot)

# Fill all other slots two hours at a time, letting TAs choose by seniority.
tas.sort(lambda x, y : PARAMS['quarters_taught'][y] -
                       PARAMS['quarters_taught'][x])
print tas, map(lambda ta : PARAMS['quarters_taught'][ta], tas)
for ta in tas:
    if to_place[ta] > 0 and attempt_place(ta, regular_quotas): to_place[ta] -= 1
    if to_place[ta] > 0 and attempt_place(ta, regular_quotas): to_place[ta] -= 1

# Fill in surplus wherever the TAs would like it.
for ta in tas:
    to_place[ta] = max(0, PARAMS['max_hours_per_ta'](ta) -
                          PARAMS['min_hours_per_ta'])
while not all_zero(to_place):
    ta = first_non_zero(to_place)
    if attempt_place(ta):
        to_place[ta] -= 1
    else:
        print 'No extra slot available.'
