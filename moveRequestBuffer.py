
import config
import arduinoSend

class MoveRequestBuffer:

    def __init__(self):
        self.servoRequestList = []
        self.verbose = False
        self.superVerbose = False


    def clearBuffer(self):
        self.servoRequestList.clear()


    def addMoveRequest(self, request):
        self.servoRequestList.append(request)
        if self.verbose: config.log(f"addMoveToRequestList {request} ")


    def removeServoFromRequestList(self, servoName):
        """
        clear servo from buffered requests because a stop was requested
        :param servoName:
        :return:
        """
        if self.verbose: config.log(f"remove servo from moveRequestBuffer {servoName:20s}, {config.servoRequestList=}")
        for index, item in enumerate(self.servoRequestList):
            if item['servoName'] == servoName:
                self.servoRequestList.pop(index)
                if self.verbose: config.log(f"request removed {index=}: {config.servoRequestList=}")
        config.activeServos.remove(servoName)
        if self.verbose: config.log(f"{config.activeServos=}")


    def checkForExecutableRequests(self):
        """
        sequential move requests are dequeued from the buffered list when servo is not moving
        :return:
        """
        # config.log(f"check for executable request")
        listChanged = True
        while listChanged:
            listChanged = False
            for index, item in enumerate(self.servoRequestList):

                # if more than 1 request for servo in list use only the first one
                if config.activeServos.isServoActive(item['servoName']):
                    config.activeServos.setServoActive(item['servoName'])
                    config.log(f"send request to arduino {item=}")
                    arduinoSend.sendArduinoCommand(item['arduino'], item['msg'])
                    self.servoRequestList.pop(index)
                    listChanged = True
                    if self.superVerbose: config.log(f"remaining requests: {self.servoRequestList=}")
                    break


class ActiveServos:
    def __init__(self):
        self.servoActive = []
        self.verbose = False

    def clearServoActiveList(self):
        if self.verbose: config.log(f"cleared activeServos {self.servoActive=}")
        self.servoActive.clear()

    def setServoActive(self, servoName):
        if self.verbose: config.log(f"added servo to servoActive {config.servoActive=}")
        self.servoActive.append(servoName)

    def isServoActive(self, servoName):
        return servoName in self.servoActive

    def setServoInactive(self, servoName):
        if servoName not in self.servoActive:
            config.log(f"ActiveServos: remove servo {servoName} failed, not in list")
        else:
            self.servoActive.remove(servoName)
