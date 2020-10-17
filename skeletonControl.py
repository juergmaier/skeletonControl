
import os, sys
import time
#from multiprocessing.managers import SyncManager
import serial   # pip install pyserial
import threading

import marvinglobal.marvinglobal as mg
#from shared_memory_dict import SharedMemoryDict
import config

import arduinoSend
import arduinoReceive
import servoRequests

def openSerial(ad):
    #{'arduinoIndex', 'arduinoName', 'comPort', 'connected'}

    if ad['comPort'] == "unassigned":
        return True
    conn = None
    try:
        conn = serial.Serial(ad['comPort'])
        # try to reset the arduino
        #conn.setDTR(False)
        #time.sleep(0.2)
        #conn.setDTR(True)
        conn.baudrate = 115200
        conn.writeTimeout = 0
        #config.log(f"serial connection with arduino {a['arduinoIndex']}, {a['arduinoName']} on {a['comPort']} initialized")

        config.log(f"serial connection with arduino {ad['arduinoName']} set")
        config.arduinoConn[ad['arduinoIndex']] = conn

        return True

    except Exception as eSerial:
        config.log(f"exception on serial connect with arduino: {ad['arduinoName']}, comPort: {ad['comPort']}, {eSerial}, going down")
        if conn is not None:
            try:
                conn.close()
            except Exception as e2:
                config.log(f"conn.close failed, {e2}")
        sys.exit(1)



def assignServos(arduinoIndex):
    """
    servo definitions are stored in a json file
    for each servo handled by the <arduinoIndex> send the definitions to the arduino
    :param arduinoIndex:
    :return:
    """

    config.log(f"send servo definitions to arduino {arduinoIndex} and set current position to last persisted position")

    # send servo definition data to arduino
    for servoName, servoStatic in config.md.servoStaticDict.items():

        if servoStatic.enabled and servoStatic.arduino == arduinoIndex:

            #config.log(f"servo assign {servoName}")
            arduinoSend.servoAssign(servoName, config.md.servoCurrentDict.get(servoName).position)
            #time.sleep(0.1)


def initServoControl():

    # reset arduino connected state in shared data
    for a, ad in config.md.arduinoDict.items():
        updStmt = ("arduinoDict", a, {'connected':False})
        config.updateSharedDict(updStmt)


    #ik.init()
    # try to open comm ports
    for a, ad in config.md.arduinoDict.items():
        if not openSerial(ad):
            config.log(f"could not open serial port {a['comPort']}, going down")
            os._exit(1)

    # start serial port receiving threads
    for a,ad in config.md.arduinoDict.items():

        serialReadThread = threading.Thread(target=arduinoReceive.readMessages, args={ad['arduinoIndex']})
        serialReadThread.name = f"arduinoRead_{ad['arduinoIndex']}"
        serialReadThread.start()

    # verify connection by requesting a first response from Arduino
    time.sleep(0.2)
    for a, ad in config.md.arduinoDict.items():
        arduinoSend.requestArduinoReady(ad['arduinoIndex'])

    # wait for response from arduinos
    for i in range(100):
        if config.md.arduinoDict.get(0)['connected'] and config.md.arduinoDict.get(1)['connected']:
            break
        time.sleep(0.05)

    # check for successful connection with both arduinos
    for a, ad in config.md.arduinoDict.items():
        if not ad['connected']:
            config.log(f"could not receive serial response from arduino {ad['arduinoName']}, {ad['comPort']}")
            conn = config.arduinoConn[ad['arduinoIndex']]
            if conn is not None:
                try:
                    conn.close()
                except Exception as e2:
                    config.log(f"conn.close failed, {e2}")
            sys.exit(1)

    for a, ad in config.md.arduinoDict.items():
        assignServos(ad['arduinoIndex'])

    # set verbose mode for servos to report more details
    arduinoSend.setVerbose('head.rothead', True)

    config.log(f"skeletonControl ready")
    config.log(f"---------------")

    # allow arduinos to report their status
    time.sleep(0.5)


if __name__ == "__main__":

    config.startLogging()

    # connect with shared data
    config.md = mg.MarvinGlobal()
    if not config.md.connect():
        os._exit(1)


    # add own process to shared process list
    config.md.updateProcessDict(config.processName)

    # create a dict to find servo name from arduino and pin (for messages from arduino)
    for servoName, servoStatic in config.md.servoStaticDict.items():
        config.servoNameByArduinoAndPin.update({config.md.servoDerivedDict.get(servoName).servoUniqueId: servoName})

    # connect with arduinos
    initServoControl()

    # request all servos to rest position
    config.log(f"request all servos rest")
    config.md.servoRequestQueue.put({'cmd': 'allServoRest'})

    # wait for move requests or timeout
    while True:
        if not config.md.updateProcessDict(config.processName):
            # connection with shared data lost
            config.md = None
            while config.md is None:
                config.md = mg.MarvinGlobal()
                if not config.md.connect():
                    time.sleep(1)
            time.sleep(0.5)

        try:
            request = config.md.servoRequestQueue.get(timeout=2)
        except Exception as e:
            # in case of empty queue update processDict only
            continue

        config.log(f"servoRequestQueue, request received: {request}")

        # try to call the requested servo method
        try:
            methodName = request['cmd']
            getattr(servoRequests, methodName, lambda: 'unknown')(request)

        except Exception as e:
            config.log(f"unknown command in request [{request['cmd']}]")


