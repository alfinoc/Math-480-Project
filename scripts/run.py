from sys import argv, exit
from simulation import Simulator
from data import QueueData
from conf import DAY_NAMES

# Report correct usage and exit gracefully.
def usageError():
   exit('Usage: <request_file_tsv> <week> <day>')

try:
   filename = argv[1]
   week = int(argv[2])
   day = argv[3]
   if not day in DAY_NAMES:
      usageError()
except:
   print e
   usageError()

print 'Simulating on {0} of week {1}.'.format(day, week)
data = QueueData(filename).byWeek()[week][day]
sim = Simulator(data, 3, 2)
sim.run()
