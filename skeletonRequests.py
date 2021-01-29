
import config
import arduinoSend
from marvinglobal import marvinglobal as mg
from marvinglobal import skeletonClasses

#    def assign(self, requestQueue, servoName, initialPosition):
#        requestQueue.put({'cmd': 'assign', 'servoName': servoName, 'position': initialPosition})
def assign(request):
    arduinoSend.servoAssign(request['servoName'], request['position'])

#    def stop(self, requestQueue, servoName):
#        requestQueue.put({'cmd': 'stop', 'servoName': servoName})
def stop(request):
    arduinoSend.requestServoStop(request['servoName'])

# move servo to position 0..180
def position(request):
    #config.log(f"{request=}")
    arduinoSend.requestServoPosition(request['servoName'], request['position'], request['duration'],request['sequential'])

# move servo to requested degrees
def requestDegrees(request):
    arduinoSend.requestServoDegrees(request['servoName'], request['degrees'], request['duration'], request['sequential'])

#    def setVerbose(self, requestQueue, servoName, verbose):
#        requestQueue.put({'cmd': 'setVerbose', 'servoName': servoName, 'verbose': verbose})
def setVerbose(request):
    arduinoSend.setVerbose(request['servoName'], request['verboseOn'])

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
    arduinoSend.setAutoDetach(request['servoName'], request['duration']/1000)

# random moves is a separate process
#def startRandomMoves(request):
#    config.log(f"tbd: startRandomMoves requested")

#def stopRandomMoves(request):
#    config.log(f"tbd: stopRandomMoves requested")

def startSwipe(request):
    config.log(f"startSwipe requested")
    servoName = request['servoName']
    servoStatic: skeletonClasses.ServoStatic = config.servoStaticDictLocal.get(servoName)
    servoDerived: skeletonClasses.ServoDerived = config.servoDerivedDictLocal.get(servoName)

    # request servoCurrent update with new swiping state
    updStmt = (mg.SharedDataItem.SERVO_CURRENT, servoName, {'swiping': True})
    config.updateSharedDict(updStmt)

    minPos = servoStatic.minPos
    moveDuration = servoDerived.msPerPos * servoDerived.posRange

    arduinoSend.requestServoPosition(servoName, minPos, moveDuration)
    # continuation of swipe is handled with the end move message in arduinoReceive
    # swiping stop is triggered by button or servo stop/rest request


def stopSwipe(request):
    config.log(f"stopSwipe requested")
    servoName = request['servoName']
    updStmt = (mg.SharedDataItem.SERVO_CURRENT, servoName, {'swiping': False})
    config.updateSharedDict(updStmt)
    arduinoSend.requestRest(servoName)

# test git 2