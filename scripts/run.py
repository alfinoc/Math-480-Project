from sys import argv, exit
from simulation import Simulator
from data import QueueData
from conf import DAY_NAMES
import json

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

quotas = json.load(open('data/quotas.txt'))

print 'Simulating on {0} of week {1}.'.format(day, week)
data = QueueData(filename).byWeek()[week][day]
sim = Simulator(data)
file = open("{0}_{1}_{2}.results".format(filename, week, day), 'w')

# Report the results to the open file.
def reportResults(report):
   report.printTSV(file)

def diff(l1, l2):
   return map(lambda (x, y) : x - y, zip(l1, l2))

senior = quotas['senior'][day]
regular = diff(quotas['total'][day], senior)
sim.run(reportResults, regular, senior)
