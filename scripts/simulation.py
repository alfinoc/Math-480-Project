from threading import Timer, Thread, Lock, Condition
from time import sleep
from Queue import Queue
from data import QueueData
from sys import stdout
from random import random

# 1 is real time, which would take roughly 9 hours.
SPEED_FACTOR = 9 * 60 * 2

# Odds that the 2-minute queue will take precedence over the 10 minute.
TWO_MIN_PREF = 1

class DoubleQueue():
   def __init__(self):
      self.queues = {
         '2': Queue(),
         '10': Queue()
      }
      self.lock = Lock()

   # Returns true if both queues are empty, false otherwise.
   def empty(self):
      with self.lock:
         return self._unsafe_empty()

   # Dequeue a single request from one of the queues.
   def get(self):
      with self.lock:
         if self._unsafe_empty():
            return None
         if self.queues['2'].empty():
            return self.queues['10'].get()
         elif self.queues['10'].empty():
            return self.queues['2'].get()
         else:
            # Both queues have pending requests. Choose randomly according to
            # configurable odds.
            if random() < 1.0 / (TWO_MIN_PREF + 1):
               return self.queues['10'].get()
            else:
               return self.queues['2'].get()

   # Enqueue the request in the appropriate queue.
   def put(self, request):
      with self.lock:
         self.queues[request.queue_type].put(request)

   def _unsafe_empty(self):
      return self.queues['2'].empty() and self.queues['10'].empty()

class Simulator:
   # Stores the given list of data.QueueRequest objects.
   def __init__(self, requests, regularTAs, seniorTAs):
      self.queue = DoubleQueue()
      self.buffer = sorted(requests, key=lambda req : req.time_in)
      self.buffer.reverse()
      self.cv = Condition()
      self.requestsLeft = 0

   # Run simulation threads
   def run(self):
      start = self.scheduleRequests()
      print '   Requests scheduled.'
      for i in range(5):
         ta = Thread(target=self.serve)
         #ta.daemon = True
         ta.start()
      print '   TAs born and waiting.'
      start()

   # Attempt to serve incoming requests until none are left.
   def serve(self):
      while self.requestsLeft > 0:
         self.cv.acquire()
         while self.queue.empty() and self.requestsLeft > 0:
            self.cv.wait()
         request = self.queue.get()
         self.cv.release()
         if request != None:
            print '   served ' + str(request) + ', left: ' + str(self.requestsLeft)
            self.requestsLeft -= 1
            # Help the student for exactly the amount of time for that queue
            # (2 minutes or 10 minutes).
            sleep(float(request.queue_type) * 60 / SPEED_FACTOR)
      print 'TA thread finishing.'
      self.cv.acquire()
      self.cv.notifyAll()
      self.cv.release()

   # Fills the queues with the stored requests at the times specified
   # in each requests 'time_in' field relative to the first request (which
   # is made immediately). Time is scaled according to SPEED_FACTOR.
   def scheduleRequests(self):
      if len(self.buffer) == 0:
         raise ValueError('No requests to schedule!')
      self.requestsLeft = len(self.buffer)
      first = self.buffer[len(self.buffer) - 1].time_in
      timers = []
      while len(self.buffer) > 0:
         next = self.buffer.pop()
         time = float((next.time_in - first).seconds) / SPEED_FACTOR
         timers.append(Timer(time, self.makeRequest, (next,)))
      def start():
         for t in timers:
            t.start()
      return start

   # Adds the given request to either the two-minute or ten-minute queue
   # depending on the type of the request.
   def makeRequest(self, request):
      self.cv.acquire()
      self.queue.put(request)
      self.cv.notify()
      self.cv.release()
