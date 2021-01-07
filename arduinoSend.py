
import time
import config

from marvinglobal import servoClasses
from marvinglobal import marvinglobal as mg

def sendArduinoCommand(arduinoIndex, msg):
    if msg[-1] != "\n":
        msg += "\n"
    conn = config.arduinoConn[arduinoIndex]
    if conn is not None:
        #config.log(f"send msg to arduino {arduinoIndex}, {msg}")
        conn.write(bytes(msg, 'ascii'))
        conn.flush()
    else:
        config.log(f"no connection with arduino {arduinoIndex}")


def requestArduinoReady(arduinoIndex):

    msg = f"i,{arduinoIndex}\n"
    sendArduinoCommand(arduinoIndex, msg)
    arduinoData = config.arduinoDictLocal[arduinoIndex]
    config.log(f"request ready message from arduino {arduinoIndex}, {arduinoData['arduinoName']}, {arduinoData['comPort']}")


def servoAssign(servoName, lastPos):

    servoStatic = config.servoStaticDictLocal.get(servoName)
    servoType = config.servoTypeDictLocal.get(servoStatic.servoType)
    servoDerived = config.servoDerivedDictLocal.get(servoName)

    # send servo definitions to the arduino's
    # both servo and servoType have an inverted flag. for our servo inversion is given if either of them
    # are set, double inversion or no inversion means normal operation of the servo
    invertedFlag = (servoStatic.inverted != servoType.typeInverted)
    inverted = 1 if invertedFlag else 0
    msg = f"0,{servoName},{servoStatic.pin},{servoStatic.minPos},{servoStatic.maxPos},{servoStatic.autoDetach:.1f},{inverted},{lastPos},{servoStatic.powerPin},\n"

    sendArduinoCommand(servoStatic.arduinoIndex, msg)
    if config.servoCurrentDictLocal.get(servoName).verbose:
        config.log(f"assign servo: {servoName:<20}, \
pin: {servoStatic.pin:2}, minPos: {servoStatic.minPos:3}, maxPos:{servoStatic.maxPos:3}, \
restDeg: {servoStatic.restDeg:3}, autoDetach: {servoStatic.autoDetach:4.0f}, inverted: {inverted}, lastPos: {lastPos:3}, powerPin: {servoStatic.powerPin}")


def requestServoPosition(servoName, position, duration, filterSequence=True):
    """
    move servo in <duration> seconds from current position to <position>
    filter fast passed in requests
    """
    # command 1,<arduino>,<servo>,<position>,<duration>
    # e.g. servo=eyeX, position=50, duration=2500: 2,3,50,2500
    servoStatic = config.servoStaticDictLocal.get(servoName)
    servoDerived = config.servoDerivedDictLocal.get(servoName)
    servoCurrent = config.servoCurrentDictLocal.get(servoName)

    # filter out jaw moves from log as they are very frequent
    if servoName != "head.jaw":
        servoStatic = config.servoStaticDictLocal.get(servoName)
        servoDerived = config.servoDerivedDictLocal.get(servoName)
        degrees = mg.evalDegFromPos(servoStatic, servoDerived, position)
        config.log(f"arduino send {servoName}, arduino {servoStatic.arduinoIndex}, degrees: {degrees}, position: {position:.0f}, duration: {duration:.0f}", publish=False)

    # if new position requests come in high sequence avoid responding to each one
    # when filterSequence is active
    if filterSequence and (time.time() - servoCurrent.timeOfLastMoveRequest) < 0.2:
        config.log(f"move request ignored, time diff last request: {time.time() - servoCurrent.timeOfLastMoveRequest} s")
        return
    #else:
        #config.log(f"time since last move request: {time.time() - servoCurrent.timeOfLastMoveRequest}")

    servoCurrent.timeOfLastMoveRequest = time.time()

    if not servoStatic.enabled:
        config.log(f"servoPos {position} requested but servo is disabled in ServoDict.json")
        return

    # verify duration
    #config.log(f"position: {position}, scurrpos: {config.servoCurrent[servoName].position}")
    deltaPos = abs(config.servoCurrentDictLocal.get(servoName).position - position)
    minDuration = servoDerived.msPerPos * deltaPos

    # for filtered moves increase move duration based on servos properties
    if duration < minDuration and filterSequence and servoName != 'head.jaw':
        config.log(f"{servoName}: duration increased, deltaPos: {deltaPos:.0f}, msPerPos: {servoDerived.msPerPos:.1f}, from: {duration:.0f} to: {minDuration:.0f}")
        duration = minDuration


    msg = f"1,{servoStatic.pin:02.0f},{position:03.0f},{duration:04.0f},\n"
    sendArduinoCommand(servoStatic.arduinoIndex, msg)


def requestServoDegrees(servoName, degrees, duration, filterSequence=False):
    servoStatic: servoClasses.ServoStatic = config.servoStaticDictLocal.get(servoName)
    servoDerived: servoClasses.ServoDerived = config.servoDerivedDictLocal.get(servoName)
    position = mg.evalPosFromDeg(servoStatic, servoDerived, degrees)
    requestServoPosition(servoName, position, duration, filterSequence)


def requestServoStop(servoName):
    servoStatic: servoClasses.ServoStatic = config.servoStaticDictLocal.get(servoName)
    servoCurrent: servoClasses.ServoCurrent = config.servoCurrentDictLocal.get(servoName)
    msg = f"2,{servoStatic.pin}\n"
    sendArduinoCommand(servoStatic.arduinoIndex, msg)
    if servoCurrent.swiping:
        updStmt = (mg.SharedDataItem.SERVO_CURRENT, servoName, {'swiping': False})
        config.updateSharedDict(updStmt)


def requestAllServosStop():
    config.log(f"all servos stop requested")
    msg = f"3\n"
    for i in range(config.numArduinos):
        if config.arduinoConn[i] is not None:
            sendArduinoCommand(i, msg)
    time.sleep(1)   # allow some time to stop

def requestServoStatus(servoName: str):
    servoStatic = config.servoStaticDictLocal.get(servoName)
    msg = f"4,{servoStatic.pin}\n"
    sendArduinoCommand(servoStatic.arduinoIndex, msg)


def setAutoDetach(servoName: str, milliseconds: int):
    servoStatic = config.servoStaticDictLocal.get(servoName)
    msg = f"5,{servoStatic.pin},{milliseconds}\n"
    sendArduinoCommand(servoStatic.arduinoIndex, msg)


def setPosition(servoName: str, newPos: int):
    servoStatic = config.servoStaticDictLocal.get(servoName)
    #servoControl.setPowerPin([servoStatic.powerPin])
    msg = f"6,{servoStatic.pin},{newPos}\n"
    sendArduinoCommand(servoStatic.arduinoIndex, msg)


def setVerbose(servoName: str, state: bool):
    config.log(f"{servoName} verbose set to {state}")
    servoStatic = config.servoStaticDictLocal.get(servoName)
    verboseState = 1 if state else 0
    msg = f"7,{servoStatic.pin},{verboseState},\n"
    sendArduinoCommand(servoStatic.arduinoIndex, msg)


def requestRest(servoName: str):
    servoStatic: servoClasses.ServoStatic = config.servoStaticDictLocal.get(servoName)
    servoDerived: servoClasses.ServoDerived = config.servoDerivedDictLocal.get(servoName)
    if servoStatic.enabled:
        pos = mg.evalPosFromDeg(servoStatic, servoDerived, servoStatic.restDeg)
        requestServoPosition(servoName, pos, 1500)
        time.sleep(0.1)


def requestAllServosRest():
    config.log(f"all servos rest requested")
    for servoName, servoStatic in config.servoStaticDictLocal.items():
        if servoStatic.enabled:
            servoDerived = config.servoDerivedDictLocal.get(servoName)
            pos = mg.evalPosFromDeg(servoStatic, servoDerived, servoStatic.restDeg)
            requestServoPosition(servoName, pos, 1500)
            time.sleep(0.1)
            #config.log(f"rest position for {servoName}, pos: {pos}")


def pinHigh(pinList):
    pins = "".join(c for c in str(pinList) if c not in '[ ]')
    msg = f"h,{pins}\n"
    config.log(f"arduino send pinHigh {msg}", publish=False)
    sendArduinoCommand(0, msg)


def pinLow(pinList):
    pins = "".join(c for c in str(pinList) if c not in '[ ]')
    msg = f"l,{pins}\n"
    config.log(f"arduino send pinLow {msg}", publish=False)
    sendArduinoCommand(0, msg)
