#coding: utf-8
MQTT_BROKER_IP = '192.168.178.254'                                      # IP address of MQTT Broker
MQTT_BROKER_PORT = 1883					                                        # Port of MQTT Broker
MQTT_AUTHENTICATION = False                                             # Mqtt authentication
MQTT_BROKER_USER = ''			                                              # Mqtt User name
MQTT_BROKER_PASSWORD = ''			                                          # Mqtt password
MQTT_CLIENT_ID_BASE = "GardenaLocalControl"                             # Name des Gateways
MQTT_TOPIC_BASE = MQTT_CLIENT_ID_BASE + "/{0}"                          # Base topic. {0} is for insert the device address
MQTT_TOPIC_SUBSCRIBE = MQTT_TOPIC_BASE.format("#") 		                  # Subscribe topic
MQTT_TOPIC_PUBLISH = MQTT_TOPIC_BASE                                    # Command Topic
MQTT_PUBLISH_RETAIN = False                                             # Publish Command as retain
GARDENA_NNG_FORWARD_PATH_EVT = "ipc:///tmp/lemonbeatd-event.ipc"        # nngforward path from Gardena Smart Gateway to receive events
GARDENA_NNG_FORWARD_PATH_CMD = "ipc:///tmp/lemonbeatd-command.ipc"      # nngforward path from Gardena Smart Gateway to publish commands
SCRIPT_VERSION = '2.0.1.0'					                                    # Version of GardenaLocalControl script
