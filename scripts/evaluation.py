# Returns the total adherence to the preferences of given ta.
def ta_adherence(ta):
    def satisfied_preference(slot):
        return PARAMS['ta_preference'][ta][slot] * int(ta in schedule[slot])
    return sum([ satisfied_preference(i) for i in range(len(schedule)) ])

# Returns the total adherence to all preferences of all tas in given schedule.
def total_adherence(schedule):
    return sum([ ta_adherence(i) for i in tas ])

# Returns the total weighted adherence to all preferences of all tas in given
# schedule where each ta adherence total is scaled by that ta's number of
# quarters taught.
def total_weighted_adherence(schedule):
    return sum([ PARAMS['quarters_taught'][i] * ta_adherence(i) for i in tas ])

# Returns the number of slots scheduled for seniors in the given schedule.
def seniors_scheduled(schedule):
    def numSeniors(working):
        return len(filter(PARAMS['is_senior'], working))
    return sum(map(lambda slot : numSeniors(slot), schedule))

# Returns the number of slots scheduled for regular tas in the given schedule.
def regular_scheduled(schedule):
    def numSeniors(working):
        return len(working)
    return sum(map(lambda slot : numSeniors(slot), schedule )) - seniors_scheduled(schedule)

# The mean satisfied preference value across all assigned slots in the schedule.
# Formally, this is the mean value of the set of all {a_ij : x_ij = 1}. filterFn
# takes one argument, a ta, and returns true if that ta's assigned slot should
# be considered.
def mean_pref(filterFn, schedule):
    prefs_satisfied = []
    total = 0
    for slot in range(len(schedule)):
        consider = filter(filterFn, schedule[slot])
        total += len(consider)
        for ta in consider:
            prefs_satisfied.append(PARAMS['ta_preference'][ta][slot])
    return sum(prefs_satisfied) / total