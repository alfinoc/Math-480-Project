from sys import argv, exit
from simulation import Simulator
from data import QueueData
from conf import DAY_NAMES
from policies import crisisThresholdsAndFlip
import json

# Report correct usage and exit gracefully.
def usageError():
   exit('Usage: <request_file_tsv> <week> <day>')

# Parse command line arguments.
try:
   filename = argv[1]
   week = int(argv[2])
   day = argv[3]
   if not day in DAY_NAMES:
      usageError()
except:
   usageError()

# Returns the vector difference of lists l1 and l2.
def diff(l1, l2):
   return map(lambda (x, y) : x - y, zip(l1, l2))

print 'Simulating on {0} of week {1}.'.format(day, week)

# Set up simulation
quotas = json.load(open('data/quotas.txt'))
senior = quotas['senior'][day]
regular = diff(quotas['total'][day], senior)
requests = QueueData(filename).byWeek()[week][day]

# Run the simulation with above configuration 'trial' number of times.
def runSim(trials):
   sim = Simulator(requests)
   outFile = open("data/results/{0}_{1}_{2}_delays.results".format(week, day, trials), 'w')

   # Report the results to the open file.
   def reportResults(report):
      report.printTSV(outFile)
      if trials > 1:
         runSim(trials - 1)

   # Run the simulation.
   tieBreakingPolicy = crisisThresholdsAndFlip(10 * 60, 40 * 60, 1.5)
   sim.run(reportResults, tieBreakingPolicy, regular, senior)

runSim(1)
