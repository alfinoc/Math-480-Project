# Returns a list of pairs (delta, event time), where delta is either 1 or -1 to
# indicate a request entering or exiting the queue at that event time.
def changes(requests):
   ins = map(lambda req : (1, req.time_in), requests)
   outs = map(lambda req : (-1, req.time_out), requests)
   return sorted(ins + outs, key=lambda pair : pair[1])

# Returns a list of pairs (duration, count) where duration is the time in
# between events in provided list of 'changes', and count is the number of
# requests in the queue during that interval.
def intervals(changes):
   intervals = []
   count = 0
   for i in range(len(changes) - 1):
      count += changes[i][0]
      intervals.append(((changes[i + 1][1] - changes[i][1]).seconds, count))
   return intervals

# Returns the mean number of waiting given 'requests', supposing that each was
# enqueued at it's time_in and dequeued at time_out.
def meanNumberOfWaitingRequests(requests):
   if len(requests) == 0:
      return None
   counts = intervals(changes(requests))
   weightedCountSum = sum([ duration * count for (duration, count) in counts ])
   totalDuration = sum([ duration for (duration, count) in counts ])
   return float(weightedCountSum) / totalDuration

# Returns the average arrival rate across all requests.
def arrivalRate(requests):
   first = requests[0]
   last = requests[len(requests) - 1]
   return float(len(requests)) / (last.time_in - first.time_in).seconds
