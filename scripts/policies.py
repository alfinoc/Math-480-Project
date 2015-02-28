from random import random

# Returns a 'break ties' function for the simulator that chooses to dequeue
# from the 2 or 10 minute queue if either is above given thresholds. If
# neither or both is above given thresholds, the 'break ties' function returns
# a random choice, with odds 'twoMinPref':1 in favor of the 2-min queue.
def crisisThresholdsAndFlip(twoMinWaitTreshold, tenMinWaitThreshold, twoMinPref):
   def breakTies(twoMinWait, tenMinWait):
      twoMinCrisis = twoMinWait > float(twoMinWaitTreshold)
      tenMinCrisis = tenMinWait > float(tenMinWaitThreshold)
      if twoMinCrisis and not tenMinCrisis:
         return '2'
      elif tenMinCrisis and not twoMinCrisis:
         return '10'

      # Either both or neither queues is in dire need. Choose randomly
      # according to customizable odds.
      elif random() < 1.0 / (twoMinPref + 1):
         return '10'
      else:
         return '2'
   return breakTies
