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

rxdevice = None
txdevice = None

# pylint: disable=unused-argument
def exithandler(signal, frame):
    rxdevice.cleanup()
    txdevice.cleanup()
    sys.exit(0)

# RX setup
logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)-15s - [%(levelname)s] %(module)s: %(message)s', )

parser = argparse.ArgumentParser(description='Receives a decimal code via a 433/315MHz GPIO device')
parser.add_argument('-g', dest='gpio', type=int, default=27,
                    help="GPIO pin (Default: 27)")
argsRx = parser.parse_args()

signal.signal(signal.SIGINT, exithandler)
rxdevice = RFDevice(argsRx.gpio)

# TX setup
parser = argparse.ArgumentParser(description='Sends a decimal code via a 433/315MHz GPIO device')
parser.add_argument('-g', dest='gpio', type=int, default=17,
                    help="GPIO pin (Default: 17)")
parser.add_argument('-p', dest='pulselength', type=int, default=None,
                    help="Pulselength (Default: 350)")
parser.add_argument('-t', dest='protocol', type=int, default=None,
                    help="Protocol (Default: 1)")
argsTx = parser.parse_args()

txdevice = RFDevice(argsTx.gpio)

#Set up my info
file = open('idNum.txt', 'r')
line = file.readlines()
myID = int(line[0])
logging.info("Received ID " + str(myID))

maxID = 5 #b/c we know the # of nodes
numMsgTypes = 3

numDests = 10

msgCounts = [1] * numMsgTypes
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
    msg = makeMsgRouteDisc(myID, msgCounts[0], myID, destNode, [])
    msgCounts[0] = msgCounts[0] + 1
    sendMsg(txdevice, msg, rxdevice) #auto RX blanking

    logging.info(hex(msg) +
        " sent [msgType " + str(getMsgType(msg)) + "]")

timestamp = None
logging.info("Listening for codes on GPIO " + str(argsRx.gpio))

#TODO: Need to figure out a plan for logic to create messages
#  Might just be spamming msgs 1->5
msgBuffer = genDests(numDests, myID)

#Listening loop
testDone = False
while not(testDone):
    if rxdevice.rx_code_timestamp != timestamp:
        timestamp = rxdevice.rx_code_timestamp
        newMsg = rxdevice.rx_code
        msgType = getMsgType(newMsg)
        logging.info(hex(newMsg) +
                     " [pulselength " + str(rxdevice.rx_pulselength) +
                     ", protocol " + str(rxdevice.rx_proto) +
                     ", msgType " + str(msgType) + "]")

        #We will do processing if this is a real message
        if msgType == 1: #Route Discovery
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgRouteDisc(newMsg)
            if origID == myID: #Ignore our own msgs (or replies to them)
                continue
            #Check if we've seen it - Need to allow for multiple paths coming in
            lastMsgID = lastMsg[origID-1][0]
            if msgID == lastMsgID and destID != myID:
                continue
            else: #add it to the list
                lastMsg[origID-1][0] = msgID
                if destID == myID: #It's for me! Let's send a reply
                    #If this is a shorter path than I previously had, or it's a new msg
                    if hops2Node[srcID-1] > hopCount or msgID != lastMsgID:
                        path2Node, hops2Node = updateCache(path2Node, hops2Node, myID, origID, destID, pathFromOrig)
                        logging.info("Got Route Disc. Updated routing cache to " + print(path2Node))
                        
                        msg = makeMsgRouteReply(origID, msgID, myID, destID, pathFromOrig)
                        logging.info("Got Route Disc. Sending Reply msg " + hex(msg))
                        sendMsg(txdevice, msg, rxdevice) #auto RX blanking
                        
                else: # We want to forward along the route disc
                    # Check that we aren't on the path already, then send it!
                    if myID in pathFromOrig:
                        continue #We don't want to create endless loops
                    pathFromOrig[pathFromOrig.index(0)] = myID #add myself in the first available 0 spot
                    msg = makeMsgRouteDisc(origID, msgID, myID, destID, pathFromOrig)
                    logging.info("Got Route Disc. Sending Disc msg " + hex(msg))
                    sendMsg(txdevice, msg, rxdevice) #auto RX blanking
            
        if msgType == 2: #Route Reply
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgRouteReply(newMsg)
            
            #Capture the info as long as we're involved
            if myID not in pathFromOrig:
                continue #Skip if it's not something involving us
            
            path2Node, hops2Node = updateCache(path2Node, hops2Node, myID, origID, destID, pathFromOrig)
            logging.info("Got Route Reply. Updated routing cache to " + print(path2Node))
            
            if origID == myID: # We got a response!
                #Print the message!
                logging.info("Received Route Reply from node " + str(srcID) +
                             " with path " + str(pathFromOrig))
                testDone = True #TODO Temporary logic for test - next send a data message
                
            else: # Check if it's our turn to send this msg (comes from the previous person)
                # We should be right before the sender
                srcInd = pathFromOrig.index(srcID)
                myInd  = pathFromOrig.index(myID)

                if srcInd == myInd + 1:
                    #Forward it along!
                    msg = makeMsgRouteReply(origID, msgID, myID, pathFromOrig)
                    sendMsg(txdevice, msg, rxdevice) #auto RX blanking

        if msgType == 3: #Data Message
            (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsgData(newMsg)
            #Forward the message if your predecessor in the list sent
            pathFromOrig.insert(0, origID) # Now this is the whole path

            #Error checking that we should be getting this message
            if srcID not in pathFromOrig:
                logging.info("Received msg from node " + str(srcID) +
                             "not in route " + str(pathFromOrig))
                continue
            
            senderInd = pathFromOrig.index(srcID) #Who this came from
            #Only send if I'm the next stop in the route
            if pathFromOrig[senderInd + 1] == myID:
                #Then I send it along!
                newMsg = makeMsgData(origID, msgID, myID, destID, pathFromOrig)
                logging.info("Received msg from node " + str(srcID) +
                             "Sending along " + str(newMsg))
                msg = newMsg #Just keep the message untouched
                sendMsg(txdevice, msg, rxdevice) #auto RX blanking
                
    time.sleep(0.01)
    
#Stop receive
rxdevice.disable_rx()

#Clean up before exiting
rxdevice.cleanup()
txdevice.cleanup()

