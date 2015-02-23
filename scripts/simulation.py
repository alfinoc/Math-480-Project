from threading import Timer, Thread, Lock, Condition
from time import sleep
from Queue import Queue
from data import QueueData
from sys import stdout
from random import random
from datetime import datetime

# Simulation speed multiplier. 1 is real time, which would take roughly 9 hours
# for a typical day's worth of data.
SPEED_FACTOR = 9 * 60 * 2

# Senior TA speed multiplier (how much faster senior TAs serve students than
# normal TAs). 1 is the same amount of time as regular TAs.
SENIOR_FACTOR = 2

# Odds that the 2-minute queue will take precedence over the 10 minute.
TWO_MIN_PREF = 1

class Report:
   def __init__(self, requests):
      self.served = list(requests)
      self.time_in = {}
      self.time_out = {}

   # Record the unqueue time for the given request object at time of call.
   def recordTimeIn(self, request):
      self.time_in[request] = datetime.now()

   # Record the dequeue time for the given request object at time of call.
   def recordTimeOut(self, request):
      self.time_out[request] = datetime.now()

   # Print the ledger in tab-separated lines, with each line containing an
   # original request as well as that request's enqueue time and dequeue time.
   # Each time is a *real time* lapse from the first enqueue (in seconds).
   def printTSV(self, file=None):
      def write(line):
         if file == None:
            print line
         else:
            file.write(line + '\n')
      requests = sorted(self.served, key=lambda req : self.time_in[req])
      first = min([ self.time_in[req] for req in requests ])
      write('request\ttime in\ttime out')
      for req in requests:
         adjIn = self._adjust(self.time_in[req], first)
         adjOut = self._adjust(self.time_out[req], first)
         write('\t'.join(map(str, [req, adjIn, adjOut])))

   # Convert a simulation 'time' record into real seconds since 'offset' (also
   # in simulation time).
   def _adjust(self, time, offset):
      diff = time - offset
      simSeconds = diff.seconds + float(diff.microseconds) / 1000000
      return simSeconds * SPEED_FACTOR

class DoubleQueue:
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

   # Dequeue and return a single request from one of the queues.
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

   # Returns true if both queues are empty, false otherwise. Does not acquire
   # lock before check.
   def _unsafe_empty(self):
      return self.queues['2'].empty() and self.queues['10'].empty()

class Simulator:
   # Stores the given list of data.QueueRequest objects. 'finishedCallback' is a
   # function of one argument that is called with the completed report object.
   def __init__(self, requests):
      self.queue = DoubleQueue()
      self.buffer = sorted(requests, key=lambda req : req.time_in)
      self.buffer.reverse()
      self.cv = Condition()
      self.requestsLeft = 0

   # Run simulation threads.
   def run(self, regularTAs, seniorTAs, finishedCallback, totalReqts):
      self.report = Report(self.buffer)
      self.finished = finishedCallback
      self.totalSurplus = 0
      self.seniorSurplus = 0
      timers = self.scheduleRequests() + self.scheduleReqtChanges(totalReqts)
      print '   Requests scheduled.'
      for i in range(regularTAs + seniorTAs):
         ta = Thread(target=self.serve, args=(i >= regularTAs,))
         #ta.daemon = True
         ta.start()
      print '   TAs born and waiting.'
      for t in timers:
         t.start()

   # Attempt to serve incoming requests until none are left.
   def serve(self, senior=False):
      while self.requestsLeft > 0:
         self.cv.acquire()
         while self.queue.empty() and self.requestsLeft > 0:
            self.cv.wait()
         #if self._handleSurplus(senior):
         #   return
         request = self.queue.get()
         self.cv.release()
         if request != None:
            self.requestsLeft -= 1
            print '   served request %s. %d requests left.' % (request, self.requestsLeft)
            # Help the student for exactly the amount of time for that queue
            # (2 minutes or 10 minutes).
            self.report.recordTimeOut(request)
            sleep(float(request.queue_type) * 60 / SPEED_FACTOR / SENIOR_FACTOR)

      # No more requests are coming, so every TA should exit.
      self.cv.acquire()
      self.cv.notifyAll()
      # Call the finished callback exactly once.
      self.finished(self.report)
      self.finished = lambda x : None
      self.cv.release()

   # Schedule changes in the number of TAs required at various times in the day.
   # Each returned timer fires at a certain hour, incrementing or decrementing the
   # total or senior TA requirements.
   def scheduleReqtChanges(self, reqs):
      # Returns a sequence of differences between consecutive elements in 'reqs'.
      def getDeltas(reqs):
         deltas = []
         for i in range(1, len(reqs)):
            deltas.append(reqs[i] - reqs[i - 1])
         return deltas
      timers = []
      deltas = zip(getDeltas(reqs), getDeltas(reqs))
      hour = 1
      print deltas
      for total, senior in deltas:
         time = hour * 360 / SPEED_FACTOR
         timers.append(Timer(time, self.changeSurplus, args=(total, senior)))
      return timers

   def _handleSurplus(self, senior):
      if senior:
         if self.seniorSurplus > 0:
            self.seniorSurplus -= 1
            self.cv.notify()
            return True
         elif self.seniorSurplus < 0:
            self.seniorSurplus += 1
            Thread(target=self.serve, args=(True,)).start()
      else:
         if self.totalSurplus > 0:
            self.totalSurplus -= 1
            self.cv.notify()
            return True
         elif self.totalSurplus < 0:
            self.totalSurplus += 1
            Thread(target=self.serve, args=(False,)).start()
      return False

   def changeSurplus(self, totalChange, seniorChange):
      self.cv.acquire()
      self.totalSurplus += totalChange
      self.seniorSurplus += seniorChange
      self.cv.release()

   # Schedules the request times. Returns a list of timers, one per request.
   # Once started, each request is made at the times specified in the request's
   # 'time_in' field relative to the first request (which is made immediately).
   # Time is scaled according to SPEED_FACTOR.
   def scheduleRequests(self):
      if len(self.buffer) == 0:
         raise ValueError('No requests to schedule!')
      self.requestsLeft = len(self.buffer)
      first = self.buffer[len(self.buffer) - 1].time_in
      timers = []
      for req in self.buffer:
         time = float((req.time_in - first).seconds) / SPEED_FACTOR
         timers.append(Timer(time, self.makeRequest, (req,)))
      return timers

   # Adds the given request to either the two-minute or ten-minute queue
   # depending on the type of the request.
   def makeRequest(self, request):
      self.cv.acquire()
      self.report.recordTimeIn(request)
      self.queue.put(request)
      self.cv.notify()
      self.cv.release()
