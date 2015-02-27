from threading import Timer, Thread, Lock, Condition
from time import sleep
from Queue import Queue
from data import QueueData
from sys import stdout
from random import random, randint
from datetime import datetime, timedelta

# Simulation speed multiplier. 1 is real time, which would take roughly 9 hours
# for a typical day's worth of data.
SPEED_FACTOR = 9 * 60 * 2

# Senior TA speed multiplier (how much faster senior TAs serve students than
# normal TAs). 1 is the same amount of time as regular TAs.
SENIOR_FACTOR = 2

# Odds that the 2-minute queue will take precedence over the 10 minute.
TWO_MIN_PREF = 1.5

def getHelpTime(queueType):
   if queueType == '2':
      return randint(4, 9)
   else:
      return randint(7, 15)

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
      #write('request\ttime in\ttime out')
      for req in requests:
         adjIn = self._adjust(self.time_in[req], first)
         adjOut = self._adjust(self.time_out[req], first)
         #write('\t'.join(map(str, [req, adjIn, adjOut])))
         write(str(adjOut - adjIn))

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
   def run(self, finishedCallback, totalReqts, seniorReqts):
      self.report = Report(self.buffer)
      self.finished = finishedCallback
      self.regularSurplus = 0
      self.seniorSurplus = 0
      timers = self.scheduleRequests() + self.scheduleReqtChanges(totalReqts, seniorReqts)
      print 'Timers scheduled.'
      initialRegular = totalReqts[0]
      initialSenior = seniorReqts[0]
      for i in range(initialRegular + initialSenior):
         Thread(target=self.serve, args=(i >= initialRegular,)).start()
      for t in timers:
         t.start()

   # Attempt to serve incoming requests until none are left.
   def serve(self, senior=False):
      print '{0} TA beginning shift.'.format('Senior' if senior else 'Normal')
      while self.requestsLeft > 0:
         with self.cv:
            while self.queue.empty() and self.requestsLeft > 0:
               self.cv.wait()
            if self._handleSurplus(senior):
               print 'TA finishing shift.'
               return
            request = self.queue.get()
         if request != None:
            self.requestsLeft -= 1
            print '   served request %s. %d requests left.' % (request, self.requestsLeft)
            # Help the student for exactly the amount of time for that queue
            # (2 minutes or 10 minutes).
            self.report.recordTimeOut(request)
            workingTime = float(getHelpTime(request.queue_type)) * 60 / SPEED_FACTOR
            if senior:
               workingTime /= SENIOR_FACTOR
            sleep(workingTime)

      # No more requests are coming, so every TA should exit.
      with self.cv:
         self.cv.notifyAll()
         # Call the finished callback exactly once.
         self.finished(self.report)
         self.finished = lambda x : None

   # Schedule changes in the number of TAs required at various times in the day.
   # Each returned timer fires at a certain hour, incrementing or decrementing the
   # total or senior TA requirements.
   def scheduleReqtChanges(self, totalReqs, seniorReqs):
      # Returns a sequence of differences between consecutive elements in 'reqs'.
      def getDeltas(reqs):
         deltas = []
         for i in range(1, len(reqs)):
            deltas.append(reqs[i - 1] - reqs[i])
         return deltas
      timers = []
      deltas = zip(getDeltas(totalReqs), getDeltas(seniorReqs))
      hour = 1
      for total, senior in deltas:
         time = float(hour * 3600) / SPEED_FACTOR
         timers.append(Timer(time, self.changeSurplus, args=(total, senior)))
         hour += 1
      return timers

   # If a TA surplus is positive, decrements it and returns True. If a TA surplus
   # is negative, increments it, spins up a new TA thread, and returns False. If
   # the surplus is 0, returns False.
   def _handleSurplus(self, senior):
      # Get the surplus of the current TA type.
      def get():
         return self.seniorSurplus if senior else self.regularSurplus

      # Set the surplus of the current TA type to the given value.
      def set(val):
         if senior:
            self.seniorSurplus = val
         else:
            self.regularSurplus = val

      prior = get()
      if prior > 0:
         set(prior - 1)
         self.cv.notify()
         return True
      elif prior < 0:
         set(prior + 1)
         Thread(target=self.serve, args=(True,)).start()
      return False

   # Changes the total and senior TA surplus by the provided deltas threadsafely.
   def changeSurplus(self, totalChange, seniorChange):
      with self.cv:
         print 'Requirement change: ({0}, {1}).'.format(totalChange, seniorChange)
         self.regularSurplus += totalChange
         self.seniorSurplus += seniorChange

   # Schedules the request times. Returns a list of timers, one per request.
   # Once started, each request is made at the times specified in the request's
   # 'time_in' field relative to the first request (which is made immediately).
   # Time is scaled according to SPEED_FACTOR.
   def scheduleRequests(self):
      if len(self.buffer) == 0:
         raise ValueError('No requests to schedule!')
      self.requestsLeft = len(self.buffer)
      # Start simulation at noon.
      first = self.buffer[len(self.buffer) - 1].time_in
      first = datetime.combine(first.date(), datetime.min.time())
      first += timedelta(hours=12)
      timers = []
      for req in self.buffer:
         time = float((req.time_in - first).seconds) / SPEED_FACTOR
         timers.append(Timer(time, self.makeRequest, (req,)))
      return timers

   # Adds the given request to either the two-minute or ten-minute queue
   # depending on the type of the request.
   def makeRequest(self, request):
      with self.cv:
         self.report.recordTimeIn(request)
         self.queue.put(request)
         self.cv.notify()
