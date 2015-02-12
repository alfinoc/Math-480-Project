DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
             'Friday', 'Saturday', 'Sunday']

TIME_KEYS = ['time_in', 'time_out']
KEYS = TIME_KEYS + ['queue_type', 'course', 'title']

HOURS = {}
for day in DAY_NAMES[:-3]:
   HOURS[day] = 9
HOURS['Friday'] = 6
HOURS['Saturday'] = 4
HOURS['Sunday'] = 4
