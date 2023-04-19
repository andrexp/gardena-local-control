#coding: utf-8
MQTT_BROKER_IP = '192.168.0.40'		                            # IP address of MQTT Broker
MQTT_BROKER_PORT = 1883					                        # Port of MQTT Broker
MQTT_AUTHENTICATION = False                                     # Mqtt authentication
MQTT_USER = ''			                                        # Mqtt User name
MQTT_PASSWORD = ''			                                    # Mqtt password
MQTT_TOPIC_BASE = "GatewayName/DeviceAddress/"                  # Base topic
MQTT_TOPIC_SUBSCRIBE = MQTT_TOPIC_BASE + 'Value'		        # Subscribe topic
MQTT_TOPIC_PUBLISH = MQTT_TOPIC_BASE + 'Command'                # Command Topic
SCRIPT_VERSION = '1.0.0.0'					                    # Version of GardenaLocalControl script