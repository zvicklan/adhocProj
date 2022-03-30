#General helper function for going Byte String to Msg
def bytes2Msg(byteList, logger='None'):
    
    #Log if desired
    if logger != 'None':
        logger.writerow(byteList)
        
    msg = 0
    #Loop through the bytes to make a msg
    for b in byteList:
        if msg == 0: #Create the msg
            msg = b + 8
        else: #Or tack onto the end (shifting up)
            msg = msg * (2**4) + b
    #And output!
    return msg

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
        logger.writerow(byteList)
        
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
        msg = 0 #throw it out
    else:
        msg = msg - 8
        
    #And output. This is the last Byte (hence the msg Type)
    return msg

def makeMsgRouteDisc(origID, msgID, srcID, destID, logger='None'):
    #Combines everything together into a message for sending
    
    #Build the Bytes - Total message is 9 Nibbles
    byteList = [0] * 8
    byteList[0] = 1
    byteList[1] = origID
    byteList[2] = 0 # overflow for msgID
    byteList[3] = msgID
    byteList[4] = srcID
    byteList[5] = destID

    #And return the made msg
    return bytes2Msg(byteList, logger)
    
def readMsgRouteDisc(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, destID
    
    #Get the bytes
    byteList = msg2Bytes(msg, logger)
        
    # Build the message
    origID = byteList[1]
    msgID  = byteList[3] + 16*byteList[2]
    srcID  = byteList[4]
    destID = byteList[5]

    #And return
    return origID, msgID, srcID, destID

def makeMsgRouteReply(origID, msgID, srcID, pathFromDest, logger='None'):
    #Combines everything together into a message for sending
    
    #Build the Bytes - Total message is 8 nibbles
    byteList = [0] * 8
    byteList[0] = 2
    byteList[1] = origID
    byteList[2] = 0 # overflow for msgID
    byteList[3] = msgID 
    byteList[4] = srcID
    ind = 5
    for node in pathFromDest:
        byteList[ind] = node
        ind = ind + 1
        
    #And return the made msg
    return bytes2Msg(byteList, logger)
    
def readMsgRouteReply(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, hopCount, pathFromDest
    
    #Get the bytes
    byteList = msg2Bytes(msg, logger)
        
    # Build the message
    origID = byteList[1]
    msgID  = byteList[3] + 16*byteList[2]
    srcID  = byteList[4]
    pathFromDest = byteList[5:] #and the rest
    hopCount = len(pathFromDest)
    #And return
    return origID, msgID, srcID, hopCount, pathFromDest

def makeMsgData(origID, msgID, srcID, pathFromOrig, logger='None'):
    #Combines everything together into a message for sending
    
    #Build the Bytes - Total message is 8 nibbles
    byteList = [0] * 8
    byteList[0] = 3
    byteList[1] = origID
    byteList[2] = 0 # overflow for msgID
    byteList[3] = msgID 
    byteList[4] = srcID
    ind = 5
    for node in pathFromOrig:
        byteList[ind] = node
        ind = ind + 1

    #And return the made msg
    return bytes2Msg(byteList, logger)
    
def readMsgData(msg, logger='None'):
    #Outputs in order origID, msgID, srcID, hopCount, pathFromOrig
    
    #Get the bytes
    byteList = msg2Bytes(msg, logger)
        
    # Build the message
    origID = byteList[1]
    msgID  = byteList[3] + 16*byteList[2]
    srcID  = byteList[4]
    pathFromOrig = byteList[5:] #and the rest
    hopCount = len(pathFromOrig)
    
    #And return
    return origID, msgID, srcID, hopCount, pathFromOrig

