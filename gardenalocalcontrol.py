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
from pynng import Sub0
import argparse

from config import MQTT_BROKER_IP
from config import MQTT_BROKER_PORT
from config import MQTT_AUTHENTICATION
from config import MQTT_BROKER_USER
from config import MQTT_BROKER_PASSWORD
from config import MQTT_CLIENT_ID_BASE
from config import MQTT_TOPIC_SUBSCRIBE
from config import MQTT_TOPIC_PUBLISH
from config import GARDENA_NNG_FORWARD_PATH
from config import MQTT_PUBLISH_RETAIN
from config import SCRIPT_VERSION


def gardenaCommandBuilder(command, device, meta):
    gardenaCommand = ""
    return gardenaCommand

def gardenaEventInterpreter(event_str):
#    try:
        gardenaEventDict = json.loads(event_str)
        device = gardenaEventDict[0]["entity"]["device"]
        logging.debug("got message from device: %s", device)
#    except:
#        pass

def gardenaEventSubscribeTask():
    logging.debug("gardenaEventSubscribe Task is start reading")
    while True:
        with Sub0(dial=GARDENA_NNG_FORWARD_PATH) as sub0:
            sub0.subscribe("")
            received_telegram = sub0.recv()
            logging.debug("received telegram: %s", received_telegram)
            gardenaEventInterpreter(received_telegram.decode('utf-8'))

#Class to store nng EventData
class EventData:
    def __init__(self, deviceAddress, eventtype, eventvalue):
        self.deviceAddress = deviceAddress
        self.eventtype = eventtype
        self.eventvalue = eventvalue

#Class to store nng commandData
class CommandData:
    def __init__(self, deviceAddress, eventtype, eventvalue):
        self.deviceAddress = deviceAddress
        self.eventtype = eventtype
        self.eventvalue = eventvalue    

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
    #TODO parse received messages to CommandData
    logging.debug(msg.topic + ": " + str(msg.payload))
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
        returnValue = client.publish(clientName.format(eventData.deviceAddress) + "/" + str(eventData.eventtype), str(eventData.eventvalue), qos=0, retain=MQTT_PUBLISH_RETAIN)
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
            logging.exception(e)
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
    logging.basicConfig(level=loglevel)

    sendEventDataToMQTTThread = Thread(target=publishEventDataToMQTT)
    sendEventDataToMQTTThread.start()
    sendEventDataToMQTTThread = Thread(target=startSubscribeCommandDataFromMQTT)
    sendEventDataToMQTTThread.start()

    while True:
        random = Random()
        publishEventDataQueue.put(EventData("Device{0}".format(random.randint(20,50)), random.randint(10,100), random.randint(50,200)))
        publishEventDataQueue.put(EventData("Device{0}".format(random.randint(20,50)),random.randint(10,100), random.randint(50,200)))
        publishEventDataQueue.put(EventData("Device{0}".format(random.randint(20,50)),random.randint(10,100), random.randint(50,200)))

        time.sleep(10)
