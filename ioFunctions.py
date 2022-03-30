#!/usr/bin/env python3

def sendMsg(rfdevice, msg):
#Takes in the rfdevice and msg (as an int) and sends it out

    protocol = None #Default 1
    pulselength = 700 #Default 350
    rfdevice.tx_code(msg, protocol, pulselength)
