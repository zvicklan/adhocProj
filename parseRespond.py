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

msgCounts = np.zeros(3,1)

# Start listening:
rxdevice.enable_rx()

timestamp = None
logging.info("Listening for codes on GPIO " + str(argsRx.gpio))
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
            
            #Otherwise, we want to send it again
            msg = makeMsgRouteDisc(origID, msgID, myID, destID)
            sendMsg(txdevice, msg, rxdevice) #auto RX blanking
            
        if msgType == 2: #Route Reply
            (origID, msgID, srcID, hopCount, pathFromDest) = readMsgRouteReply(newMsg)
            pathFromDest.insert(0, srcID) #Interface defined w/o src in list, so add it
            
            if origID == myID: # We got a response!
                #Print the message!
                logging.info("Received Route Reply from node " + str(srcID) +
                             " with path " + str(pathFromDest))
                testDone = True #TODO Temporary logic for test
                
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
    
rxdevice.disable_rx()
#Send a Route Discovery msg (just as a test)
msg = makeMsgRouteDisc(4,3,2,1)
sendMsg(txdevice, msg)

logging.info(hex(msg) +
    " sent [msgType " + str(getMsgType(msg)) + "]")

#Clean up before exiting
rxdevice.cleanup()
txdevice.cleanup()
