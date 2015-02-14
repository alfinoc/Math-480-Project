from sys import argv
from preferences import getRandomTAPreferenceMap, serialize

NUM_TAS = 10
try:
   NUM_TAS = int(argv[1])
except:
   pass

for i in range(NUM_TAS):
   prefMap = getRandomTAPreferenceMap()
   print serialize(prefMap)
