from sys import argv, exit
from random import choice, randint, gammavariate
from conf import *

NUM_CLASSES = range(2, 4)
NUM_SECTIONS = range(1, 2)

def blackoutDays(preferences, days, hour):
   for day in days:
      if hour < len(preferences[day]):
         preferences[day][hour] = 0

def blackoutMWF(preferences, hour):
   blackoutDays(preferences, ['Monday', 'Wednesday', 'Friday'], hour)

def blackoutTTh(preferences, hour):
   blackoutDays(preferences, ['Tuesday', 'Thursday'], hour)

def normalize(vector):
   m = max(vector)
   return map(lambda x : float(x) / m, vector)

def preferenceMap():
   preferences = {}
   for day in HOURS:
      preferences[day] = [1] * HOURS[day]
   return preferences

def blackoutCourses(preferences):
   # Black out some MWF lectures.
   chosen = set()
   for i in range(choice(NUM_CLASSES)):
      hour = choice(list(set(range(5)) - chosen))
      chosen.add(hour)
      blackoutMWF(preferences, hour)

   # Black out some TTh Sections
   chosen = set()
   for i in range(choice(NUM_SECTIONS)):
      hour = choice(list(set(range(5)) - chosen))
      chosen.add(hour)
      blackoutTTh(preferences, hour)
   return preferences

def preferenceVector(size, peak, samples=1000):
   if peak >= size:
      raise ValueError('peak index out of range')
   overlay = [1] * size
   for i in range(samples):
      point = int(gammavariate(float(peak) / 3, 3))
      if (0 <= point and point < size):
         overlay[point] += 1
   return normalize(overlay)

def getRandomTAPreferenceMap():
   prefs = preferenceMap()
   blackoutCourses(prefs)
   for day in prefs:
      hours = len(prefs[day])
      vect = preferenceVector(hours, randint(1, hours - 1))
      for i in range(hours):
         prefs[day][i] *= vect[i]
   return prefs

def serialize(prefMap):
   result = []
   for day in prefMap:
      result += prefMap[day]
   return result

def deserialize(prefList):
   result = preferenceMap()
   index = 0
   for day in result:
      for i in range(len(result[day])):
         result[day][i] = prefList[index]
         index += 1
   return result

NUM_TAS = 10
try:
   NUM_TAS = int(argv[1])
except:
   pass

for i in range(NUM_TAS):
   prefMap = getRandomTAPreferenceMap()
   print serialize(prefMap)




