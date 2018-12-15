import requests
import sys
from time import sleep
import logger

sprinkler_on = "http://192.168.1.112/water_mode/manual"
sprinkler_off = "http://192.168.1.112/water_mode/auto"

# Set up logger
log_client = logger.Client(name='sprinkler')

if(len(sys.argv) > 1):
	if('off' in sys.argv[1]):
		try:
			requests.get(sprinkler_off)
			log_client.info("Sprinklers manually disabled")
		except:
			log_client.error("Unable to connect to sprinkler system")
			sys.exit()
	else:
		try:
			sprinkler_duration = int(sys.argv[1]) # min
			try:
				requests.get(sprinkler_on)
				log_client.info("Sprinklers enabled for %d minutes" % (sprinkler_duration))
				sleep(sprinkler_duration*60)
				requests.get(sprinkler_off)
				log_client.info("Sprinklers disabled after %d minutes" % (sprinkler_duration))
			except:
				log_client.error("Unable to connect to sprinkler system")
				sys.exit()
		except TypeError:
			log_client.warning("No integer sprinkler interval supplied")
else:
	log_client.warning("No sprinkler arguments supplied")
