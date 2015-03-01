from conf import DAY_NAMES
from data import QueueData
from sys import argv
from queue import meanNumberOfWaitingRequests, arrivalRate
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


quotas = json.load(open('data/quotas.txt'))
data = QueueData(filename).byWeek()

requests = data[week][day]
L_s = meanNumberOfWaitingRequests(requests)
lam = arrivalRate(requests)
print L_s, lam, L_s / lam
