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
    
    maxWait = 1 #max time to allow this to wait
    reTxInterval = .25 #time between retransmits
    awaitingACK = True
    timedOut = 0
    
    origID, msgID, srcID, destID, hopCount, pathFromOrig = readMsg(msg) #want to match these
    msgType = getMsgType(msg)
    startTime = datetime.now()
    lastTx = startTime
    timestamp = None
    
    logging.info("Start " + str(datetime.now().microsecond))
    #Send the first time, then start listening
    sendMsg(txdevice, msg, rxdevice, logging)
    logging.info("0 " + str(datetime.now().microsecond))
    #Carry out the loop, listening
    while awaitingACK and not timedOut:
        logging.info("sendWithAck loop")
        logging.info("A " + str(datetime.now().microsecond))
        #Check for a message
        if rxdevice.rx_code_timestamp != timestamp:
            logging.info("B " + str(datetime.now().microsecond))
            (timestamp, rxMsg, msgType_rx) = loadNewMsg(rxdevice, timestamp, logging)
            logging.info("sendWithAck received: " + hex(rxMsg)
                         + ", type " + str(msgType))
            
            logging.info("C " + str(datetime.now().microsecond))
            #Check if it's one we want:
            if msgType_rx: #!= 0
                toParse = deAckMsg(rxMsg) #returns rxMsg if rxMsg not an ACK
                
                logging.info("D " + str(datetime.now().microsecond))
                origID_rx, msgID_rx, srcID_rx, destID, hopCount, pathFromOrig = readMsg(toParse)
                #Logic for Route Disc/Route Reply
                if msgType == 1 and msgType_rx == 2:
                    if origID == srcID: #Ensure this was my Route Disc
                        if (origID_rx, msgID_rx) == (origID, msgID): #same msg
                            #It's the same msg! We got it!
                            
                            logging.info("E " + str(datetime.now().microsecond))
                            awaitingACK = False
                elif msgType_rx == msgType and isAckMsg(rxMsg):
                    if (origID, msgID, srcID) == (origID_rx, msgID_rx, srcID_rx):
                        #It's the same msg! We got it!
                        
                        logging.info("F " + str(datetime.now().microsecond))
                        awaitingACK = False

        #Check if we want to retransmit
                        
        logging.info("G " + str(datetime.now().microsecond))
        if awaitingACK: #Just so we skip this when we find the msg
            
            logging.info("H " + str(datetime.now().microsecond))
            currTime = datetime.now()
            timeDiff = currTime - startTime
            logging.info("Delay " + str(timeDiff.total_seconds()))
            #If it's been long enough, time out
            if timeDiff.total_seconds() > maxWait:
                
                logging.info("I " + str(datetime.now().microsecond))
                timedOut = 1
            else:
                
                logging.info("J " + str(datetime.now().microsecond))
                txTimeDiff = currTime - lastTx
                logging.info("TX Delay " + str(txTimeDiff.total_seconds()))
                
                logging.info("K " + str(datetime.now().microsecond))
                if txTimeDiff.total_seconds() > reTxInterval:
                    sendMsg(txdevice, msg, rxdevice, logging)
                    lastTx = currTime

            #And wait a bit
            
            logging.info("L " + str(datetime.now().microsecond))
            time.sleep(0.01)
            
            logging.info("M " + str(datetime.now().microsecond))

    logging.info("N " + str(datetime.now().microsecond))   
    if not awaitingACK:
        logging.info("sendWithAck recognized ACK msg")
    logging.info("Leaving sendWithAck")
    retVal = 1-timedOut #1 if we were successful, 0 else
    return retVal

def sendMsg(txdevice, msg, rxdevice, logging):
    #Takes in the rfdevice and msg (as an int) and sends it out

    logging.info("1 " + str(datetime.now().microsecond)) 
    protocol = None #Default 1
    pulselength = None #Default 350

    time.sleep(0.01)
    #Do some logic to avoid receiving our own signal
    if rxdevice != "None":
        rxdevice.disable_rx()

    #Flash on our antenna, send, turn it off
        
    logging.info("1.5 " + str(datetime.now().microsecond))
    txdevice.enable_tx()
    
    logging.info("1.9 " + str(datetime.now().microsecond))
    logging.info("sendMsg: " + hex(msg))
    logging.info("2 " + str(datetime.now().microsecond))
    txdevice.tx_code(msg, protocol, pulselength)
    logging.info("3 " + str(datetime.now().microsecond))
    txdevice.disable_tx()
    
    logging.info("4 " + str(datetime.now().microsecond))
    #And turn rx back on (if provided)
    if rxdevice != "None":
        rxdevice.enable_rx()

    logging.info("5 " + str(datetime.now().microsecond))
    
def getFileTimeStamp():
    #Returns a string in format 'mmdd_hhmm'
    now = datetime.now()
    timeStamp = now.strftime('%m%d_%H%M%S')
    return timeStamp
