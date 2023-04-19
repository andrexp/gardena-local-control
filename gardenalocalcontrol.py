#!/usr/bin/python3
# coding: utf-8

from config import MQTT_BROKER_IP
from config import MQTT_BROKER_PORT
from config import MQTT_AUTHENTICATION
from config import MQTT_USER
from config import MQTT_PASSWORD
from config import MQTT_TOPIC_SUBSCRIBE
from config import MQTT_TOPIC_PUBLISH
from config import SCRIPT_VERSION

import logging
import threading
import time
import json
from pynng import Sub0

def gardenaCommandBuilder(command, device, meta):
    gardenaCommand = ""
    return gardenaCommand

def gardenaEventInterpreter(event_str):
    try:
        gardenaEventDict = json.loads(event_str)
    except:
        pass

def gardenaEventSubscribeTask(name):
    logging.debug("gardenaEventSubscribe Task is starting reading: ", name)
    with Sub0(dial='ipc:///tmp/lemonbeatd-event.ipc') as sub0:
        sub0.subscribe("")
        gardenaEventInterpreter(sub0.recv().decode('utf-8'))

if __name__ == "__main__":
    
