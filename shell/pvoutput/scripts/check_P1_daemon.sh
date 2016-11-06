#!/bin/sh

ps="$(ps aux | grep ' python /home/pi/repository/python/pvoutput/P1Update.py' | wc -l)"
if [ $ps -eq 2 ]; then
	echo "Daemon running, no action required"
else
	echo "Daemon not running, starting..."
	python /home/pi/repository/python/pvoutput/P1Update.py >/dev/null 2>&1 &
	ps="$(ps aux | grep ' python /home/pi/repository/python/pvoutput/P1Update.py' | wc -l)"
	if [ $ps -eq 2 ]; then
		echo "Daemon succesfully started"
	else
		echo "Daemon could not be started!"
	fi
fi
