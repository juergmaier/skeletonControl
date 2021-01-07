
import os
import time, datetime
import logging

from marvinglobal import marvinShares

numArduinos = 2
arduinoConn = [None] * numArduinos

processName = 'skeletonControl'
marvinShares = None   # shared data

# skeleton control updates its sharedDict's in marvinData
# the dicts owned by the skeleton control itself get updated and queried locally
arduinoDictLocal = {}            # local version of arduinoDict
servoTypeDictLocal = {}
servoStaticDictLocal = {}
servoDerivedDictLocal = {}
servoCurrentDictLocal = {}
persistedServoPositionsLocal = {}

servoNameByArduinoAndPin = {}   # a dictionary to access servos by Arduino and Id

lastPositionSaveTime:float = time.time()


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

    if not marvinShares.updateSharedData(updStmt):

        log(f"connection with shared data lost, going down")# connection to marvinData lost, try to reconnect
        os._exit(1)