#General helper function for going Byte String to Msg
def bytes2Msg(byteList, logger='None'):
    
    #Log if desired
    if logger != 'None':
        logger.writerow(byteList)
        
    msg = 0
    #Loop through the bytes to make a msg
    for b in byteList:
        if msg == 0: #Create the msg
            msg = b
        else: #Or tack onto the end (shifting up)
            msg = msg * (2**8) + b
    #And output!
    return msg

#General helper function for going Msg to Byte String
def msg2Bytes(msg, logger='None'):
    #Start empty and recursively add
    byteList = []
    while msg > 0:
        byteList.append(msg % 256) #capture the current
        msg = msg // 256 #shift down a byte
    #Reverse it
    byteList.reverse() #b/c want small byte last
    
    #Log if desired
    if logger != 'None':
        logger.writerow(byteList)
        
    #And output!
    return byteList 

#General helper function for getting the message type
def getMsgType(msg):
    #Only want to capture the last byte (highest value)
    #Also serves to check if messages are actually for us
    minMsgLen = 7 #MAKE SURE TO UPDATE THIS: YOU'RE GONNA MESS THIS UP ZACH
    
    lenCount = 1
    msgLen = 0
    while msg > 255:
        msgLen = msg % 256 #will end up being the 2nd byte
        msg = msg // 256 #shift down a byte
        lenCount = lenCount + 1

    if lenCount != msgLen or msgLen < minMsgLen: #It doesn't add up!
        msg = 0 #throw it out
        
    #And output. This is the last Byte (hence the msg Type)
    return msg

def makeMsgRouteDisc(origID, msgID, srcID, destID, logger='None'):
    #Combines everything together into a message for sending

    msgLen = 7
    
    #Build the Bytes - Total message is 6B
    byteList = [0] * 7
    byteList[0] = 1
    byteList[1] = msgLen
    byteList[2] = origID
    byteList[3] = 0 #Defined for consistency. Really just Byte4
    byteList[4] = msgID #also counts as Byte 3
    byteList[5] = srcID
    byteList[6] = destID

    #And return the made msg
    return bytes2Msg(byteList, logger)
    
def readMsgRouteDisc(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, destID
    
    #Get the bytes
    byteList = msg2Bytes(msg, logger)
        
    # Build the message
    origID = byteList[2]
    msgID  = byteList[4] + 256*byteList[3]
    srcID  = byteList[5]
    destID = byteList[6]

    #And return
    return origID, msgID, srcID, destID

def makeMsgRouteReply(origID, msgID, srcID, pathFromDest, logger='None'):
    #Combines everything together into a message for sending

    msgLen = 7 + len(pathFromDest)
    
    #Build the Bytes - Total message is 6B
    byteList = [0] * 7
    byteList[0] = 2
    byteList[1] = msgLen
    byteList[2] = origID
    byteList[3] = 0 #Defined for consistency. Really just Byte4
    byteList[4] = msgID #also counts as Byte 3
    byteList[5] = srcID
    byteList[6] = len(pathFromDest)
    for node in pathFromDest:
        byteList.append(node)
        
    #And return the made msg
    return bytes2Msg(byteList, logger)
    
def readMsgRouteReply(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, hopCount, pathFromDest
    
    #Get the bytes
    byteList = msg2Bytes(msg, logger)
        
    # Build the message
    origID = byteList[2]
    msgID  = byteList[4] + 256*byteList[3]
    srcID  = byteList[5]
    hopCount = byteList[6]
    pathFromDest = byteList[7:] #and the rest
    
    #And return
    return origID, msgID, srcID, hopCount, pathFromDest

def makeMsgData(origID, msgID, srcID, pathFromDest, logger='None'):
    #Combines everything together into a message for sending
    
    msgLen = 7 + len(pathFromDest)
    
    #Build the Bytes - Total message is 6B
    byteList = [0] * 7
    byteList[0] = 3
    byteList[1] = msgLen
    byteList[2] = origID
    byteList[3] = 0 #Defined for consistency. Really just Byte4
    byteList[4] = msgID #also counts as Byte 3
    byteList[5] = srcID
    byteList[6] = len(pathFromDest)
    for node in pathFromDest:
        byteList.append(node)
        
    #And return the made msg
    return bytes2Msg(byteList, logger)
    
def readMsgData(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, hopCount, pathFromDest
    
    #Get the bytes
    byteList = msg2Bytes(msg, logger)
        
    # Build the message
    origID = byteList[2]
    msgID  = byteList[4] + 256*byteList[3]
    srcID  = byteList[5]
    hopCount = byteList[6]
    pathFromDest = byteList[7:] #and the rest
    
    #And return
    return origID, msgID, srcID, hopCount, pathFromDest

