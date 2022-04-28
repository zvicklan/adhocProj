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
from ackFuncs import *
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
#parser.add_argument('filename') #, type=str, nargs ='+', action = 'store', help='to use as logfile name')
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

#Make logging file
logDir = '../log/'
os.makedirs(logDir, exist_ok=True)
filename = getFileTimeStamp() # Because python is the worst: args.filename #sys.argv[1] # 
log = open(logDir + 'log_' + str(myID) + '_' + filename + '.csv', 'w', newline='')
logger = csv.writer(log)

# And logging for the screen
file = logging.FileHandler("stdLog_" + str(myID) + '_' + timeStamp + '.csv')
logging.addHandler(file)

logging.info("Received ID " + str(myID))

#Setup node information and internal memory state
maxID = 5 #b/c we know the # of nodes
numMsgTypes = 4
numDests = 10
forceRouting = 1

msgIDs = [1] * numMsgTypes
hops2Node = [0] * maxID # Will store the num hops
path2Node = [0] * maxID # Will store the node

#Create a struct for tracking the last msg we've seen from each node
lastMsgIDs = [[0 for i in range(numMsgTypes)] for j in range(maxID)]

# Start listening:
rxdevice.enable_rx()

#Create acknowledgement structure (msg, lastTime, count)
ackList = []
reTxInterval = 1 #sec
maxTxCount = 3

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
    #Before listening loop
    # Check if we need to re-send any un-acknowledged messages
    reTxMsg = hasStaleAck(ackList)
    if reTxMsg:
        #If it's too far gone, we need to mark it out and drop it
        if isDead(ackList, reTxMsg):
            #Get the node that didn't respond to us
            origID, msgID, srcID, destID, hopCount, pathFromOrig = readMsg(reTxMsg)
            wholePath = getWholePath(origID, pathFromOrig, destID)
            badDestID = getNextNode(wholePath, myID)

            # Fix the cache and send out a drop            
            removeLinkFromCache(path2Node, badSrcID, badDestID, logging)
            dropMsg = makeMsgRouteDrop(origID, msgID, myID, badDestID, pathFromOrig)
            sendMsg(txdevice, dropMsg, rxdevice, logging, logger)

            # Then to keep things interesting, start sending again
            if myID == origID and (myID == 5 or myID == 1): #Send a new route disc
                msg = makeMsgRouteDisc(myID, msgIDs[0], myID, 6-myID, []) #send to opposite side
                msgIDs[0] = (msgIDs[0] + 1) % 16
                sendMsg(txdevice, msg, rxdevice, logging, logger) #auto RX blanking
        else:
            #Re-send it
            sendMsg(txdevice, msg, rxdevice, logging, logger) #auto RX blanking
            ackList = updateAckList(ackList, reTxMsg)

    # Now see if we have a new msg
    if rxdevice.rx_code_timestamp != timestamp:
        (timestamp, rxMsg, msgType) = loadNewMsg(rxdevice, timestamp, logging)
        logging.info(hex(rxMsg) +
                     " [pulselength " + str(rxdevice.rx_pulselength) +
                     ", protocol " + str(rxdevice.rx_proto) +
                     ", msgType " + str(msgType) + "]") #print all msgs
        
        #We will do processing if this is a real message
        if not msgType: #ignore msgs not part of the system
            continue

        #Check if this is an ACK
        ackedMsg = isAwaitingAck(ackList, rxMsg) #returns 0 if not an ACK
        if ackedMsg: 
            #If so, mark it as done
            logging.info("Received ACK msg " + hex(rxMsg) + " for awaiting " + hex(ackedMsg))
            ackList = removeAck(ackList, ackedMsg)
            
        #Log if desired
        if logger != 'None':
            logMsg(rxMsg, logger, 1) # 1 means "in"


        ##########################
        if msgType == ROUT_DISC: #Route Discovery
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgRouteDisc(rxMsg)
            if forceRouting and not (srcID == myID + 1 or srcID == myID - 1): #Force routing
                continue
            wholePath = getWholePath(origID, pathFromOrig, destID)

            #Check if we've seen it - Need to allow for multiple paths coming in
            lastMsgIDs, isNew = checkLastMsg(lastMsgIDs, ROUT_DISC, origID, msgID)
            
            if origID == myID and not isAckMsg(rxMsg): #Ignore our own msgs (or replies to them)
                continue
            
            if not isNew and destID != myID: #duplicate, not for me
                continue
            
            else: # I want it!
                if destID == myID: #It's for me! Let's send a reply
                    #If this is a shorter path than I previously had, or it's a new msg
                    if hops2Node[srcID-1] > hopCount or isNew:
                        #Update the cache
                        logging.info("Got Route Disc for me !!! !!!")
                        path2Node, hops2Node = updateCache(path2Node, hops2Node, myID, wholePath, logging)
                        #Make and send a new msg
                        replyMsg = makeMsgRouteReply(origID, msgID, myID, destID, pathFromOrig)
                        sendMsg(txdevice, replyMsg, rxdevice, logging, logger) #auto RX blanking
                        ackList = addAck(ackList, replyMsg, reTxInterval, maxTxCount)
                        
                else: # We want to forward along the route disc
                    # Check that we aren't on the path already, then send it!
                    if myID in wholePath:
                        continue #We don't want to create endless loops

                    #add myself to list and forward along
                    logging.info("Not for me. Forwarding along")
                    pathFromOrig.append(myID) 
                    msg = makeMsgRouteDisc(origID, msgID, myID, destID, pathFromOrig)
                    sendMsg(txdevice, msg, rxdevice, logging, logger) #auto RX blanking

        ##########################
        if msgType == ROUT_REPL: #Route Reply
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgRouteReply(rxMsg)
            if forceRouting and not (srcID == myID + 1 or srcID == myID - 1): #Force routing
                continue
            wholePath = getWholePath(origID, pathFromOrig, destID)

            # We should be right before the sender (route backwards for replies)
            imNext = nextInPath(origID, destID, pathFromOrig, myID, srcID)
            # If not, pass
            if not imNext:
                continue

            #Send the ACK - even if not new (so before checking newness)
            sendAck(txdevice, rxMsg, rxdevice, logging, logger)
            
            #Mark this one done (using lastMsg)
            lastMsgIDs, isNew = checkLastMsg(lastMsgIDs, ROUT_REPL, origID, msgID)
            if not isNew:
                continue #skip if we've seen this one before
                        
            #Print the message!
            logging.info("Received Route Reply from node " + str(srcID) +
                         " with path " + str(wholePath))
            path2Node, hops2Node = updateCache(path2Node, hops2Node, myID, wholePath, logging)
            
            if origID == myID: # We got a response!
                #Send a data msg!
                path = path2Node[destID-1]
                dataMsg = makeMsgData(origID, msgIDs[2], myID, destID, path[1:-1])
                msgIDs[2] = (msgIDs[2] + 1) % 16
                sendMsg(txdevice, dataMsg, rxdevice, logging, logger)
                ackList = addAck(ackList, dataMsg, reTxInterval, maxTxCount)
                
            else: # Otherwise, forward it along!
                replyMsg = makeMsgRouteReply(origID, msgID, myID, destID, pathFromOrig)
                sendMsg(txdevice, replyMsg, rxdevice, logging, logger) #auto RX blanking
                ackList = addAck(ackList, replyMsg, reTxInterval, maxTxCount)

        #########################
        if msgType == DATA_MSG: #Data Message
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgData(rxMsg)
            if forceRouting and not (srcID == myID + 1 or srcID == myID - 1): #Force routing
                continue
            #Forward the message if your predecessor in the list sent
            wholePath = getWholePath(origID, pathFromOrig, destID)

            #If it's not for you, pass
            if srcID not in wholePath:
                continue
            
            #Only send if I'm the next stop in the route
            imNext = nextInPath(origID, destID, pathFromOrig, srcID, myID)
            #If i'm next, acknowledge no matter what:
            if imNext:
                sendAck(txdevice, rxMsg, rxdevice, logging, logger)

                if destID == myID: #It's for me!
                    #Mark this one done (using lastMsg)
                    lastMsgIDs, isNew = checkLastMsg(lastMsgIDs, DATA_MSG, origID, msgID)
                    if isNew:
                        logging.info("Received data msg from node " + str(origID))
                        #Send a data msg back!
                        path = path2Node[origID-1]
                        msgID = msgIDs[2]
                        msgIDs[2] = (msgIDs[2] + 1) % 16
                        dataMsg = makeMsgData(myID, msgID, myID, origID, path[1:-1])
                
                else:
                    #Mark this one done (using lastMsg)
                    lastMsgIDs, isNew = checkLastMsg(lastMsgIDs, DATA_MSG, origID, msgID)
                    if not isNew: #skip if this is a duplicate
                        continue
                    
                    # Otherwise I send it along!                
                    logging.info("Forwarding msg from node " + str(srcID))
                    dataMsg = makeMsgData(origID, msgID, myID, destID, pathFromOrig) #update the sourceID
                    
                # Share the sending code - shorter
                sendMsg(txdevice, dataMsg, rxdevice, logging, logger)
                ackList = addAck(ackList, dataMsg, reTxInterval, maxTxCount) #Add to ACK list

        ##########################
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
                removeLinkFromCache(path2Node, badSrcID, badDestID, logging)

                #And forward the message
                dropMsg = makeMsgRouteDrop(origID, msgID, myID, badDestID, pathFromOrig)
                sendMsg(txdevice, dropMsg, rxdevice, logging, logger)

                if myID == origID and (myID == 5 or myID == 1): #Send a new route disc
                    msg = makeMsgRouteDisc(myID, msgIDs[0], myID, 6-myID, []) #send to opposite side
                    msgIDs[0] = (msgIDs[0] + 1) % 16
                    sendMsg(txdevice, msg, rxdevice, logging, logger) #auto RX blanking

    # Do a token wait between loops to avoid using all the power
    time.sleep(0.01)
    
#Stop receive
rxdevice.disable_rx()

#Clean up before exiting
rxdevice.cleanup()
txdevice.cleanup()

