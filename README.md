# GardenaLocalControl

## Leading words

This small script is for simple communication between the Gardena Smart Gateway and a MQTT broker of your desire. It has been tested with the Gardena Smart Gateway (Art. No. 190005). Required prequisions are rooting the Gateway and enabling the nngforward-service (see FAQ below)

## Commands to send via GardenaLocalControl
For comfort several commands are available to send via MQTT. The main job is done by the script. Simply put a command to MQTT Topic: 

    GardenaLocalControl/<device_id>/Command

in the following JSON format:

    {
        "command": <command_name>
        "payload": <payload_depending_on_command>
    }
### Available Commands
For the first step only basic commands are available for using it with a smart-home system as openHAB or Home-Assistant. More Commands e.g. for Gardena Smart Irrigation Control may follow later.
#### mower_timer
Start manual mowing with time period. According to app control the valid values are limited to 6 hours. 

accepted payload: integer value for mowing time in seconds

Example:

    {
        "command": mower_timer
        "payload": 3600
    }
#### park_until_next_task
Park mower until next schedule task would be started

accepted payload: "true" (without quotes)

Example:

    {
        "command": park_until_next_task
        "payload": true
    }
#### park_until_further_notice
Park mower permanently

accepted payload: "true" (without quotes)

Example:

    {
        "command": park_until_further_notice
        "payload": true
    }
#### cyclic_status_req
Enable cyclic status requests for specified device in payload

accepted payload: integer value for cyclic status request in seconds

    {
        "command": cyclic_status_req
        "payload": 60
    }

# FAQ

## How do I root my Gardena Smart Gateway
BE AWARE YOU WILL LOSING WARRANTY! ANY MODIFICATIONS WILL BE DONE AT YOUR OWN RISK!

1. Connect to the UART of the Board. You will find the Pins in the official [Gardena documentation](https://github.com/husqvarnagroup/smart-garden-gateway-public)