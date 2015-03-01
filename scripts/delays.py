from data import QueueData
from sys import argv

data = QueueData('data/fall_queue_data.tsv').byWeek()

delays = data[0]['Thursday']
print ' '.join([ str((i + 1, (delays[i].time_out - delays[i].time_in).seconds)) for i in range(len(delays)) ])

