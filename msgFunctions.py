from cacheFunctions import *
from datetime import datetime

def getTimeStamp():
    #Returns a time (float)
    now = datetime.now()
    timeStamp = 3600*now.hour + 60*now.minute + now.second + now.microsecond*1e-6
    return timeStamp

#General helper function for going Byte String to Msg
def bytes2Msg(byteList, logger='None'):
    
    #Log if desired
    if logger != 'None':
        logger.writerow([getTimeStamp()] + [0] + byteList) #0 means "out"
        
    msg = 0
    #Loop through the bytes to make a msg
    for b in byteList:
        if msg == 0: #Create the msg
            msg = b + 8
        else: #Or tack onto the end (shifting up)
            msg = msg * (2**4) + b
    #And output!
    return msg

def isAckMsg(msg):
#Checks for ACK by checking one bit
    bitNum = 28
    bitPow = bitNum - 1

    isACK = 0
    #First, we want to check it isn't already an ACK
    shifted = msg // (2**bitPow)
    if shifted % 2 == 1:
        #Then we're an ACK
        isACK = 1
        
    return isACK

def createAckMsg(msg):
#Creates an ACK msg by setting one bit
    bitNum = 28
    bitPow = bitNum - 1

    #First, we want to check it isn't already an ACK
    if not isAckMsg(msg):
        #Then we're good to go
        msgNew = msg + 2**bitPow

        #If something isn't working, error
        if not isAckMsg(msgNew):
            raise Exception("ACK Creation is not working properly: " +
                            hex(msg) + " led to " + hex(msgNew))        
    else:
        msgNew = msg
        
    #And return the result
    return msgNew

def deAckMsg(msg):
#Removes the ACK from a msg
    bitNum = 28
    bitPow = bitNum - 1

    #First, we want to check it is already an ACK
    if isAckMsg(msg):
        #Then we're good to go
        msgNew = msg - 2**bitPow      
    else: #Wasn't an ACK anyway
        msgNew = msg
        
    #And return the result
    return msgNew

#General helper function for going Msg to Byte String
def msg2Bytes(msg, logger='None'):
    #Start empty and recursively add
    byteList = []
    while msg > 0:
        byteList.append(msg % 16) #capture the current
        msg = msg // 16 #shift down a byte
    #Reverse it
    byteList.reverse() #b/c want small byte last
    
    #Log if desired
    if logger != 'None':
        logger.writerow([getTimeStamp()] + [1] + byteList) # 1 means "in"
        
    #And output!
    return byteList 

#General helper function for getting the message type
def getMsgType(msg):
    #Only want to capture the last byte (highest value)
    # Not that we use the first bit now as a check
    #Also serves to check if messages are actually for us
    
    lenCount = 1
    msgLen = 8
    while msg > 15:
        msg = msg // 16 #shift down a byte
        lenCount = lenCount + 1

    if lenCount != 8 or (msg < 8): #s/b 8 nibbles and min val s/b 8
        msgType = 0 #throw it out
    else:
        msgType = msg - 8
        
    #And output. This is the last Byte (hence the msg Type)
    return msgType

def makeMsg(msgType, origID, msgID, srcID, destID, pathFromOrig, logger='None'):
    #Base helper function for everything (since msgs are so similar)
        
    #Build the Bytes - Total message is 8 Nibbles
    byteList = [0] * 8
    byteList[0] = msgType
    byteList[1] = origID
    byteList[2] = msgID
    byteList[3] = srcID
    byteList[4] = destID

    ind = 5
    for node in pathFromOrig:
        byteList[ind] = node
        ind = ind + 1
        
    #And return the made msg
    return bytes2Msg(byteList, logger)

def readMsg(msg, logger='None'):
    #Default function for reading all msgs
    
    #Get the bytes
    byteList = msg2Bytes(msg, logger)
        
    # Build the message
    origID = byteList[1]
    msgID  = byteList[2]
    srcID  = byteList[3]
    destID  = byteList[4]
    pathFromOrig = byteList[5:] #and the rest

    pathFromOrig = remove0s(pathFromOrig)
    hopCount = len(pathFromOrig) + 1
    
    #And return
    return origID, msgID, srcID, destID, hopCount, pathFromOrig

def makeMsgRouteDisc(origID, msgID, srcID, destID, pathFromOrig, logger='None'):
    #Combines everything together into a message for sending

    msgType = 1
    
    #Use the helper function
    msg = makeMsg(msgType, origID, msgID, srcID, destID, pathFromOrig, logger)
        
    #And return the made msg
    return msg

def readMsgRouteDisc(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, destID, hopCount, pathFromOrig
    
    #Get the bytes
    (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsg(msg, logger)

    #And return
    return origID, msgID, srcID, destID, hopCount, pathFromOrig



def makeMsgRouteReply(origID, msgID, srcID, destID, pathFromOrig, logger='None'):
    #Combines everything together into a message for sending

    msgType = 2
    
    #Use the helper function
    msg = makeMsg(msgType, origID, msgID, srcID, destID, pathFromOrig, logger)
        
    #And return the made msg
    return msg
    
def readMsgRouteReply(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, destID, hopCount, pathFromOrig
    
    #Get the bytes
    (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsg(msg, logger)

    #And return
    return origID, msgID, srcID, destID, hopCount, pathFromOrig

def makeMsgData(origID, msgID, srcID, destID, pathFromOrig, logger='None'):
    #Combines everything together into a message for sending

    msgType = 3
    
    #Use the helper function
    msg = makeMsg(msgType, origID, msgID, srcID, destID, pathFromOrig, logger)
        
    #And return the made msg
    return msg
    
def readMsgData(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, destID, hopCount, pathFromOrig
    
    #Get the bytes
    (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsg(msg, logger)

    #And return
    return origID, msgID, srcID, destID, hopCount, pathFromOrig

def makeMsgRouteDrop(origID, msgID, srcID, destID, pathFromOrig, logger='None'):
    #Combines everything together into a message for sending

    msgType = 4
    pathFromOrig = [0]*3
    #Use the helper function
    msg = makeMsg(msgType, origID, msgID, srcID, destID, pathFromOrig, logger)
        
    #And return the made msg
    return msg

def readMsgRouteDrop(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, destID
    #Ignore the pathFromOrig
    
    #Get the bytes
    (origID, msgID, srcID, destID, hopCount, pathFromOrig) = readMsg(msg, logger)

    #And return
    return origID, msgID, srcID, destID, hopCount, pathFromOrig

def checkLastMsg(lastMsgIDs, msgType, origID, msgID):
    #Updates the last message, lets you know if this is new

    lastMsgID = lastMsgIDs[origID-1][msgType-1]
    if lastMsgID == msgID:
        isNew = False
    else:
        isNew = True
        lastMsgIDs[origID-1][msgType-1] = msgID

    return lastMsgIDs, isNew
