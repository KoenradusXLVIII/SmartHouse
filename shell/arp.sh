#!/bin/sh

# Author: Joost Verberk
# Date: 22-8-2016

# ---------------------------------------------------
# Detect presence by detecting smartphone on WiFi
# ---------------------------------------------------

# ---------------------------------------------------
# Declaration of script variables
# ---------------------------------------------------
MAC_ONEPLUS6="c0:ee:fb:05:1c:0a"
MAC_ONEPLUS6_MQTT="C0EEFB051C0A"

# ---------------------------------------------------
# Main program loop 
# ---------------------------------------------------

present=$(sudo arp-scan --localnet | grep $MAC_ONEPLUS6 | wc -l) 

if [ $present = 1 ]; then
	mosquitto_pub -h joostverberk.nl -m "1" -t "nodes/B827EBF288F8/devices/$MAC_ONEPLUS6_MQTT" -u "vjmpotre" -P "#ukELk48z0js" -r
	if [ "$1" = "-v" ]; then
		echo "$MAC_ONEPLUS6 detected on network"	
	fi
else
	mosquitto_pub -h joostverberk.nl -m "0" -t "nodes/B827EBF288F8/devices/$MAC_ONEPLUS6_MQTT" -u "vjmpotre" -P "#ukELk48z0js" -r
	if [ "$1" = "-v" ]; then
		echo "$MAC_ONEPLUS6 not detected on network"	
	fi
fi
