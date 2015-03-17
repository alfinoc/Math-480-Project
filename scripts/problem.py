import json, preferences

# A JSON object with a single key "prefs" mapping to a 2D array of floats. Each
# row corresponds to a TA and each column to a time slot.
prefs = json.load(open('prefs.txt'))

# A JSON object with two keys "total" and "senior" each mapping to a quota dict.
# Each quota dict is keyed on the day of the week and keyed on a list of all
# minimum workers required for each hour that day.
quotas = json.load(open('quotas.txt'))

# A JSON object of a single key "seniority" mapping to a list of seniority
# numbers (number of quarters that TA has taught).
seniority = json.load(open('seniority.txt'))

# A JSON object of a single key "max_hours" mapping to a list of max hours
# numbers (the most any TA would like to work).
max_hours_per_ta = json.load(open('max_hours.txt'))

# Returns a program configuration containing all constant values and predicates
# for a given scheduling problem. Some are loaded from configuration data files,
# while other constants are included as literals below.
def getConfig():
    config = {
        'min_hours_per_ta': 2,
        'max_hours_per_ta': lambda ta : min(max_hours_per_ta['max_hours'][ta], 19.5),
        'min_required_total': preferences.serialize(quotas["total"]),
        'min_required_senior': preferences.serialize(quotas["senior"]),
        'ta_preference': prefs['prefs'],
        'quarters_taught': seniority['seniority'],
        'is_senior': lambda ta : config['quarters_taught'][ta] >= 3,
        'senior_priority': 1,
        'min_pref': 0.3
    }

    # Allow 2 more than the minimum in each time slot.
    config['max_allowed_total'] = map(lambda x : x + 2, config['min_required_total'])
    config['num_tas'] = len(config['ta_preference'])
    config['num_time_slots'] = len(config['min_required_total'])

    # Treat all preferences below min_pref.
    meetMinPref = lambda row : map(lambda x : x if x >= config['min_pref'] else 0, row)
    config['ta_preference'] = map(lambda row : meetMinPref(row), config['ta_preference'])
    return config
