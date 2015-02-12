from datetime import datetime
from conf import KEYS, TIME_KEYS

class QueueRequest:
   # Initializes the QueueRequest to store all (key, value) pairs in dict 
   def __init__(self, dict):
      for key in dict:
         setattr(self, key, dict[key])

class QueueData:
   # Initializes the QueueData store with the contents of the tab separated
   # file, using the first line of the file as column labels.
   def __init__(self, filename):
      lines = list(open(filename))
      keys = lines[0].strip().split('\t')
      self.requests = map(self._parseLine, lines[1:])

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
