from data import QueueData
from sys import argv

data = QueueData(argv[1]).byWeek()

for d in data[0]['Thursday']:
   print (d.time_out - d.time_in).seconds

