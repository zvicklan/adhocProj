#!/usr/bin/env python3
import time
from datetime import datetime
from msgFunctions import *

#In form [msg, lastTx, count, reTxInterval, maxTxCount]

def getAckCount(ackList, msg):
    #Returns count if msg in ackList
    for thisAck in ackList:
        if thisAck[0] == msg:
            return thisAck[2]
    #else
    return 0

def getMaxTxCount(ackList, msg):
    #Returns maxTxCount if msg in ackList
    for thisAck in ackList:
        if thisAck[0] == msg:
            return thisAck[4]
    #else
    return 0

def getLastTx(ackList, msg):
    #Returns lastTx if msg in ackList
    for thisAck in ackList:
        if thisAck[0] == msg:
            return thisAck[1]
    #else
    return 0

def hasStaleAck(ackList):
    #Are any Acks out on their time?
    newNow = datetime.now()
    for thisAck in ackList:
        tDelta = newNow - thisAck[1]
        reTxInterval = thisAck[3]
        if tDelta.total_seconds() > reTxInterval:
            return thisAck[0]
    #else
    return 0

def isStale(ackList, msg):
    # Is this Ack stale?
    newNow = datetime.now()
    for thisAck in ackList:
        tDelta = newNow - thisAck[1]
        reTxInterval = thisAck[3]
        if tDelta.total_seconds() > reTxInterval:
            return msg
    #else
    return 0

def isDead(ackList, msg):
    # Check if the msg is dead (assume not getting an Ack)
    retVal = 0
    if getAckCount(ackList, msg) > getMaxTxCount(ackList, msg):
        retVal = 1
    #And return
    return retVal

def updateAckList(ackList, msg):
    #Updates the count and time
    for thisAck in ackList:
        if thisAck[0] == msg:
            #We found it!
            thisAck[1] = datetime.now()
            thisAck[2] = thisAck[2] + 1
    # Not necessary to return, but much easier to read
    return ackList

def addAck(ackList, msg, reTxInterval, maxTxCount, logging="None"):
    #Adds a new acknowledgement
    if logging != "None":
        logging.info("AddAck: msg is " + hex(msg))
        
    if len(ackList) == 0:
        ackList = [[msg, datetime.now(), 1, reTxInterval, maxTxCount]]
    else:
        ackList = ackList + [[msg, datetime.now(), 1, reTxInterval, maxTxCount]]
    # And return
    return ackList

def removeAck(ackList, msg):
    #Remove the acknowledgement
    newList = [thisAck for thisAck in ackList if thisAck[0] != msg]
    # And return
    return newList

def isAwaitedAck(ackList, msg):
    #Returns 1 if this is something I've been waiting for
    for thisAck in ackList:
        if isMyAck(thisAck[0], msg):
            return thisAck[0]
    #else
    return 0

def isMyAck(txMsg, rxMsg):
    #Take in a msg and return True if it's the Ack msg for the other

    itsMyAck = 0

    #Parse the Tx Message
    origID, msgID, srcID, destID, hopCount, pathFromOrig = readMsg(txMsg)
    msgType = getMsgType(txMsg)
    
    #And parse the Rx Msg
    toParse = deAckMsg(rxMsg) #returns rxMsg if rxMsg not an ACK        
    origID_rx, msgID_rx, srcID_rx, destID, hopCount, pathFromOrig = readMsg(toParse)
    msgType_rx = getMsgType(rxMsg)
    
    #Logic for Route Disc/Route Reply
    if msgType == 1 and msgType_rx == 2:
        if origID == srcID: #Ensure this was my Route Disc
            if (origID_rx, msgID_rx) == (origID, msgID): #same msg
                imNext = nextInPath(origID, destID, pathFromOrig, origID, srcID_rx)
                if imNext:
                    #It's the same msg! We got it!
                    itsMyAck = 1
    elif msgType_rx == msgType and isAckMsg(rxMsg):
        if (origID, msgID, srcID) == (origID_rx, msgID_rx, srcID_rx):
            #It's the same msg! We got it!
            itsMyAck = 1
    #And return
    return itsMyAck

def nextInPath(origID, destID, pathFromOrig, node1, node2):
    #Builds the complete path, then checks if I'm next
    wholePath = pathFromOrig.copy()
    wholePath.insert(0, origID)
    wholePath.append(destID) # Now this is the whole path   

    # We should be right before the sender
    if node1 not in wholePath or node2 not in wholePath:
        imNext = 0
    else: #they're at least in the path
        node1Ind = wholePath.index(node1)
        node2Ind = wholePath.index(node2)

        imNext = node2Ind == (node1Ind + 1)

    return imNext
