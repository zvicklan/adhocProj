#!/usr/bin/env python3

import argparse
import signal
import sys
import time
import logging

from rpi_rf import RFDevice
from msgFunctions import *
from ioFunctions import *

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
rxdevice.enable_rx()

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
txdevice.enable_tx()

#Send a Route Discovery msg (just as a test)
msg = makeMsgRouteDisc(1,2,3,4)
sendMsg(txdevice, msg)

logging.info(hex(msg) +
    " sent [msgType " + str(getMsgType(msg)) + "]")

timestamp = None
logging.info("Listening for codes on GPIO " + str(argsRx.gpio))
#Listening loop
awaitingResponse = True
while awaitingResponse:
    if rxdevice.rx_code_timestamp != timestamp:
        timestamp = rxdevice.rx_code_timestamp
        msgType = getMsgType(rxdevice.rx_code)
        logging.info(hex(rxdevice.rx_code) +
                     " [pulselength " + str(rxdevice.rx_pulselength) +
                     ", protocol " + str(rxdevice.rx_proto) +
                     ", msgType " + str(msgType) + "]")
        if msgType == 1: #It's a real message!
            awaitingResponse = False
    time.sleep(0.01)

#Clean up before exiting
rxdevice.cleanup()
txdevice.cleanup()

