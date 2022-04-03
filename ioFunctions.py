#!/usr/bin/env python3

def sendMsg(txdevice, msg, rxdevice="None"):
#Takes in the rfdevice and msg (as an int) and sends it out

    protocol = None #Default 1
    pulselength = None #Default 350

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
