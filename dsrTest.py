#!/usr/bin/env python3

import argparse
import signal
import sys
import time
import logging
import os
import csv

from rpi_rf import RFDevice
from msgFunctions import *
from ioFunctions import *
from cacheFunctions import *
from random import *
import numpy as np
import faulthandler

rxdevice = None
txdevice = None

# pylint: disable=unused-argument
def exithandler(signal, frame):
    rxdevice.cleanup()
    txdevice.cleanup()
    sys.exit(0)

#Logging setup
logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)-15s.%(msecs)03d - [%(levelname)s] %(module)s: %(message)s', )

#For naming log file
#parser = argparse.ArgumentParser(description='Ad Hoc Routing via DSR')
#parser.add_argument('filename', nargs ='+', action = 'store')
#args = parser.parse_args()

faulthandler.enable()

# RX setup
rxdevice = rxSetup()

# TX setup
txdevice = txSetup()

signal.signal(signal.SIGINT, exithandler)

#Set up constants
ROUT_DISC = 1
ROUT_REPL = 2
DATA_MSG = 3
ROUT_DROP = 4

#Set up my info
file = open('idNum.txt', 'r')
line = file.readlines()
myID = int(line[0])
logging.info("Received ID " + str(myID))

#Make logging file
logDir = '../log/'
os.makedirs(logDir, exist_ok=True)
filename = getFileTimeStamp() #If no input, use a timestamp
log = open(logDir + 'log_' + str(myID) + '_' + filename + '.csv', 'w', newline='')
logger = csv.writer(log)

#Setup node information and internal memory state
maxID = 5 #b/c we know the # of nodes
numMsgTypes = 4
numDests = 10

msgIDs = [1] * numMsgTypes
hops2Node = [0] * maxID # Will store the num hops
path2Node = [0] * maxID # Will store the node

#Create a struct for tracking the last msg we've seen from each node
lastMsgIDs = [[0 for i in range(numMsgTypes)] for j in range(maxID)]

# Start listening:
rxdevice.enable_rx()

if myID == 1: #We'll have the first guy kick this off
    msgDests = genDests(numDests, myID)
    #Send a Route Discovery msg (just as a test)
    destNode = msgDests[0]

    destNode = 5 #for testing
    msg = makeMsgRouteDisc(myID, msgIDs[0], myID, destNode, [])
    msgIDs[0] = (msgIDs[0] + 1) % 16
    sendMsg(txdevice, msg, rxdevice, logging, logger) #auto RX blanking

timestamp = None
logging.info("Listening for codes on GPIO")

#TODO: Need to figure out a plan for logic to create messages
#  Might just be spamming msgs 1->5
msgBuffer = genDests(numDests, myID)

#Listening loop
testDone = False
while not(testDone):
    if rxdevice.rx_code_timestamp != timestamp:
        (timestamp, rxMsg, msgType) = loadNewMsg(rxdevice, timestamp, logging)
        logging.info(hex(rxMsg) +
                     " [pulselength " + str(rxdevice.rx_pulselength) +
                     ", protocol " + str(rxdevice.rx_proto) +
                     ", msgType " + str(msgType) + "]")
        
        #We will do processing if this is a real message
        if not msgType: #ignore msgs not part of the system
            continue
        
        if msgType and isAckMsg(rxMsg): #It's a real msg and an ACK (I'm not in the right state, so skip)
            continue
        #Log if desired
        if logger != 'None':
            logMsg(rxMsg, logger, 1) # 1 means "in"
            
        if msgType == ROUT_DISC: #Route Discovery
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgRouteDisc(rxMsg)
            wholePath = getWholePath(origID, pathFromOrig, destID)

            #Check if we've seen it - Need to allow for multiple paths coming in
            lastMsgIDs, isNew = checkLastMsg(lastMsgIDs, ROUT_DISC, origID, msgID)
            
            if origID == myID: #Ignore our own msgs (or replies to them)
                continue
            
            if not isNew and destID != myID: #duplicate, not for me
                continue
            else: #add it to the list
                if destID == myID: #It's for me! Let's send a reply
                    #If this is a shorter path than I previously had, or it's a new msg
                    if hops2Node[srcID-1] > hopCount or isNew:
                        path2Node, hops2Node = updateCache(path2Node, hops2Node, myID, wholePath)
                        logging.info("Got Route Disc for me. Updated routing cache to "
                                     + str(path2Node))
                        msg = makeMsgRouteReply(origID, msgID, myID, destID, pathFromOrig)
                        sendMsgWithAck(txdevice, msg, rxdevice, logging, logger) #auto RX blanking
                        
                else: # We want to forward along the route disc
                    # Check that we aren't on the path already, then send it!
                    if myID in wholePath:
                        continue #We don't want to create endless loops
                    
                    pathFromOrig.append(myID) #add myself in the first available 0 spot
                    msg = makeMsgRouteDisc(origID, msgID, myID, destID, pathFromOrig)
                    logging.info("Not for me. Forwarding along")
                    sendMsg(txdevice, msg, rxdevice, logging, logger) #auto RX blanking
            
        if msgType == ROUT_REPL: #Route Reply
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgRouteReply(rxMsg)
            wholePath = getWholePath(origID, pathFromOrig, destID)
            
            #Capture the info as long as we're involved
            if myID not in wholePath:
                continue #Skip if it's not something involving us

            # We should be right before the sender (route backwards for replies)
            imNext = nextInPath(origID, destID, pathFromOrig, myID, srcID)
            
            if imNext:
                #Mark this one done (using lastMsg)
                lastMsgIDs, isNew = checkLastMsg(lastMsgIDs, ROUT_REPL, origID, msgID)
                if not isNew:
                    continue #skip if we've seen this one before
                
                #Send the ACK
                sendAck(txdevice, rxMsg, rxdevice, logging, logger)
                
                #Print the message!
                path2Node, hops2Node = updateCache(path2Node, hops2Node, myID, wholePath)
                logging.info("Received Route Reply from node " + str(srcID) +
                             " with path " + str(wholePath))
                logging.info("Updated routing cache to " + str(path2Node))
                
                if origID == myID: # We got a response!
                    #Send a data msg!
                    path = path2Node[destID-1]
                    dataMsg = makeMsgData(origID, msgID, myID, destID, path[1:-1])
                    ackRcvd = sendMsgWithAck(txdevice, dataMsg, rxdevice, logging, logger)
                    if not ackRcvd:
                        #The path broke! Send an update
                        badDestID = getNextNode(wholePath, myID)
                        logging.info("ACK Failed. Removing bad link " + str(myID) + "->" + str(badDestID) +
                                     " from route cache. ")
                        removeLinkFromCache(path2Node, myID, badDestID)
                        logging.info("Updated routing cache to " + str(path2Node))
                        dropMsg = makeMsgRouteDrop(origID, msgID, myID, badDestID, pathFromOrig)
                        sendMsg(txdevice, dropMsg, rxdevice, logging, logger)
                        lastMsgIDs[origID-1][3] = msgID
                    
                else: # Check if it's our turn to send this msg (comes from the previous person)
                    # Then forward it along!
                    msg = makeMsgRouteReply(origID, msgIDs[1], myID, destID, pathFromOrig)
                    msgIDs[1] = (msgIDs[1] + 1) % 16
                    sendMsgWithAck(txdevice, msg, rxdevice, logging, logger) #auto RX blanking

        if msgType == DATA_MSG: #Data Message
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgData(rxMsg)
            #Forward the message if your predecessor in the list sent
            wholePath = getWholePath(origID, pathFromOrig, destID)

            #Error checking that we should be getting this message
            if srcID not in wholePath:
                logging.info("Not in route " + str(wholePath))
                continue
            
            senderInd = wholePath.index(srcID) #Who this came from
            #Only send if I'm the next stop in the route
            #If i'm next, acknowledge no matter what:
            if wholePath[senderInd + 1] == myID:
                sendAck(txdevice, rxMsg, rxdevice, logging, logger)
                
            if destID == myID and wholePath[senderInd + 1] == myID: #It's for me!
                #Mark this one done (using lastMsg)
                lastMsgIDs, isNew = checkLastMsg(lastMsgIDs, DATA_MSG, origID, msgID)
                if isNew:
                    logging.info("Received data msg from node " + str(origID))
                    #Send a data msg back!
                    path = path2Node[origID-1]
                    msgID = msgIDs[2]
                    msgIDs[2] = (msgIDs[2] + 1) % 16
                    dataMsg = makeMsgData(myID, msgID, myID, origID, path[1:-1])
                    ackRcvd = sendMsgWithAck(txdevice, dataMsg, rxdevice, logging, logger)
                
            elif senderInd < len(wholePath) - 1 and wholePath[senderInd + 1] == myID:
                #Mark this one done (using lastMsg)
                sendAck(txdevice, rxMsg, rxdevice, logging, logger) #Send the ACK
                lastMsgIDs, isNew = checkLastMsg(lastMsgIDs, DATA_MSG, origID, msgID)
                if not isNew: #skip if this is a duplicate
                    continue
                
                #Then I send it along!                
                dataMsg = makeMsgData(origID, msgID, myID, destID, pathFromOrig) #update the sourceID
                logging.info("Forwarding msg from node " + str(srcID))

                ackRcvd = sendMsgWithAck(txdevice, dataMsg, rxdevice, logging, logger)
                if not ackRcvd:
                    #The path broke! Send an update
                    badDestID = getNextNode(wholePath, myID)
                    logging.info("ACK Failed. Removing bad link " + str(myID) + "->" + str(badDestID) +
                                 " from route cache. ")
                    removeLinkFromCache(path2Node, myID, badDestID)
                    logging.info("Updated routing cache to " + str(path2Node))
                    dropMsg = makeMsgRouteDrop(origID, msgID, myID, badDestID, pathFromOrig)
                    sendMsg(txdevice, dropMsg, rxdevice, logging, logger)
                    lastMsgIDs[origID-1][3] = msgID

        if msgType == ROUT_DROP: #Drop Message
            origID, msgID, srcID, badDestID, hopCount, pathFromOrig = readMsgRouteDrop(rxMsg)
            #Check we haven't seen it already
            lastMsgIDs, isNew = checkLastMsg(lastMsgIDs, ROUT_DROP, origID, msgID)

            if not isNew: #TODO this has serious wrap-around issues I think. Need to clear this somehow
                continue
            else:
                #I want to clean my route cache
                wholePath = getWholePath(origID, pathFromOrig, badDestID)
                badSrcID = getPrevNode(wholePath, badDestID)
                logging.info("Removing bad link " + str(badSrcID) + "->" + str(badDestID) +
                             " from route cache. ")
                removeLinkFromCache(path2Node, badSrcID, badDestID)
                logging.info("Updated routing cache to " + str(path2Node))

                #And forward the message
                dropMsg = makeMsgRouteDrop(origID, msgID, myID, badDestID, pathFromOrig)
                sendMsg(txdevice, dropMsg, rxdevice, logging, logger)
                
    time.sleep(0.01)
    
#Stop receive
rxdevice.disable_rx()

#Clean up before exiting
rxdevice.cleanup()
txdevice.cleanup()

