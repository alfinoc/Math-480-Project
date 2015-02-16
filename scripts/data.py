from datetime import datetime
from conf import KEYS, TIME_KEYS, DAY_NAMES

class QueueRequest:
   # Initializes the QueueRequest to store all (key, value) pairs in dict.
   def __init__(self, dict):
      for key in dict:
         setattr(self, key, dict[key])

   def __str__(self):
      return '(%s, %s)' % (str(self.time_in), self.queue_type)

   def __unicode__(self):
      return str(self)

class QueueData:
   # Initializes the QueueData store with the contents of the tab separated
   # file, using the first line of the file as column labels.
   def __init__(self, filename):
      lines = list(open(filename))
      keys = lines[0].strip().split('\t')
      self.requests = map(self._parseLine, lines[1:])

   # Returns an array of maps, one map per week starting at the beginning of the
   # data set. Each map is keyed on day names and each value is a list of requests
   # for that day sorted on request time.
   def byWeek(self):
      # Start at the beginning of the first day.
      first = datetime.combine(self.requests[0].time_in.date(), datetime.min.time())
      last = self.requests[len(self.requests) - 1].time_in
      buckets = [None] * ((last - first).days / len(DAY_NAMES) + 1)
      for req in self.requests:
         delta = req.time_in - first
         day = DAY_NAMES[delta.days % len(DAY_NAMES)]
         week = delta.days / len(DAY_NAMES)
         if buckets[week] == None:
            # Initialize a new week map.
            buckets[week] = {}
            for dayName in DAY_NAMES:
               buckets[week][dayName] = []
         buckets[week][day].append(req)
      return buckets

   # Returns a QueueRequest based on the tab separated data in lines, assuming
   # request fields are ordered as in KEYS. TIME_KEYS are parsed as datetimes.
   def _parseLine(self, line):
      result = {}
      parts = line.strip().split('\t')
      for i in range(len(parts)):
         result[KEYS[i]] = parts[i]
      for key in TIME_KEYS:
         result[key] = datetime.fromtimestamp(int(result[key]))
      return QueueRequest(result)

   # Returns an iterator or the requests list.
   def __iter__(self):
      return self.requests.__iter__()
