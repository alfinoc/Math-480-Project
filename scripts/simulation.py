from threading import Timer, Thread, Lock, Condition
from time import sleep
from Queue import Queue
from data import QueueData
from sys import stdout

# 1 is real time, which would take roughly 9 hours.
SPEED_FACTOR = 9 * 60 * 2

class TAPool:
   def __init__(self, regular, senior):
      self.regular = regular
      self.available = [True] * (regular + senior)
      self.lock = Lock()

   # Records that one randomly chosen TA is busy working. Returns None if no TAs are
   # available. Otherwise return a tuple (ID, seniority) where seniority is True if
   # the TA with the returned ID is a senior TA and false otherwise. The ID is to be
   # used with the reenter method.
   def checkout(self):
      with self.lock:
         available = filter(lambda ta : self.available[ta], range(len(self.available)))
         if len(available):
            return None
      result = choice(available)
      self.available[result] = False
      return (result, Senior)

   def reenter(self, id):
      if id < 0 or id >= len(self.available):
         raise ValueError('Bad TA id ' + str(id))
      with self.lock:
         available[id] = True

class Simulator:
   # Stores the given list of data.QueueRequest objects.
   def __init__(self, requests, regularTAs, seniorTAs):
      #self.twoMinute = Queue()
      self.tenMinute = Queue()
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
         ta.daemon = True
         ta.start()
      print '   TAs born and waiting.'
      start()

   # Attempt to serve incoming requests until none are left.
   def serve(self):
      while self.requestsLeft > 0:
         self.cv.acquire()
         while self.tenMinute.empty():
            self.cv.wait()
         request = self.tenMinute.get()
         self.cv.release()
         if request != None:
            print '   answered question ' + str(request)
            self.requestsLeft -= 1
            # Help the student for exactly the amount of time for that queue
            # (2 minutes or 10 minutes).
            sleep(float(request.queue_type) * 60 / SPEED_FACTOR)

   # Fills the queues with the stored requests at the times specified
   # in each requests 'time_in' field relative to the first request (which
   # is made immediately). Time is scaled according to SPEED_FACTOR.
   def scheduleRequests(self):
      if len(self.buffer) == 0:
         raise ValueError('No requests to schedule!')
      self.requestsLeft = len(self.buffer)
      first = self.buffer[len(self.buffer) - 1].time_in
      timers = []
      for req in self.buffer:
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
      #if request.queue_type == "2":
      #   self.twoMinute.put(request)
      #else:
      self.cv.acquire()
      self.tenMinute.put(request)
      self.cv.notify()
      self.cv.release()
