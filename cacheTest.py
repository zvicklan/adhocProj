import csv
import sys
from importlib import reload
sys.path.append("D:/Documents/2021/CMU/04sprin/Networks/Projects/Proj2/Pi")
import cacheFunctions
reload(cacheFunctions)
from cacheFunctions import *

#Remove tests
path = [0, 0, 0]
a = remove0s(path)
print(a)
path = [1, 0, 0]
a = remove0s(path)
print(a)

#updateCache tests
cache = [8]*5
hops2Node = [0] * 5
node = 1
path=[1, 2,3,4, 5]
updateCache(cache, hops2Node, node, path)
print(cache)
print(hops2Node)

cache = [8]*5
hops2Node = [0] * 5
updateCache(cache, hops2Node, 2, path)
print(cache)
print(hops2Node)

cache = [8]*5
hops2Node = [0] * 5
updateCache(cache, hops2Node, 3, path)
print(cache)
print(hops2Node)

cache = [8]*5
hops2Node = [0] * 5
updateCache(cache, hops2Node, 4, path)
print(cache)
print(hops2Node)

cache = [8]*5
hops2Node = [0] * 5
updateCache(cache, hops2Node, 5, path)
print(cache)
print(hops2Node)

#genDests tests
a = genDests(10, 1)
print(a)
a = genDests(10, 3)
print(a)
a = genDests(1, 3)
print(a)

#getWholePath tests
print(getWholePath(1, [2,3,4], 5))
print(getWholePath(1, [2,3,4], 3))

#getPrevNode tests
print(getPrevNode([5,4,3,2,1], 1))
print(getPrevNode([5,4,3,2,1], 2))
print(getPrevNode([5,4,3,2,1], 3))
print(getPrevNode([5,4,3,2,1], 4))

#getNextNode tests
print(getNextNode([5,4,3,2,1], 5))
print(getNextNode([5,4,3,2,1], 4))
print(getNextNode([5,4,3,2,1], 3))
print(getNextNode([5,4,3,2,1], 2))

#removeLinkFromCache tests
cache = [[5, 4, 3, 2, 1], [5, 4, 3, 2], [5, 4, 3], [5, 4], 8]

print(removeLinkFromCache(cache, 4, 3))
