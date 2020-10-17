
import os
import sys
import time

import config
import marvinglobal.marvinglobal as mg

import arduinoSend
import skeletonControl


#####################################
# readMessages runs in its own THREAD
#####################################
def readMessages(arduino):

    config.log(f"arduinoReceive, readMessages started for arduino: {arduino}")

    while True:
        if config.arduinoConn[arduino] is None:
            time.sleep(1)
            continue

        conn = config.arduinoConn[arduino]
        while conn.is_open:

            try:
                bytesAvailable = conn.in_waiting
            except Exception as e:
                config.log(f"exception in arduino: {arduino} in in_waiting {e}, shutting down ...")
                sys.exit(1)
            #config.log("waiting for arduino message")
            if bytesAvailable > 0:

                recvB = conn.readline()

                #config.log(f"from arduino: {recvB}")

                # check for existing shared data connection
                if config.md is None:
                    continue

                # special case status messages, as these can be very frequently
                # a compressed format is used
                if len(recvB) == 8:
                    s1 = int(recvB[0:2], 16)
                    s2 = int(recvB[2:4], 16)
                    s3 = int(recvB[4:6], 16)

                    # extract data from binary message
                    pin          = s1 & 0x7f
                    position     = s2 - 40           # to prevent value seen as lf 40 is added by the arduino
                    assigned     = s3 & 0x01 > 0
                    moving       = s3 & 0x02 > 0
                    attached     = s3 & 0x04 > 0
                    autoDetach   = s3 & 0x08 > 0
                    servoVerbose = s3 & 0x10 > 0


                    servoUniqueId = (arduino * 100) + pin
                    servoName = config.servoNameByArduinoAndPin[servoUniqueId]

                    if servoVerbose:
                        config.log(f"servo update {servoName}, {s1:02X},{s2:02X},{s3:02X}, arduino: {arduino}, pin: {pin:2}, pos {position:3}, assigned: {assigned}, moving {moving}, attached {attached}, autoDetach: {autoDetach}, verbose: {servoVerbose}", publish=False)

                    prevCurrentDict = config.md.servoCurrentDict.get(servoName)
                    servoStatic = config.md.servoStaticDict.get(servoName)
                    servoDerived: mg.ServoDerived = config.md.servoDerivedDict.get(servoName)
                    degrees = mg.evalDegFromPos(servoStatic, servoDerived, position)

                    newValues = {'assigned': assigned,
                                 'moving': moving,
                                 'attached':attached,
                                 'autoDetach': autoDetach,
                                 'verbose': servoVerbose,
                                 'position': position,
                                 'degrees': degrees,
                                 'swiping': prevCurrentDict.swiping,
                                 'timeOfLastMoveRequest': prevCurrentDict.timeOfLastMoveRequest}

                    # update the shared dict
                    if config.md is not None:
                        updStmt = ("servoCurrentDict", servoName, newValues)
                        config.updateSharedDict(updStmt)

                    if position != prevCurrentDict.position:
                        pass #ik.updateDhChain()

                    # update skeleton gui if running
                    if config.md.isProcessRunning('skeletonGui'):
                        config.md.guiUpdateQueue.put({'type':'updateServo','servoName': servoName})

                    # check for move target postition reached
                    if not moving and attached:

                        # handle special case in swipe mode
                        #config.log(f"{servoName}: not moving and attached, swiping: {prevCurrentDict.swiping}")
                        if prevCurrentDict.swiping:
                            newPos = 0
                            if abs(position - servoStatic.minPos) < 3:
                                newPos = servoStatic.maxPos
                            if abs(position - servoStatic.maxPos) < 3:
                                newPos = servoStatic.minPos
                            swipeMoveDuration = servoDerived.posRange * servoDerived.msPerPos * 2
                            arduinoSend.requestServoPosition(servoName, newPos, swipeMoveDuration)

                    continue


                # now process all other messages not starting with 0x80 byte
                try:
                    recv = recvB.decode()
                except:
                    config.log(f"problem with decoding arduino msg '{recvB}'")
                    continue

                # config.log(f"line read {recv}")
                msgID = recvB[0:3].decode()


                if msgID == "!A0":  # "arduino ready"

                    #config.md.arduinoDict.get(arduino)['connected'] = True
                    config.log(f"ready message from arduino {config.md.arduinoDict.get(arduino)['arduinoName']} received")
                    updStmt = ("arduinoDict", arduino, {'connected':True})
                    config.updateSharedDict(updStmt)

                    if config.md.isProcessRunning('skeletonGui'):
                        info = {'type': 'arduinoUpdate', 'arduino': arduino, 'connected': True}
                        config.log(f"update skeletonGui {info}")
                        config.md.guiUpdateQueue.put(info)


                else:
                    try:
                        config.log(f"<-I{arduino} " + recv[:-1], publish=False)
                    except:
                        config.log(f"Unexpected error on reading messages: {sys.exc_info()[0]}")

