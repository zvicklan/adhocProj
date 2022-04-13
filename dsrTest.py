#!/usr/bin/env python3

import argparse
import signal
import sys
import time
import logging

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


faulthandler.enable()

# RX setup
rxdevice = rxSetup()

# TX setup
txdevice = txSetup()

signal.signal(signal.SIGINT, exithandler)


#Set up my info
file = open('idNum.txt', 'r')
line = file.readlines()
myID = int(line[0])
logging.info("Received ID " + str(myID))

#Setup node information and internal memory state
maxID = 5 #b/c we know the # of nodes
numMsgTypes = 3
numDests = 10

msgIDs = [1] * numMsgTypes
hops2Node = [0] * maxID # Will store the num hops
path2Node = [0] * maxID # Will store the node

#Create a struct for tracking the last msg we've seen from each node
lastMsg = [[0 for i in range(3)] for j in range(5)]

# Start listening:
rxdevice.enable_rx()

if myID == 1: #We'll have the first guy kick this off
    msgDests = genDests(numDests, myID)
    #Send a Route Discovery msg (just as a test)
    destNode = msgDests[0]

    destNode = 5 #for testing
    msg = makeMsgRouteDisc(myID, msgIDs[0], myID, destNode, [])
    msgIDs[0] = (msgIDs[0] + 1) % 16
    sendMsg(txdevice, msg, rxdevice, logging) #auto RX blanking

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
        if msgType and isAckMsg(rxMsg): #It's a real msg and an ACK (I'm not in the right state, so skip)
            continue
        if msgType == 1: #Route Discovery
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgRouteDisc(rxMsg)
            wholePath = pathFromOrig.copy()
            wholePath.insert(0, origID)
            wholePath.append(destID) # Now this is the whole path
            
            if origID == myID: #Ignore our own msgs (or replies to them)
                continue
            #Check if we've seen it - Need to allow for multiple paths coming in
            lastMsgID = lastMsg[origID-1][0]
            if msgID == lastMsgID and destID != myID: #duplicate, not for me
                continue
            else: #add it to the list
                lastMsg[origID-1][0] = msgID
                if destID == myID: #It's for me! Let's send a reply
                    #If this is a shorter path than I previously had, or it's a new msg
                    if hops2Node[srcID-1] > hopCount or msgID != lastMsgID:
                        path2Node, hops2Node = updateCache(path2Node, hops2Node, myID, wholePath)
                        logging.info("Got Route Disc for me. Updated routing cache to "
                                     + str(path2Node[origID-1]))
                        msg = makeMsgRouteReply(origID, msgID, myID, destID, pathFromOrig)
                        sendMsgWithAck(txdevice, msg, rxdevice, logging) #auto RX blanking
                        
                else: # We want to forward along the route disc
                    # Check that we aren't on the path already, then send it!
                    if myID in wholePath:
                        continue #We don't want to create endless loops
                    pathFromOrig.append(myID) #add myself in the first available 0 spot
                    msg = makeMsgRouteDisc(origID, msgID, myID, destID, pathFromOrig)
                    logging.info("Not for me. Forwarding along")
                    sendMsg(txdevice, msg, rxdevice, logging) #auto RX blanking
            
        if msgType == 2: #Route Reply
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgRouteReply(rxMsg)
            wholePath = pathFromOrig.copy()
            wholePath.insert(0, origID)
            wholePath.append(destID) # Now this is the whole path
            
            #Capture the info as long as we're involved
            if myID not in wholePath:
                continue #Skip if it's not something involving us
            
            if origID == myID: # We got a response!
                #Send the ACK
                sendAck(txdevice, rxMsg, rxdevice, logging)
                
                #Print the message!
                logging.info("Received Route Reply from node " + str(srcID) +
                             " with path " + str(wholePath))
                path2Node, hops2Node = updateCache(path2Node, hops2Node, myID, wholePath)
                logging.info("Got Route Reply. Updated routing cache to " + str(path2Node[destID-1]))
                
                #Send a data msg!
                path = path2Node[destID-1]
                dataMsg = makeMsgData(origID, msgID, myID, destID, path[:-1])
                sendMsgWithAck(txdevice, dataMsg, rxdevice, logging) #auto Rx blanking
                
            else: # Check if it's our turn to send this msg (comes from the previous person)
                # We should be right before the sender
                imNext = nextInPath(origID, destID, pathFromOrig, srcID, myID)

                if imNext:
                    #I'm next! First send ACK
                    sendAck(txdevice, rxMsg, rxdevice, logging)

                    path2Node, hops2Node = updateCache(path2Node, hops2Node, myID, wholePath)
                    logging.info("Got Route Reply. Updated routing cache to " + str(path2Node[destID-1]))
                
                    # Then forward it along!
                    msg = makeMsgRouteReply(origID, msgIDs[1], myID, destID, pathFromOrig)
                    msgIDs[1] = (msgIDs[1] + 1) % 16
                    sendMsgWithAck(txdevice, msg, rxdevice, logging) #auto RX blanking

        if msgType == 3: #Data Message
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgData(rxMsg)
            #Forward the message if your predecessor in the list sent
            wholePath = pathFromOrig.copy()
            wholePath.insert(0, origID)
            wholePath.append(destID) # Now this is the whole path

            #Error checking that we should be getting this message
            if srcID not in wholePath:
                logging.info("Received msg from node " + str(srcID) +
                             "not in route " + str(wholePath))
                continue
            
            senderInd = wholePath.index(srcID) #Who this came from
            #Only send if I'm the next stop in the route
            if destID == myID: #It's for me!
                sendAck(txdevice, rxMsg, rxdevice, logging)
                logging.info("Received msg from node " + str(srcID) +
                             ". Msg was " + hex(rxMsg))
            elif senderInd < len(wholePath) - 1 and wholePath[senderInd + 1] == myID:
                sendAck(txdevice, rxMsg, rxdevice, logging) #Send the ACK
                #Then I send it along!                
                dataMsg = makeMsgData(origID, msgID, myID, destID, pathFromOrig) #update the sourceID
                logging.info("Received msg from node " + str(srcID))
                sendMsgWithAck(txdevice, dataMsg, rxdevice, logging) #auto RX blanking
                
    time.sleep(0.01)
    
#Stop receive
rxdevice.disable_rx()

#Clean up before exiting
rxdevice.cleanup()
txdevice.cleanup()

