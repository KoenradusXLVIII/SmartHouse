#!/bin/sh

ps="$(ps aux | grep ' python /home/pi/repository/python/pvoutput/process.py' | wc -l)"
if [ $ps -eq 2 ]; then
	echo "Daemon running, stopping..."
	PID=`ps aux | grep ' python /home/pi/repository/python/pvoutput/process.py' | awk '{print $2}'`
	kill=`sudo kill -9 $PID`
	ps="$(ps aux | grep ' python /home/pi/repository/python/pvoutput/process.py' | wc -l)"
	if [ $ps -eq 1 ]; then
		echo "Daemon succesfully stopped"
	else
		echo "Daemon could not be stopped!"
	fi
else
	echo "Daemon not running, starting..."
	python /home/pi/repository/python/pvoutput/process.py >/dev/null 2>&1 &
	ps="$(ps aux | grep ' python /home/pi/repository/python/pvoutput/process.py' | wc -l)"
	if [ $ps -eq 2 ]; then
		echo "Daemon succesfully started"
	else
		echo "Daemon could not be started!"
	fi
fi
