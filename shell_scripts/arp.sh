#!/bin/sh

# Author: Joost Verberk
# Date: 22-8-2016

# ---------------------------------------------------
# Detect presence by detecting smartphone on WiFi
# ---------------------------------------------------

# ---------------------------------------------------
# Declaration of script variables
# ---------------------------------------------------
MAC_JOOST="ec:9b:f3:63:92:ba"
STATEFILE_JOOST="/home/pi/shell_scripts/ARP_JOOST"
LOGFILE="/home/pi/shell_scripts/arp.log"

# ---------------------------------------------------
# Main program loop 
# ---------------------------------------------------

PrevState_Joost=$(cat $STATEFILE_JOOST)
echo $PrevState_Joost
CurState_Joost=$(sudo arp-scan --localnet | grep $MAC_JOOST | wc -l | tee $STATEFILE_JOOST) 
echo $CurState_Joost

if [ $CurState_Joost != $PrevState_Joost ]; then
	if [ $CurState_Joost = 1 ]; then
		echo "$(date): Joost arrived home" >> $LOGFILE 
	else
		echo "$(date): Joost left home" >> $LOGFILE 
	fi
fi
