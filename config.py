
import time, datetime
import logging
import marvinglobal.marvinglobal as mg

numArduinos = 2
arduinoConn = [None] * numArduinos

processName = 'skeletonControl'
md = None   # shared data

arduinoDict = None

servoNameByArduinoAndPin = {}   # a list to access servos by Arduino and Id

simulateServoMoves = False


def startLogging():
    logging.basicConfig(
        filename=f"log/skeletonControl.log",
        level=logging.INFO,
        format='%(message)s',
        filemode="w")


def log(msg, publish=True):

    logtime = str(datetime.datetime.now())[11:23]
    logging.info(f"{logtime} - {msg}")
    print(f"{logtime} - {msg}")


def updateSharedDict(updStmt):

    global md
    if not md.updateSharedDict(updStmt):

        # connection to marvinData lost, try to reconnect
        md = None
        while md is None:
            md = mg.MarvinGlobal()
            if not md.connect():
                time.sleep(1)
            else:
                break
