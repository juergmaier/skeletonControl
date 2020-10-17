
import time
import random

from PyQt5.QtCore import pyqtSlot, QRunnable

import config
import arduinoSend
import marvinglobal.marvinglobal as mg


class RandomMoves(QRunnable):
    """
    This thread moves all robot servos with random speed and position
    """
    @pyqtSlot()
    def __init__(self):
        super().__init__()
        self.lastAction = time.time()
        self.moveFactor = 0.7            # the smaller the shorter the moves
        config.log(f"random moves init done")

    @pyqtSlot()
    def run(self):

        config.log(f"thread random moves is running")
        while config.randomMovesActive: # controlled by the gui

            maxMoveSeconds = 20
            restSeconds = 8
            lastRest = time.time()
            while config.randomMovesActive:

                nextAction = random.randint(1000, 4000)

                if time.time() - self.lastAction > (nextAction/1000):

                    self.moveServos()

                    self.lastAction = time.time()

                time.sleep(0.1)

                if time.time() - lastRest > maxMoveSeconds:
                    config.log("pause in random moves")
                    arduinoSend.requestAllServosRest()
                    time.sleep(restSeconds)
                    config.log("continue random moves")
                    lastRest = time.time()


    def moveServos(self):

        config.log(f"randomMoves, moveServos")
        for servoName, curr in config.servoCurrentDict.items():

            if not curr.moving and config.randomMovesActive:
                servoStatic: mg.ServoStatic = config.servoStaticDict.get(servoName)

                pos = random.randint(servoStatic.minPos, servoStatic.maxPos)

                duration = random.randint(3, 20)

                # prevent inward moves with armRotate as they might cause collisions of arms with body
                if servoName == 'leftArm.rotate':
                    if pos < 90:
                        pos = 90
                if servoName == 'rightArm.rotate':
                    if pos < 90:
                        pos = 90

                config.log(f"move servo {servoName}, pos: {pos}, duration: {duration*100}")
                arduinoSend.requestServoPosition(servoName, pos, duration*100)
