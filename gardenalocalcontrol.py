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
from config import MQTT_TOPIC_SUBSCRIBE
from config import MQTT_TOPIC_PUBLISH
from config import GARDENA_NNG_FORWARD_PATH
from config import SCRIPT_VERSION

#Class to store nng EventData
class EventData:
    def __init__(self, deviceid, eventtype, eventvalue):
        self.deviceid = deviceid
        self.eventtype = eventtype
        self.eventvalue = eventvalue




#Queue for publish events
publishQueue = Queue()

def gardenaCommandBuilder(command, device, meta):
    gardenaCommand = ""
    return gardenaCommand

def gardenaEventInterpreter(event_str):
    ed = EventData("","","")

    try:
        gardenaEventDict = json.loads(event_str)
        deviceId = gardenaEventDict[0]["entity"]["device"]
        subPath = gardenaEventDict[0]["entity"]["path"]
        sequence = gardenaEventDict[0]["metadata"]["sequence"]
        source = gardenaEventDict[0]["metadata"]["source"]
        operation = gardenaEventDict[0]["op"]
        payload = gardenaEventDict[0]["payload"]
        payload_action = list(payload.keys())[0]

        logging.debug("gardenaEvtParse: Message from deviceId: {}, payload: {}, payload_action: {}".format(deviceId, payload, payload_action))

    except Exception as e:
        logging.debug("ERR Parsing JSON-Data: {}".format(e))
        # if no valid interpetation is possible set type to unknown and value to raw event_str
        ed.eventtype = "unknown"
        ed.eventvalue = event_str

    # send to publish queue
    publishQueue.put(ed)
    return ed

def gardenaEventSubscribeTask():
    logging.debug("gardenaEventSubscribe Task is start reading")
    while True:
        with Sub0(dial=GARDENA_NNG_FORWARD_PATH) as sub0:
            sub0.subscribe("")
            received_telegram = sub0.recv()
            logging.debug("received telegram: %s", received_telegram)
            gardenaEventInterpreter(received_telegram.decode('utf-8'))

#Connect callback for MQTT clients
def connectCallback(client, userdata, flags, rc):
    global mqttConnectionReturnCode_M
    global mqttDisconnectionReturnCode_M
    #Reset disconnection code
    mqttDisconnectionReturnCode_M = -1
    mqttConnectionReturnCode_M = rc
    if rc==0:
        print("MQTT connected OK returned code=",rc)
    else:
        print("MQTT bad disconnection returned code=",rc)
#def connectCallback(client, userdata, flags, rc):
        
#Disconnect callback for MQTT clients
def disconnectCallback(client, userdata, rc):
    global mqttDisconnectionReturnCode_M
    global mqttConnectionReturnCode_M
    #Reset connection code
    mqttConnectionReturnCode_M = -1
    mqttDisconnectionReturnCode_M = rc
    if rc==0:
        print("MQTT disconnected OK returned code=",rc)
    else:
        print("MQTT bad disconnection returned code=",rc)
#def disconnectCallback(client, userdata, flags, rc):
     
#Methode um eine Verbindung zu der übergebenen Broker Adresse herzustellen und
#zu warten, bis die Verbindung hergestellt wurde
#client: MQTT Client Objekt mit dem die Verbindung hergestellt werden soll
#brokerAddress: Adresse des MQTT Brokers, zu dem eine Verbindung hergestellt werden soll
def connectMQTTBrokerAndWait(client, brokerAddress): 
    #Verbindung zum Broker herstellen
    client.connect(brokerAddress)
    #Solange warten, bis das Connection Event aufgerufen wurde
    waitForMQTTConnect()
#def connectMQTTBrokerAndWait(client, brokerAddress):

#Methode um zu warten, bis die Verbindung zum MQTT Broker hergestellt wurde
def waitForMQTTConnect():
    global mqttConnectionReturnCode_M
    #Solange warten, bis das Connection Event aufgerufen wurde
    while mqttConnectionReturnCode_M == -1:
        print("MQTT in connect wait loop")
        time.sleep(1)
#def waitForMQTTConnect():

#Methode um die Verbindung zum MQTT Broker zu trennen und zu warten bis die Verbindung getrennt wurde
#client: MQTT Client der die Verbindung trennen soll
def disconnectMQTTBrokerAndWait(client): 
    #Verbindung zum Broker trennen
    client.disconnect()
    #Solange warten, bis das Disconnect Event aufgerufen wurde
    waitForMQTTDisconnect()
#def disconnectMQTTBrokerAndWait(client):
    
#Methode um zu warten, bis die Verbindung zum MQTT Broker hergestellt wurde
def waitForMQTTDisconnect():
    global mqttDisconnectionReturnCode_M
    #Solange warten,bis das Disconnection Event aufgerufen wurde
    while mqttDisconnectionReturnCode_M == -1:
        print("MQTT in disconnect wait loop")
        time.sleep(1)
#def waitForMQTTConnect():

#Methode um die übergebenen Daten an den MQTT Broker zu senden
#client: MQTT Client der die Daten veröffentlichen soll
#clientName: Name des Clients
def publishMQTTData(client, clientName, dataName, dataValue):
    global mqttDisconnectionReturnCode_M
    global mqttConnectionReturnCode_M
    #Nur ausführen, wenn die Verbindung nicht getrennt wurde und eine Verbindung besteht
    if mqttDisconnectionReturnCode_M == -1 and mqttConnectionReturnCode_M == 0:
        #Nachricht veröffentlichen
        returnValue = client.publish(str(clientName) + "/" + str(dataName), dataValue, qos=0, retain=MQTT_PUBLISH_RETAIN)
        print("MQTT Wait for publish")
        #Warten bis die Nachricht veröffentlicht wurde oder die Verbindung getrennt wurde
        while not returnValue.is_published and mqttDisconnectionReturnCode_M == -1:
            print("MQTT in publish wait loop")
            time.sleep(1)
#def publishMQTTData(client, clientName, dataName, dataValue):

#Method to send mqtt data
def sendMQTTData():
    global mqttConnectionReturnCode_M
    global mqttDisconnectionReturnCode_M
    while True:
        #Wenn keine Elemente in der Queue sind Schleifendurchlauf abbrechen
        if publishQueue.empty():
            continue
        mqttConnectionReturnCode_M = -1
        mqttDisconnectionReturnCode_M = -1
        #MQTT Client Objekt erstellen
        client = mqtt.Client(MQTT_TOPIC_SUBSCRIBE)
        #Connect Callback zuweisen
        client.on_connect = connectCallback
        #Disconnect Callback zuweisen
        client.on_disconnect = disconnectCallback
        if MQTT_AUTHENTICATION:
            #Benutzername und Passwort setzen
            client.username_pw_set(username=MQTT_BROKER_USER,password=MQTT_BROKER_PASSWORD)
        try:
            client.loop_start()
            #Verbindung zum MQTT Broker herstellen
            connectMQTTBrokerAndWait(client, MQTT_BROKER_IP)
            #Wenn Connection erfolgreich ausgeführt wurde ausführen
            if mqttConnectionReturnCode_M == 0:
                #Alle Einträge aus der Queue übermitteln
                while publishQueue.qsize() > 0:
                    # Get item
                    item = publishQueue.get()
                    # check for stop
                    if item is None:
                        continue
                    publishMQTTData(client, MQTT_TOPIC_PUBLISH, item.eventtype, item.eventvalue)
                #Verbindung zum MQTT Broker trennen
                disconnectMQTTBrokerAndWait(client)
        except:
            client.disconnect()
            print("MQTT Exception")
        finally:
            client.loop_stop()
        #TODO Thread abgeben?
#def sendMQTTData():

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

    sendMQTTDataThread = Thread(target=sendMQTTData)
    sendMQTTDataThread.start()
    eventSubscribeThread = Thread(target=gardenaEventSubscribeTask)
    eventSubscribeThread.start()

    while True:

        time.sleep(10)