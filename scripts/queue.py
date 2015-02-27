from conf import DAY_NAMES
from data import QueueData
from sys import argv
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
   usageError()


def changes(requests):
   ins = map(lambda req : (1, req.time_in), requests)
   outs = map(lambda req : (-1, req.time_out), requests)
   return sorted(ins + outs, key=lambda pair : pair[1])

def intervals(changes):
   intervals = []
   count = 0
   for i in range(len(changes) - 1):
      count += changes[i][0]
      intervals.append(((changes[i + 1][1] - changes[i][1]).seconds, count))
   return intervals

def meanNumberOfWaitingRequests(requests):
   if len(requests) == 0:
      return None
   counts = intervals(changes(requests))
   weightedCountSum = sum([ duration * count for (duration, count) in counts ])
   totalDuration = sum([ duration for (duration, count) in counts ])
   return float(weightedCountSum) / totalDuration

def arrivalRate(requests):
   first = requests[0]
   last = requests[len(requests) - 1]
   return float(len(requests)) / (last.time_in - first.time_in).seconds

quotas = json.load(open('data/quotas.txt'))
data = QueueData(filename).byWeek()

requests = data[week][day]
L_s = meanNumberOfWaitingRequests(requests)
lam = arrivalRate(requests)
print L_s, lam, L_s / lam



