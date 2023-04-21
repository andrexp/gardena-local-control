#!/usr/bin/python3
# coding: utf-8
import time
import threading
import paho.mqtt.client as mqtt
import logging
import json
from threading import Thread
from queue import Queue
from random import Random
from pynng import Sub0, Req0
import argparse

from config import MQTT_BROKER_IP
from config import MQTT_BROKER_PORT
from config import MQTT_AUTHENTICATION
from config import MQTT_BROKER_USER
from config import MQTT_BROKER_PASSWORD
from config import MQTT_CLIENT_ID_BASE
from config import MQTT_TOPIC_SUBSCRIBE
from config import MQTT_TOPIC_PUBLISH
from config import MQTT_PUBLISH_RETAIN
from config import GARDENA_NNG_FORWARD_PATH_EVT
from config import GARDENA_NNG_FORWARD_PATH_CMD
from config import MQTT_PUBLISH_RETAIN
from config import SCRIPT_VERSION

#Class to store nng EventData
class EventData:
    def __init__(self, deviceid, eventtype, eventvalue):
        self.deviceid = deviceid
        self.eventtype = eventtype
        self.eventvalue = eventvalue

#Class to store nng commandData
class CommandData:
    def __init__(self, deviceid, command, payload):
        self.deviceid = deviceid
        self.command = command
        self.payload = payload
        
#Class to store all data to communicate with mqtt
class MQTTClientData:
    def __init__(self, connectionReturnCode, disconnectionReturnCode):
        self.connectionReturnCode = connectionReturnCode
        self.disconnectionReturnCode = disconnectionReturnCode


#Queue for publish events
publishEventDataQueue = Queue()
#Queue for subscribe commands
subscribeCommandDataQueue = Queue()
#List for all mqtt clients
mqttClientDict = dict()

def gardenaCommandBuilder(command):
    # init command with valid values
    operation = "read"
    gardenaCommand = "status"
    varType = "vi"
    gardenaPayload = "0"
    
    try:
        # build expected command string to be sent to command queue of the gardena gateway
        if command.command == "mower_timer":
            operation = "write"
            gardenaCommand = "mower_timer"
            varType = "vi"
            gardenaPayload = command.payload
        elif command.command == "park_until_next_task" and command.payload:
            operation = "write"
            gardenaCommand = "action_paused_until_1"
            varType = "vi"
            gardenaPayload = "sgcBAQAA"
        elif command.command == "park_until_further_notice" and command.payload:
            operation = "write"
            gardenaCommand = "action_paused_until_1"
            varType = "vi"
            gardenaPayload = "+AcMHxYA"
        elif command.command == "read_status":
            operation = "read"
            gardenaCommand = "status"
            varType = "vi"
        else:
            # further commands have to be first observed, all commands which are not in list above will be ignored
            return False

        # return resulting command string byte-coded
        cmd_str = '[{{"entity":{{"device":"{}","path":"lemonbeat/0"}},"metadata":{{"sequence":1,"source":"lemonbeatd"}},"op":"{}","payload":{{"{}":{{"ts":{},"{}": {}}}}}}}]'.format(command.deviceid, operation, gardenaCommand, int(time.time()), varType, gardenaPayload)
        logging.debug("Built command string: {}".format(bytes(cmd_str, encoding='utf-8')))
        return bytes(cmd_str, encoding='utf-8')   
    
    except Exception as e:
        logging.debug("ERR Building gardena command: {}".format(e))
        # returning false leads to ignoring received command
        return False
    
    # this point should not be reached
    return False

def gardenaEventInterpreter(event_str):


    try:
        # parse JSON
        gardenaEventDict = json.loads(event_str)[0]
        deviceId = gardenaEventDict["entity"]["device"]
        payload = gardenaEventDict["payload"]

        logging.debug("gardenaEvtParse: Message from deviceId: {}, payload: {}".format(deviceId, payload))

        # fill into object to publish via MQTT, sometimes payload has more than one dataset
        for data in payload.keys():
            for key in payload[data].keys():
                if key == "vi" or key == "vo":
                    publishEventDataQueue.put(EventData(deviceId,data,payload[data][key]))

    except Exception as e:
        logging.debug("ERR Parsing JSON-Data: {}".format(e))
        # if no valid interpetation is possible set type to unknown and value to raw event_str
        publishEventDataQueue.put(EventData("unknown","unknown",event_str))

def gardenaEventSubscribe():
    logging.debug("gardenaEventSubscribe Task is start reading")
    while True:
        try:
            with Sub0(dial=GARDENA_NNG_FORWARD_PATH_EVT) as sub0:
                sub0.subscribe("")
                received_telegram = sub0.recv()
                logging.debug("received telegram from nngforward")
                gardenaEventInterpreter(received_telegram.decode('utf-8'))
        except Exception as e:
                logging.info("ERR while connecting to nngforward subscription: {}".format(e))

def gardenaCommandPublish():
    while True:
            # there must be a message in the queue
            if subscribeCommandDataQueue.empty():
                continue
            # if there is at least one element try to publish to gardena gateway
            logging.debug("received telegram to publish to gardena gateway")
            item = subscribeCommandDataQueue.get()
            if gardenaCommandBuilder(item):
                try:
                    with Req0(dial=GARDENA_NNG_FORWARD_PATH_CMD) as req:
                        req.send(gardenaCommandBuilder(item))
                        logging.debug(req.recv())
                except Exception as e:
                        logging.info("ERR while connecting to nngforward command request pipe: {}".format(e))


#Connect callback for MQTT clients
def connectCallback(client, userdata, flags, rc):
    mqttClientData = mqttClientDict.get(client)
    if mqttClientData is None:
        logging.debug("MQTT client not found")
        return
    #Reset disconnection code
    mqttClientData.disconnectionReturnCode = -1
    mqttClientData.connectionReturnCode = rc
    if rc==0:
        logging.debug("MQTT connected OK returned code=%s",rc)
    else:
        logging.debug("MQTT bad disconnection returned code=%s",rc)
#def connectCallback(client, userdata, flags, rc):
        
#Disconnect callback for MQTT clients
def disconnectCallback(client, userdata, rc):
    mqttClientData = mqttClientDict.get(client)
    if mqttClientData is None:
        logging.debug("MQTT client not found")
        return
    #Reset connection code
    mqttClientData.connectionReturnCode = -1
    mqttClientData.disconnectionReturnCode = rc
    if rc==0:
        logging.debug("MQTT disconnected OK returned code=%s",rc)
    else:
        logging.debug("MQTT bad disconnection returned code=%s",rc)
#def disconnectCallback(client, userdata, flags, rc):

#Connect callback for subscribe command data
def connectSubscribeCommandDataCallback(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC_SUBSCRIBE.format("#"))
#def connectSubscribeCommandDataCallback(client, userdata, flags, rc):

#callback with received command data
def subscribeCommandDataCallback(client, userdata, msg):
    cd = CommandData("","","")
    try:
        logging.debug(msg.topic + ": " + str(msg.payload))
        json_command = json.loads(msg.payload)
        cd.deviceid = json_command["deviceid"]
        cd.command = json_command["command"]
        cd.payload = json_command["payload"]
        subscribeCommandDataQueue.put(cd)
    except Exception as e:
        logging.debug("ERR MQTT Exception (subscribe command): {}".format(e))
#def def subscribeCommandDataCallback(client, userdata, msg):

#method to establish a connection to the given broker address and to wait
#wait until the connection is established
#client: MQTT client object with which the connection should be established
#brokerAddress: address of the MQTT broker to connect to
def connectMQTTBrokerAndWait(client, brokerAddress): 
    #Connect to the broker
    client.connect(brokerAddress)
    #Wait until the connection event has been called.
    waitForMQTTConnect(client)
#def connectMQTTBrokerAndWait(client, brokerAddress):

#Method to wait until the connection to the MQTT broker is established.
def waitForMQTTConnect(client):
    mqttClientData = mqttClientDict.get(client)
    if mqttClientData is None:
        logging.debug("MQTT client not found")
        return
    #Wait until the connection event has been called.
    while mqttClientData.connectionReturnCode == -1:
        #logging.debug("MQTT in connect wait loop")
        time.sleep( 0.0001 )
#def waitForMQTTConnect():

#method to disconnect the MQTT broker and wait until the connection is disconnected
#client: MQTT client which should disconnect the connection
def disconnectMQTTBrokerAndWait(client): 
    #Disconnect from the broker
    client.disconnect()
#Wait until the disconnect event has been called
    waitForMQTTDisconnect(client)
#def disconnectMQTTBrokerAndWait(client):
    
#Method to wait until the connection to the MQTT broker is established.
def waitForMQTTDisconnect(client):
    mqttClientData = mqttClientDict.get(client)
    if mqttClientData is None:
        logging.debug("MQTT client not found")
        return
    #Wait until the disconnection event has been called.
    while mqttClientData.disconnectionReturnCode == -1:
        #logging.debug("MQTT in disconnect wait loop")
        time.sleep( 0.0001 )
#def waitForMQTTDisconnect():

#method to send the passed data to the MQTT broker
#client: MQTT client which should publish the data
#clientName: name of the client
#dataName: name of datavalue to publish
#dataValue: Datavalue
def publishMQTTData(client, clientName, dataName, dataValue):
    mqttClientData = mqttClientDict.get(client)
    if mqttClientData is None:
        logging.debug("MQTT client not found")
        return
    #Execute only if the connection has not been disconnected and a connection exists
    if mqttClientData.disconnectionReturnCode == -1 and mqttClientData.connectionReturnCode == 0:
        #Publish message
        returnValue = client.publish(str(clientName) + "/" + str(dataName), dataValue, qos=0, retain=MQTT_PUBLISH_RETAIN)
        logging.debug("MQTT Wait for publish")
        #Wait until the message has been published or the connection has been disconnected
        while not returnValue.is_published and mqttClientData.disconnectionReturnCode == -1:
            #logging.debug("MQTT in publish wait loop")
            time.sleep( 0.0001 )
#def publishMQTTData(client, clientName, dataName, dataValue):

#method to send the passed data to the MQTT broker
#client: MQTT client which should publish the data
#clientName: name of the client
#eventData: Event data to publish
def publishMQTTData(client, clientName, eventData):
    mqttClientData = mqttClientDict.get(client)
    if mqttClientData is None:
        logging.debug("MQTT client not found")
        return
    #Execute only if the connection has not been disconnected and a connection exists
    if mqttClientData.disconnectionReturnCode == -1 and mqttClientData.connectionReturnCode == 0:
        #Publish message
        returnValue = client.publish(clientName.format(eventData.deviceid) + "/" + str(eventData.eventtype), str(eventData.eventvalue), qos=0, retain=MQTT_PUBLISH_RETAIN)
        logging.debug("MQTT Wait for publish")
        #Wait until the message has been published or the connection has been disconnected
        while not returnValue.is_published and mqttClientData.disconnectionReturnCode == -1:
            #logging.debug("MQTT in publish wait loop")
            time.sleep( 0.0001 )
#def publishMQTTData(client, clientName, dataName, dataValue):

#Method to send event data to mqtt
def publishEventDataToMQTT():
    while True:
        #There must be a message in the queue
        if publishEventDataQueue.empty():
            continue
        #Create MQTT client object and add to dict
        client = mqtt.Client(MQTT_CLIENT_ID_BASE + "_PublishEventData")
        mqttClientDict.update({client: MQTTClientData(-1, -1)})
        mqttClientData = mqttClientDict[client]
        #Set events
        client.on_connect = connectCallback
        client.on_disconnect = disconnectCallback
        #Set username and pasword if authentication is required
        if MQTT_AUTHENTICATION:
            client.username_pw_set(username=MQTT_BROKER_USER,password=MQTT_BROKER_PASSWORD)
        try:
            client.loop_start()
            #Connect to the MQTT broker
            connectMQTTBrokerAndWait(client, MQTT_BROKER_IP)
            #Execute if connection was successfully
            if mqttClientData.connectionReturnCode == 0:
                #Transmit all entries from the queue
                while publishEventDataQueue.qsize() > 0:
                    # Get item
                    item = publishEventDataQueue.get()
                    #Only publish valid items
                    if item is None:
                        continue
                    publishMQTTData(client, MQTT_TOPIC_PUBLISH, item)
                    #Disconnect from MQTT broker           
                disconnectMQTTBrokerAndWait(client)
        except Exception as e:
            client.disconnect()
            logging.debug("ERR MQTT Exception (publish event): {}".format(e))
        finally:
            client.loop_stop()
            if(mqttClientDict.get(client) != None):
                mqttClientDict.pop(client)
        time.sleep( 0.0001 )
#def sendEventDataToMQTT():

#Method to send mqtt data
def startSubscribeCommandDataFromMQTT():
        #Create MQTT client object and add to dict
        client = mqtt.Client(MQTT_CLIENT_ID_BASE + "_SubscribeCommandData")
        #Set events
        client.on_connect = connectSubscribeCommandDataCallback
        client.on_message = subscribeCommandDataCallback
        #Set username and pasword if authentication is required
        if MQTT_AUTHENTICATION:
            client.username_pw_set(username=MQTT_BROKER_USER,password=MQTT_BROKER_PASSWORD)
        #Connect to the broker
        client.connect(MQTT_BROKER_IP)            
        client.loop_forever()
#def startSubscribeCommandDataFromMQTT():

#-----------------Main program---------------------------
if __name__ == "__main__":
    cliArgParser = argparse.ArgumentParser()
    cliArgParser.add_argument("--log")

    cliArgs = cliArgParser.parse_args()
    loglevel = cliArgs.log

    try:
        logging.basicConfig(level=loglevel.upper())
    except:
        logging.basicConfig(level="INFO")

    sendEventDataToMQTTThread = Thread(target=publishEventDataToMQTT)
    sendEventDataToMQTTThread.start()
    sendEventDataToMQTTThread = Thread(target=startSubscribeCommandDataFromMQTT)
    sendEventDataToMQTTThread.start()
    gardenaEventSubscribeThread = Thread(target=gardenaEventSubscribe)
    gardenaEventSubscribeThread.start()
    gardenaCommandPublishThread = Thread(target=gardenaCommandPublish)
    gardenaCommandPublishThread.start()

    while True:

        time.sleep(10)