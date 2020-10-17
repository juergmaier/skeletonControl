
import config
import arduinoSend
import marvinglobal.marvinglobal as mg

#    def assign(self, requestQueue, servoName, initialPosition):
#        requestQueue.put({'cmd': 'assign', 'servoName': servoName, 'position': initialPosition})
def assign(request):
    arduinoSend.servoAssign(request['servoName'], request['position'])

#    def stop(self, requestQueue, servoName):
#        requestQueue.put({'cmd': 'stop', 'servoName': servoName})
def stop(request):
    arduinoSend.requestServoStop(request['servoName'])

#    def positionServo(self, requestQueue, servoName, position, duration):
#        requestQueue.put({'cmd': 'position', 'servoName': servoName, 'position': position, 'duration': duration})
def position(request):
    arduinoSend.requestServoPosition(request['servoName'], request['position'], request['duration'])

#    def setVerbose(self, requestQueue, servoName, verbose):
#        requestQueue.put({'cmd': 'setVerbose', 'servoName': servoName, 'verbose': verbose})
def setVerbose(request):
    arduinoSend.setVerbose(request['servoName'], request['verbose'])

#    def allServoStop(self, requestQueue):
#        requestQueue.put({'cmd': 'allServoStop'})
def allServoStop(request):
    arduinoSend.requestAllServosStop()

#    def allServoRest(self, requestQueue):
#        requestQueue.put({'cmd': 'allServoRest'})
def allServoRest(request):
    arduinoSend.requestAllServosRest()

#    def setAutoDetach(self, requestQueue, servoName, duration):
#        requestQueue.put({'cmd': 'setAutoDetach', 'servoName': servoName, 'duration': duration})
def setAutoDetach(request):
    arduinoSend.setAutoDetach(request['servoName'], request['duration'])


def startRandomMoves(request):
    config.log(f"tbd: startRandomMoves requested")

def stopRandomMoves(request):
    config.log(f"tbd: stopRandomMoves requested")

def startSwipe(request):
    config.log(f"startSwipe requested")
    servoName = request['servoName']
    servoStatic: mg.ServoStatic = config.md.servoStaticDict.get(servoName)
    servoDerived: mg.ServoDerived = config.md.servoDerivedDict.get(servoName)

    # request servoCurrent update with new swiping state
    updStmt = ("servoCurrentDict", servoName, {'swiping': True})
    config.updateSharedDict(updStmt)

    minPos = servoStatic.minPos
    moveDuration = servoDerived.msPerPos * servoDerived.posRange

    arduinoSend.requestServoPosition(servoName, minPos, moveDuration)
    # continuation of swipe is handled with the end move message in arduinoReceive
    # swiping stop is triggered by button or servo stop/rest request


def stopSwipe(request):
    config.log(f"stopSwipe requested")
    servoName = request['servoName']
    updStmt = ("servoCurrentDict", servoName, {'swiping': False})
    config.updateSharedDict(updStmt)
    arduinoSend.requestRest(servoName)

# test git 2