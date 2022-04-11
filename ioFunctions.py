#!/usr/bin/env python3
import time
from datetime import datetime

def sendMsg(txdevice, msg, rxdevice="None"):
#Takes in the rfdevice and msg (as an int) and sends it out

    protocol = None #Default 1
    pulselength = None #Default 350

    time.sleep(0.01)
    #Do some logic to avoid receiving our own signal
    if rxdevice != "None":
        rxdevice.disable_rx()

    #Flash on our antenna, send, turn it off
    txdevice.enable_tx()
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

def getMsgTimeStamp():
    #Returns a string in format 'mmdd_hhmm'
    now = datetime.now()
    timeStamp = 3600*now.hour + 60*now.minute + now.second + now.microsecond*1e-6
    return timeStamp
