from threading import Timer, Thread, Lock
from Queue import Queue
from data import QueueData

# 1 is real time, which would take roughly 9 hours.
SPEED_FACTOR = 9 * 60 * 2

class Simulator:
   # Stores the given list of data.QueueRequest objects.
   def __init__(self, requests, regularTAs, seniorTAs):
      self.twoMinute = Queue()
      self.tenMinute = Queue()
      self.buffer = sorted(requests, key=lambda req : req.time_in)
      self.buffer.reverse()

   # Run the simulation in several threads: one to add requests and one per
   # working TA.
   def run(self):
      Thread(target=self.scheduleRequests).start()

   # Fills the queues with the stored requests at the times specified
   # in each requests 'time_in' field relative to the first request (which
   # is made immediately). Time is scaled according to SPEED_FACTOR.
   def scheduleRequests(self):
      if len(self.buffer) == 0:
         raise ValueError('No requests to schedule!')
      first = self.buffer[len(self.buffer) - 1].time_in
      for req in self.buffer:
         next = self.buffer.pop()
         time = float((next.time_in - first).seconds) / SPEED_FACTOR
         Timer(time, self.makeRequest, (next,)).start()
      print('   Requests scheduled.')

   # Adds the given request to either the two-minute or ten-minute queue
   # depending on the type of the request.
   def makeRequest(self, request):
      if request.queue_type == "2":
         self.twoMinute.put(request)
      else:
         self.tenMinute.put(request)
