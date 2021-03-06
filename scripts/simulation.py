from threading import Timer, Thread, Lock, Condition
from time import sleep
from collections import deque
from data import QueueData
from sys import stdout
from random import randint
from datetime import datetime, timedelta

# Simulation speed multiplier. 1 is real time, which would take roughly 9 hours
# for a typical day's worth of data.
SPEED_FACTOR = 9 * 60 * 2

# Senior TA speed multiplier (how much faster senior TAs serve students than
# normal TAs). 1 is the same amount of time as regular TAs.
SENIOR_FACTOR = 1.5

# Returns a service time for a request in give queueType (either '2' or '10')
# in seconds real time.
def getHelpTime(queueType):
   if queueType == '2':
      return randint(3, 6) * 60
   else:
      return randint(8, 12) * 60

class Report:
   # Initializes the report to store information about the given requests.
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
   def __init__(self, breakTies):
      self.queues = {
         '2': deque(),
         '10': deque()
      }
      self.lock = Lock()
      self.breakTies = breakTies

   # Returns true if both queues are empty, false otherwise.
   def empty(self):
      with self.lock:
         return self._unsafe_empty()

   # Dequeue and return a single request from one of the queues. The report
   # should contain a time_in entry for every request currently in the queue. 
   def get(self, report):
      # Returns the current wait time of the oldest request in the queue with
      # given type.
      def wait(queue_type):
         delta = datetime.now() - report.time_in[self.queues[queue_type][0]]
         return delta.seconds + float(delta.microseconds) / 1000000

      with self.lock:
         if self._unsafe_empty():
            return None
         elif len(self.queues['2']) == 0:
            return self.queues['10'].popleft()
         elif len(self.queues['10']) == 0:
            return self.queues['2'].popleft()
         else:
            choice = self.breakTies(wait('2')  * SPEED_FACTOR,
                                    wait('10') * SPEED_FACTOR)
            return self.queues[choice].popleft()

   # Enqueue the request in the appropriate queue.
   def put(self, request):
      with self.lock:
         self.queues[request.queue_type].append(request)

   # Returns true if both queues are empty, false otherwise. Does not acquire
   # lock before check.
   def _unsafe_empty(self):
      return len(self.queues['2']) == 0 and len(self.queues['10']) == 0

class Simulator:
   # Stores the given list of data.QueueRequest objects. 
   def __init__(self, requests):
      self.buffer = sorted(requests, key=lambda req : req.time_in)
      self.buffer.reverse()
      self.cv = Condition()
      self.requestsLeft = 0

   # Run simulation threads.
   # 'finishedCallback' is called once when all simulation
   #    threads finish.
   # 'breakTies' is a function of two arguments (two minute wait time, ten
   #    minute queue wait time) called with the wait times of the head of either
   #    queue whenever both queues contain requests. Should return either '2' or
   #    '10' to indicate the queue from which to dequeue.
   # 'regularReqts' and 'seniorReqts' are lists of required regular and senior
   #    TAs for time slot, sorted in lists by hour.
   def run(self, finishedCallback, breakTies, regularReqts, seniorReqts):
      self.queue = DoubleQueue(breakTies)
      self.report = Report(self.buffer)
      self.finished = finishedCallback
      self.regularSurplus = 0
      self.seniorSurplus = 0
      timers = self.scheduleRequests()
      timers += self.scheduleReqtChanges(regularReqts, seniorReqts)
      initialRegular = regularReqts[0]
      initialSenior = seniorReqts[0]
      for i in range(initialRegular + initialSenior):
         Thread(target=self.serve, args=(i >= initialRegular,)).start()
      for t in timers:
         t.start()

   # Attempt to serve incoming requests until none are left.
   def serve(self, senior=False):
      # Print a message above a TA beginning or ending work.
      def printChange(action):
         print '{0} TA {1}.'.format('Senior' if senior else 'Normal', action) 

      # Print a message noting that the given request has been served.
      def printServed(request):
         params = (request, self.requestsLeft)
         print 'served request %s. %d requests left.' % params

      printChange('beginning')
      while self.requestsLeft > 0:
         with self.cv:
            while self.queue.empty() and self.requestsLeft > 0:
               self.cv.wait()
            if self._handleSurplus(senior):
               printChange('finishing')
               return
            request = self.queue.get(self.report)
         if request != None:
            self.requestsLeft -= 1
            printServed(request)
            # Help the student for exactly the amount of time for that queue (2
            # minutes or 10 minutes).
            self.report.recordTimeOut(request)
            workingTime = float(getHelpTime(request.queue_type)) / SPEED_FACTOR
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
   # Each returned timer fires at a certain hour, incrementing or decrementing
   # the regular or senior TA requirements.
   def scheduleReqtChanges(self, regularReqts, seniorReqs):
      # Returns a sequence of differences between consecutive elts in 'reqs'.
      def getDeltas(reqs):
         deltas = []
         for i in range(1, len(reqs)):
            deltas.append(reqs[i - 1] - reqs[i])
         return deltas
      timers = []
      deltas = zip(getDeltas(regularReqts), getDeltas(seniorReqs))
      hour = 1
      for total, senior in deltas:
         time = float(hour * 3600) / SPEED_FACTOR
         timers.append(Timer(time, self.changeSurplus, args=(total, senior)))
         hour += 1
      return timers

   # If any surplus (senior or regular) is greater than 0, spins up that many
   # worker threads and resets surpluses to 0. If either surplus is positive,
   # then the current worker resets a surplus to 0 (whichever matches it's type)
   # and returns True. Otherwise returns False.
   def _handleSurplus(self, senior):
      # Create TA threads to satisfy needs.
      while self.seniorSurplus < 0:
         self.seniorSurplus += 1
         Thread(target=self.serve, args=(True,)).start()
      while self.regularSurplus < 0:
         self.regularSurplus += 1
         Thread(target=self.serve, args=(False,)).start()

      # Return true to indicate "leaving work" if no longer needed.
      if self.seniorSurplus > 1 and senior:
         self.seniorSurplus -= 1
         return True
      if self.regularSurplus > 1 and not senior:
         self.regularSurplus -= 1
         return True
      return False

   # Changes the total and senior TA surplus by the provided deltas.
   def changeSurplus(self, totalChange, seniorChange):
      with self.cv:
         print 'Staffing change: ({0}, {1}).'.format(totalChange, seniorChange)
         self.regularSurplus += totalChange
         self.seniorSurplus += seniorChange

   # Schedules the request times. Returns a list of timers, one per request.
   # Once started, each request is made at the times specified in the request's
   # 'time_in' field relative to the first request (which is made immediately).
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
