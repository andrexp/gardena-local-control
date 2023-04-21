# GardenaLocalControl

## Leading words

First, the explained method including installing the script or parts of software in this repository comes with some modification instructions for your Gardena components. Be warned with the all-known words at first: 

⚠️ BE AWARE YOU MAY LOSE YOUR WARRANTY! ANY MODIFICATIONS WILL BE DONE AT YOUR OWN RISK! THE GARDENA SUPPORT MAY NOT BE ABLE TO HELP YOU IF YOU BRICK YOUR GATEWAY OR DEVICE PERMANENTLY! ⚠️

This small script is for simple communication between the Gardena Smart Gateway and a MQTT broker of your desire - **without any need of cloud infrastructure**. It has been tested with the Gardena Smart Gateway (Art. No. 190005). Required prequisions are rooting the Gateway and enabling the nngforward-service (see FAQ below)

## Installation
### Requirements
Python3

### Clone repository

    git clone https://github.com/andrexp/gardena-local-control.git
    cd gardena-local-control
### Install and execute
Simply use the "install"-script:

    sudo chmod +x install
    sudo ./install

This will copy the gardenalocalcontrol.py script to /opt/gardenalocalcontrol and executes instantly after

### Install as server
Simply use the "install_service"-script:

    sudo ./install_service

This will also copy the gardenalocalcontrol.py script to /opt/gardenalocalcontrol but in addition a .service-File for systemd is created. This will install the script as service and make it start at boot automatically.

## Status messages to receive via GardenaLocalControl
The script subscribes to the interprocess communication of lemonbeatd (rf-component which does communication with the wireless devices as the Gardena Smart Sileno mowers) and the Gardena cloud/shadoway connector. If a message is received, the script tries to interpet any component of it. Because not all of the information to be gathered is known at this point all information are pushed to the MQTT broker as it is. Therefore the following format and topics are used:

    GardenaLocalControl/<device_id>/<attribute> Value

device_id: Internal Device-ID of your Gardena device such as Smart Sileno mowers\
attribute: Interpreted data from subscription as described above

Example output for battery level:

    GardenaLocalControl/012345678901234567890/battery_level 70          # 70% battery power

Example output for rf-signal-strength:

    GardenaLocalControl/012345678901234567890/rf_link_quality 100       # best link quality

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

    GardenaLocalControl/012345678901234567890/Command
    {
        "command": mower_timer
        "payload": 3600
    }
#### park_until_next_task
Park mower until next schedule task would be started

accepted payload: "true" (without quotes)

Example:

    GardenaLocalControl/012345678901234567890/Command
    {
        "command": park_until_next_task
        "payload": true
    }
#### park_until_further_notice
Park mower permanently

accepted payload: "true" (without quotes)

Example:

    GardenaLocalControl/012345678901234567890/Command
    {
        "command": park_until_further_notice
        "payload": true
    }
#### cyclic_status_req_enable/cyclic_status_req_disable
Enable cyclic status requests for specified device in payload. The time between the requests is selected by the command payload. Setting the time to "0" (without quotes) disables the cyclic status request. Note the time selection through the payload affects all cyclic status requests and cannot be selected separately at this time (TODO).

accepted payload: integer value for cyclic status request in seconds

Example: 

    GardenaLocalControl/012345678901234567890/Command
    {
        "command": cyclic_status_req_enable     # enables cyclic status requests
        "payload": 60                           # set time to 60 sec
    }
## FAQ

### How do I root my Gardena Smart Gateway and prepare it for using the script
BE AWARE YOU WILL LOSING WARRANTY! ANY MODIFICATIONS WILL BE DONE AT YOUR OWN RISK!

1.  Connect to the UART of the Board. You will find the Pins and required settings in the official [Gardena documentation](https://github.com/husqvarnagroup/smart-garden-gateway-public), you will need a USB to UART-Adapter or a RaspberryPi to be able to connect your computer.
2.  Use a terminal application such as PuTTy (on Windows) or screen (on Linux)
3.  Connect power of the gateway
4.  Wait until you see a login shell usually something like:

        GARDENA-12affe12 login: 

    will appear.
5.  Quickly type in "root" (without quotes)
6.  You have successful gained root access
7.  Put in your public SSH key and don't forget to use following command to prevent deletion of the key in case of a firmware upgrade:

        fw_setenv dev_debug_allow_local_ssh 1

8.  Enable nngforward by the following command:

        fw_setenv dev_debug_enable_nngforward 1

9.  Have fun!

### Where can I find the device_id
The simplest way to obatin your desired device_id is to observe the output of the GardenaLocalControl when controlling e.g. a mower or any other device through the App.

## Thanks to the Gardena devs for the hints and the support!
[@rettichschnidi](https://github.com/rettichschnidi)\
[@easybe](https://github.com/easybe)\
[@broglep-work](https://github.com/broglep-work)