#General helper function for going Byte String to Msg
def bytes2Msg(byteList):
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
def msg2Bytes(msg):
    #Start empty and recursively add
    byteList = []
    while msg > 0:
        byteList.append(msg % 256) #capture the current
        msg = msg // 256 #shift down a byte
    #Reverse it
    byteList.reverse() #b/c want small byte last
    
    #And output!
    return byteList 
            
def makeMsgRouteDisc(origID, msgID, srcID, destID):
    #Combines everything together into a message for sending
    
    #Build the Bytes - Total message is 6B
    byteList = [0] * 6
    byteList[0] = 1
    byteList[1] = origID
    byteList[2] = 0 #Defined for consistency. Really just Byte4
    byteList[3] = msgID #also counts as Byte 3
    byteList[4] = srcID
    byteList[5] = destID

    #And return the made msg
    return bytes2Msg(byteList)
    
def readMsgRouteDisc(msg):
    #Outputs in order origID, msgID, srcID, destID
    
    #Get the bytes
    byteList = msg2Bytes(msg)

    # Build the message
    origID = byteList[1]
    msgID  = byteList[3] + 256*byteList[2]
    srcID  = byteList[4]
    destID = byteList[5]

    #And return
    return origID, msgID, srcID, destID
