#!/usr/bin/env python
"""
Blocky Talky - User Script (us.py, WebSocket client)

The module that works with the program written in the Blocky Talky GUI.
"""
import time
import thread
import logging
import socket
import websocket        # Install via "pip install websocket-client"
import usercode
from message import *

class UserScript(object):
    def __init__(self):
        self.hostname = socket.gethostname()
        self.msgQueue = []
        self.robot = Message.initStatus()

        #startup message to subscribe to hwVal channel
        self.handshake = Message(self.hostname, None, "Subs", 
                                 ("HwVal","MsgIn"))
        self.handshake = Message.encode(self.handshake)
        
        #true if unread data from sensor
        self.sensorStatus= Message.createSensorStatus()
        print self.sensorStatus.values()


    def executeScript(self, ws):
        """
        Resets the robot to its default state and runs the script downloaded
        from Google Blockly via usercode.run().
        """
        # To make sure socket is open before sending ...
        time.sleep(0.5)
        # Initialize local image to the default state.
        self.robot = Message.initStatus()
        # Runs the user code generated by Blockly.
        logging.info("Running usercode.py ...")
   #     try:
        usercode.run(self, ws)
    #    except:
     #       logging.error("An error has occured while running the usercode.")

    def getSensorValue(self, sensorType, port):
        key= sensorType + str(port+1)
        #print key
        self.sensorStatus[key]= False
        return self.robot[sensorType+'s'][port]
        

    def checkContent(self, content):
        """ used with "message that says: ____" blocks.  returns true if first
        element in message queue has the desired content.  otherwise
        returns false
        """
        if self.msgQueue:
            if self.msgQueue[0].getContent() == content:
                del self.msgQueue[0]
                return True
        return False

    def checkSource(self, source):
        """ used with "message from: ____" blocks.  returns true if first
        element in message queue is from the desired client.  otherwise
        returns false
        """
        if self.msgQueue:
            if self.msgQueue[0].getSource() == source:
                del self.msgQueue[0]
                return True
        return False

    def onOpen(self, ws):
        logging.info("Connection opened.")
        ws.send(self.handshake)

    def onMessage(self, ws, message):
        """
        The incoming message is either a hardware status update, a command sent
        by another Pi or a social media status update.
            # On HW message: update the robot
            # On Pi message: add to message queue
            # On SM message: TBD
        """
        # For testing purposes
        message = Message.decode(message)
        if message.getChannel() == "Message":
            # If it's a "do this" type message ...
            self.msgQueue.append(message)
            print message.getContent()
        else:
            # If it's a robot status update ...
            hwDict = message.getContent()
            # Apply the value changes
            for key, valueList in hwDict.iteritems():
                for index, value in enumerate(valueList):
                    if value is not None:
                        self.robot[key][index] = value
           # logging.debug("Command: " + str(hwDict))
        
            #tells user script that there is unread data on all ports
            for sensor in self.sensorStatus:
                self.sensorStatus[sensor]= True
   
    def onError(self, ws, error):
        logging.error("A WebSocket error has occured.")

    def onClose(self, ws):
        logging.info("Connection closed.")

if __name__ == "__main__":
    # Set the logging level.
    logging.basicConfig(format = "%(levelname)s:\t%(message)s",
                        # filename = "us.log",
                        level = logging.ERROR)
    us = UserScript()
    ws = websocket.WebSocketApp("ws://localhost:8886/mp",
                                on_open = us.onOpen,
                                on_message = us.onMessage,
                                on_error = us.onError,
                                on_close = us.onClose)
    thread.start_new(us.executeScript, (ws,))
    ws.run_forever()