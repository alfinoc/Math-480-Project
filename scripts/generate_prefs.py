from sys import argv
from preferences import getRandomTAPreferenceMap, serialize
from json import dumps

NUM_TAS = 10
try:
   NUM_TAS = int(argv[1])
except:
   pass

tas = []
for i in range(NUM_TAS):
   prefMap = getRandomTAPreferenceMap()
   tas.append(serialize(prefMap))
print dumps({'prefs': tas})
