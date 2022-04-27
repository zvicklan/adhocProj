#!/usr/bin/env python3
import time
from datetime import datetime

from ackFuncs import *

# getAckCount
ackList = [[11, datetime.now(), 2, 1, 3], [44, datetime.now(), 6, 1, 3]]
print(getAckCount(ackList, 11))
print(getAckCount(ackList, 2))
# getMaxTxCount
print(getMaxTxCount(ackList, 11))
print(getMaxTxCount(ackList, 2))
# getLastTx
print(getLastTx(ackList, 11))
print(getLastTx(ackList, 2))

# updateAckList
print(updateAckList(ackList, 11))

# hasStaleAck
print(hasStaleAck(ackList))
time.sleep(1)
print(hasStaleAck(ackList)) #s/b false now

# isDead
print(isDead(ackList, 11))
print(isDead(ackList, 44))

# addAck
newList = []
reTxInterval = 1
maxTxCount = 3
newList = addAck(newList, 1234, reTxInterval, maxTxCount)
print(newList)
newList = addAck(newList, 1235, reTxInterval, maxTxCount)
print(newList)
newList = addAck(newList, 1236, reTxInterval, maxTxCount)
print(newList)

# removeAck
newList = removeAck(newList, 1235)
print(newList)
newList = removeAck(newList, 9000)
print(newList)

# test isMyAck
rtDisc1 = int('0x91115000', 16)
rtDisc2 = int('0x91125200', 16)
rtRepl = int('0xA1125200', 16)
rtRepl1 = int('0xA9125200', 16)

print('All should be 0')
print(isMyAck(rtDisc1, rtDisc1))
print(isMyAck(rtDisc1, rtDisc2))
print(isMyAck(rtDisc2, rtRepl))
print('All should be 1')
print(isMyAck(rtDisc1, rtRepl))
print(isMyAck(rtRepl, rtRepl1))


# test isAwaitedAck
newList = []
newList = addAck(newList, rtRepl, reTxInterval, maxTxCount)
print('false then true')
print(isAwaitedAck(newList, rtDisc1))
print(isAwaitedAck(newList, rtRepl1))
print(isAwaitedAck([], rtRepl1))
