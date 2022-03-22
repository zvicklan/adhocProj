import csv
import sys
from importlib import reload
sys.path.append("D:/Documents/2021/CMU/04sprin/Networks/Projects/Proj2/Pi")
import msgFunctions
reload(msgFunctions)
from msgFunctions import *

log = open('D:/Documents/2021/CMU/04sprin/Networks/Projects/Proj2/Pi/logs/test3.csv', 'w', newline='')

logger = csv.writer(log)
a = makeMsgRouteDisc(1,2,3,1)
a2 = makeMsgRouteDisc(1,2,3,4, logger)
readMsgRouteDisc(a, logger)
readMsgRouteDisc(a2)

b = makeMsgRouteReply(2,3,4, [5, 6, 1])
b2 = makeMsgRouteReply(2,3,4, [5, 6, 2], logger)
readMsgRouteReply(b, logger)
readMsgRouteReply(b2)

c = makeMsgData(2,3,4,[5,6,7])
c2 = makeMsgData(2,3,4,[5,6,8], logger)
readMsgData(c2)
readMsgData(c, logger)

print(getMsgType(a))
print(getMsgType(b))
print(getMsgType(c))

log.close()
