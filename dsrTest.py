#!/usr/bin/env python3

import argparse
import signal
import sys
import time
import logging

from rpi_rf import RFDevice
from msgFunctions import *
from ioFunctions import *
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
maxID = 5 #b/c we know the # of nodes
numMsgTypes = 3

msgCounts = np.zeros((3,1))

#Create a struct for tracking msgs we've seen (unique origID, msgType, msgID triplets)
seenMsgs = np.zeros((maxID, numMsgTypes), dtype=object)
for ii in np.ndindex(seenMsgs.shape):
    msgs[ii] = []


# Start listening:
rxdevice.enable_rx()

if myID == 1: #We'll have the first guy kick this off
    #Send a Route Discovery msg (just as a test)
    destNode = myID
    while destNode == myID: #b/c we want to send to someone else
        destNode = randint(1,maxID)
        
    msg = makeMsgRouteDisc(myID, msgCounts[0], myID, destNode)
    msgCounts[0] = msgCounts[0] + 1
    sendMsg(txdevice, msg, rxdevice) #auto RX blanking

    logging.info(hex(msg) +
        " sent [msgType " + str(getMsgType(msg)) + "]")

timestamp = None
logging.info("Listening for codes on GPIO " + str(argsRx.gpio))

#TODO: Need to figure out a plan for logic to create messages

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
            (origID, msgID, srcID, destID) = readMsgRouteDisc(newMsg)
            if origID == myID: #Ignore our own msgs (or replies to them)
                continue
            #Check if we've seen it
            seenMsgIDs = seenMsgs[origID][0] #indexing msgType - 1
            if msgID in seenMsgIDs:
                continue
            else: #add it to the list and continue
                seenMsgs[origID][0].append(msgID)
                
            # We want to send it again
            msg = makeMsgRouteDisc(origID, msgID, myID, destID)
            sendMsg(txdevice, msg, rxdevice) #auto RX blanking
            
        if msgType == 2: #Route Reply
            (origID, msgID, srcID, hopCount, pathFromDest) = readMsgRouteReply(newMsg)
            pathFromDest.insert(0, srcID) #Interface defined w/o src in list, so add it
            
            if origID == myID: # We got a response!
                #Print the message!
                logging.info("Received Route Reply from node " + str(srcID) +
                             " with path " + str(pathFromDest))
                testDone = True #TODO Temporary logic for test - next send a data message
                
            else: # Check that we aren't on the path already, then send it!
                if myID in pathFromDest:
                    continue #We don't want to create endless loops
                #Resend with the updated path!
                msg = makeMsgRouteReply(origID, msgID, myID, pathFromDest)
                sendMsg(txdevice, msg, rxdevice) #auto RX blanking

        if msgType == 3: #Data Message
            (origID, msgID, srcID, hopCount, pathFromOrig) = readMsgData(newMsg)
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
                msg = newMsg #Just keep the message untouched
                sendMsg(txdevice, msg, rxdevice) #auto RX blanking
                
    time.sleep(0.01)
    
#Stop receive
rxdevice.disable_rx()

#Clean up before exiting
rxdevice.cleanup()
txdevice.cleanup()

