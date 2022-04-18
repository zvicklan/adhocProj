#!/usr/bin/env python3
import time
from random import *

def remove0s(path):
    #To help wipe the paths that we receive from useless stuff
    newPath = [node for node in path if node != 0]

    return newPath

def updateCache(cache, hops2Node, myNode, wholePath):

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
                subPath = reversePath[numNodes-myInd-1 : numNodes-ii]
            elif ii > myInd:
                subPath = wholePath[myInd : ii + 1]
        cache[node-1] = subPath
        hops2Node[node-1] = len(subPath)
    
    return cache, hops2Node
   
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

def getWholePath(origID, pathFromOrig, destID):
    #Creates the whole path for simplicity
    # Used for drop msgs, so ignores destID if already in list
    wholePath = pathFromOrig.copy()
    wholePath.insert(0, origID)
    if destID not in pathFromOrig:
        wholePath.append(destID) # Now this is the whole path

    return wholePath

def getPrevNode(wholePath, destID):
    #Find who transmits to the destID
    assert(destID in wholePath)

    destInd = wholePath.index(destID)
    assert(destInd > 0)
    srcID = wholePath[destInd-1]

    return srcID

def getNextNode(wholePath, srcID):
    #Find the next step
    assert(srcID in wholePath)

    destInd = wholePath.index(srcID)
    assert(destInd < len(wholePath) - 1)
    destID = wholePath[destInd+1]

    return destID

def removeLinkFromCache(cache, badSrcID, badDestID):
    #Remove all routes that contain the bad link

    cacheSize = len(cache)
    for ind in range(cacheSize):
        thisRoute = cache[ind]
        if type(thisRoute) != list: #ignore scalars
            continue
        if badSrcID in thisRoute and badDestID in thisRoute: #it uses the nodes
            srcInd = thisRoute.index(badSrcID)
            destInd = thisRoute.index(badDestID)
            if srcInd == destInd - 1 or srcInd == destInd + 1:
                #it's using the link (or its reverse (not likely))
                cache[ind] = 0 #so remove it
    return cache
