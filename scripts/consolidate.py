from sys import argv

print 'reading files:'
for filename in argv[1:]:
   print '   ' + filename

# Reads a sequence of line-separated floats from the file with given name.
def toVector(filename):
   file = open(filename)
   res = []
   for line in file:
      res.append(float(line))
   return res

# Computes the mean vector of the given array of 'vectors', which the ith 
# element in the returned vector is the mean of the ith element of each
# in 'vectors.'
def mean(vectors):
   result = []
   vectLen = len(vectors[0])
   numVect = len(vectors)
   for i in range(vectLen):
      result.append(float(sum([ vectors[j][i] for j in range(numVect) ])) / numVect)
   return result

# Print 
delays = mean(map(toVector, argv[1:]))
for d in delays:
   print d
