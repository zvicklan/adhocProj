#!/usr/bin/env python3

def sendMsg(rfdevice, msg)
#Takes in the rfdevice and msg (as an int) and sends it out

    protocol = "default"
    pulselength = "default"
    rfdevice.tx_code(msg, protocol, pulselength)
