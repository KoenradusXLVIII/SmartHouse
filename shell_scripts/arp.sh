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
STATEFILE_JOOST="/home/pi/repository/shell_scripts/ARP_JOOST"
LOGFILE="/home/pi/repository/shell_scripts/arp.log"
OFFLINE_DELAY=6 # x5 mins = 30 mins.

# ---------------------------------------------------
# Main program loop
# ---------------------------------------------------

# Set internal field separator
IFS=";"

# Read previous state
PrevState_Joost=$(cat $STATEFILE_JOOST)
read ConnectionState ConnectionTries <<< "$PrevState_Joost"
echo "Previous connection state: $ConnectionState"
echo "Previous connection state duration: $ConnectionTries"

# Poll current state
CurState_Joost=$(sudo arp-scan --localnet | grep $MAC_JOOST | wc -l)

# Detect state change
if [ $CurState_Joost != $PrevState_Joost ]; then
	# Change detected
	if [ $CurState_Joost = 1 ]; then
		# Smartphone detected on network
		echo "$(date): Joost arrived home" >> $LOGFILE
	else
		# Smartphone not detected on network
		if [ $ConnectionTries > $OFFLINE_DELAY ]; then
			# Only log after Smartphone not seen for 30 mins
			$ConnectionTries = 0;
			echo "$(date): Joost left home" >> $LOGFILE
		else
			# Otherwise increase counter
			ConnectionTries=$((ConnectionTries+1))
			echo "$ConnectionTries"
		fi
	fi
fi

# Write to STATEFILE
echo "$ConnectionState;$ConnectionTries" > $STATEFILE_JOOST
