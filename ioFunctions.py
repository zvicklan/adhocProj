#!/usr/bin/env python3

def sendMsg(txdevice, msg, rxdevice="None"):
#Takes in the rfdevice and msg (as an int) and sends it out

    print('send1')
    protocol = None #Default 1
    pulselength = None #Default 350

    print('send2')
    #Do some logic to avoid receiving our own signal
    if rxdevice != "None":
        rxdevice.disable_rx()

    print('send3')
    #Flash on our antenna, send, turn it off
    txdevice.enable_tx()
    
    print('send4')
    txdevice.tx_code(msg, protocol, pulselength)
    
    print('send5')
    txdevice.disable_tx()

    print('send6')
    #And turn rx back on (if provided)
    if rxdevice != "None":
        rxdevice.enable_rx()

    print('send7')
