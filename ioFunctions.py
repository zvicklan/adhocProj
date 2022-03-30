#!/usr/bin/env python3

def sendMsg(txdevice, msg):
#Takes in the rfdevice and msg (as an int) and sends it out

    protocol = None #Default 1
    pulselength = None #Default 350
    txdevice.enable_tx()
    txdevice.tx_code(msg, protocol, pulselength)
    txdevice.disable_tx()
