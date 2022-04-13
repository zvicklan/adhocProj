#!/usr/bin/env python3
import time
import argparse
from datetime import datetime
from rpi_rf import RFDevice
from msgFunctions import *

def loadNewMsg(rxdevice, timestamp, logging):
    timestamp = rxdevice.rx_code_timestamp
    newMsg = rxdevice.rx_code
    msgType = getMsgType(newMsg)
    return timestamp, newMsg, msgType

def rxSetup():
    #Sets up the rxdevice
    parser = argparse.ArgumentParser(description='Receives a decimal code via a 433/315MHz GPIO device')
    parser.add_argument('-g', dest='gpio', type=int, default=27,
                        help="GPIO pin (Default: 27)")
    argsRx = parser.parse_args()
    rxdevice = RFDevice(argsRx.gpio)
    return rxdevice

def txSetup():
    #Sets up the txdevice    
    parser = argparse.ArgumentParser(description='Sends a decimal code via a 433/315MHz GPIO device')
    parser.add_argument('-g', dest='gpio', type=int, default=17,
                        help="GPIO pin (Default: 17)")
    parser.add_argument('-p', dest='pulselength', type=int, default=None,
                        help="Pulselength (Default: 350)")
    parser.add_argument('-t', dest='protocol', type=int, default=None,
                        help="Protocol (Default: 1)")
    argsTx = parser.parse_args()

    txdevice = RFDevice(argsTx.gpio)
    return txdevice

def sendAck(txdevice, msg, rxdevice, logging):
    #Creates the ACK msg and sends it

    #Ignore if this is alredy an ACK
    if isAckMsg(msg):
        logging.info("sendAck ignoring " + hex(msg) + ". Already an ACK")
    else:
        ackMsg = createAckMsg(msg)
        sendMsg(txdevice, ackMsg, rxdevice, logging)
    
def sendMsgWithAck(txdevice, msg, rxdevice, logging):
    # Awaits an ACK msg with the following
    #   ACK bit set
    #   Same orig ID
    #   Same msg ID
    #   Self as srcID (same srcID)
    
    maxWait = 0.5 #max time to allow this to wait
    reTxInterval = 0.1 #time between retransmits
    awaitingACK = True
    timedOut = 0
    
    origID, msgID, srcID, destID, hopCount, pathFromOrig = readMsg(msg) #want to match these
    msgType = getMsgType(msg)
    startTime = datetime.now()
    lastTx = startTime
    timestamp = None
    
    #Send the first time, then start listening
    sendMsg(txdevice, msg, rxdevice, logging)
    
    #Carry out the loop, listening
    while awaitingACK and not timedOut:
        #Check for a message
        if rxdevice.rx_code_timestamp != timestamp:
            (timestamp, rxMsg, msgType) = loadNewMsg(rxdevice, timestamp, logging)
            logging.info("sendWithAck received: " + hex(rxMsg)
                         + ", type " + str(msgType))

            #Check if it's one we want:
            if msgType_rx: #!= 0
                origID_rx, msgID_rx, srcID_rx, destID, hopCount, pathFromOrig = readMsg(rxMsg)
                #Logic for Route Disc/Route Reply
                if msgType == 1 and msgType_rx == 2:
                    if origID == srcID: #Ensure this was my Route Disc
                        if (origID_rx, msgID_rx) == (origID, msgID): #same msg
                            #It's the same msg! We got it!
                            awaitingACK = False
                elif msgType_rx == msgType:
                    if (origID, msgID, srcID) == (origID_rx, msgID_rx, srcID_rx):
                        #It's the same msg! We got it!
                        awaitingACK = False

        #Check if we want to retransmit            
        if awaitingACK: #Just so we skip this when we find the msg
            currTime = datetime.now()
            timeDiff = currTime - startTime
            #If it's been long enough, time out
            if timeDiff.total_seconds() > maxWait:
                timedOut = 1
            else:
                txTimeDiff = currTime - lastTx
                if txTimeDiff.total_seconds() > reTxInterval:
                    sendMsg(txdevice, msg, rxdevice, logging)
                    lastTx = currTime
                    
    if not awaitingACK:
        logging.info("sendWithAck recognized ACK msg")
        
    retVal = 1-timedOut #1 if we were successful, 0 else
    return retVal

def sendMsg(txdevice, msg, rxdevice, logging):
    #Takes in the rfdevice and msg (as an int) and sends it out

    protocol = None #Default 1
    pulselength = None #Default 350

    time.sleep(0.1)
    #Do some logic to avoid receiving our own signal
    if rxdevice != "None":
        rxdevice.disable_rx()

    #Flash on our antenna, send, turn it off
    txdevice.enable_tx()
    logging.info("sendMsg: " + hex(msg))
    txdevice.tx_code(msg, protocol, pulselength)
    txdevice.disable_tx()

    #And turn rx back on (if provided)
    if rxdevice != "None":
        rxdevice.enable_rx()

def getFileTimeStamp():
    #Returns a string in format 'mmdd_hhmm'
    now = datetime.now()
    timeStamp = now.strftime('%m%d_%H%M%S')
    return timeStamp
