#!/usr/bin/env python3
import time
from random import *

def remove0s(path):
    #To help wipe the paths that we receive from useless stuff
    newPath = [node for node in path if node != 0]

    return newPath

def updateCache(cache, hops2Node, myNode, orig, dest, path):
    #Updates the cache using the info from the path
    wholePath = path.copy()
    wholePath.insert(0, orig)
    wholePath.append(dest)

    myInd = wholePath.index(myNode)

    numNodes = len(wholePath)
    reversePath = wholePath.copy()
    reversePath.reverse()
    #Loop through the list and add everything
    for ii in range(numNodes):
        node = wholePath[ii]
        if node == myNode:
            continue
        else: #Add info to the cache
            if ii < myInd:
                subPath = reversePath[numNodes-myInd : numNodes-ii]
            elif ii > myInd:
                subPath = wholePath[myInd + 1 : ii + 1]
        cache[node-1] = subPath
        hops2Node[node-1] = len(subPath)
    
    return cache
            
def genDests(numDests, myID):
    #Create a numDests vector of destinations, excluding myID
    maxID =5
    outVec = [0]*numDests
    
    for ii in range(numDests): #Create each random number
        destNode = myID
        while destNode == myID: #b/c we want to send to someone else
            destNode = randint(1,maxID)
        outVec[ii] = destNode

    return(outVec)
