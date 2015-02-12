from data import QueueData
from sys import argv, exit
from conf import DAY_NAMES

if len(argv) < 2:
   exit('Usage: provide the TSV file name.')

# Prints the number of request at each day of the week.
data = QueueData(argv[1])
daysOfWeek = [0] * 7
for pt in data:
   daysOfWeek[pt.time_in.weekday()] += 1
for i in range(len(DAY_NAMES)):
   print DAY_NAMES[i] + ':', daysOfWeek[i]
