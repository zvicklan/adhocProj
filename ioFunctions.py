#!/usr/bin/env python3
import time
import argparse
from datetime import datetime
from rpi_rf import RFDevice
from msgFunctions import *
from ackFuncs import *

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

def sendAck(txdevice, msg, rxdevice, logging, logger="None"):
    #Creates the ACK msg and sends it

    #Ignore if this is alredy an ACK
    if isAckMsg(msg):
        logging.info("sendAck ignoring " + hex(msg) + ". Already an ACK")
    else:
        ackMsg = createAckMsg(msg)
        sendMsg(txdevice, ackMsg, rxdevice, logging, logger)

def sendMsg(txdevice, msg, rxdevice, logging, logger="None"):
    #Takes in the rfdevice and msg (as an int) and sends it out
    protocol = None #Default 1
    pulselength = None #Default 350
    
    logging.info("sendMsg: " + hex(msg))
    #Log if desired
    if logger != 'None':
        logMsg(msg, logger, 0) # 0 for "out"
        
    #Do some logic to avoid receiving our own signal
    if rxdevice != "None":
        rxdevice.disable_rx()
        
    #Flash on our antenna, send, turn it off
    b = msg
    txdevice.tx_code(b, 1, 350)

    #And turn rx back on (if provided)
    if rxdevice != "None":
        rxdevice.enable_rx()
    
def getFileTimeStamp():
    #Returns a string in format 'mmdd_hhmm'
    now = datetime.now()
    timeStamp = now.strftime('%m%d_%H%M%S')
    return timeStamp
