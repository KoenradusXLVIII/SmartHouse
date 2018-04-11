import urllib
import sys
from time import sleep
import logging
import logging.handlers

sprinkler_on = "http://192.168.1.112/water_mode/manual"
sprinkler_off = "http://192.168.1.112/water_mode/auto"

# Set up logging
log_level = logging.INFO
handler = logging.handlers.SysLogHandler(address = '/dev/log')
formatter = logging.Formatter('%(name)s [%(levelname)s] %(message)s')
handler.setLevel(log_level)
handler.setFormatter(formatter)
# Create logging instance
logger = logging.getLogger('sprinkler')
logger.setLevel(log_level)
logger.addHandler(handler)

if(len(sys.argv) > 1):
	if('off' in sys.argv[1]):
		try:
			f = urllib.urlopen(sprinkler_off)
			logger.info("Sprinklers manually disabled")
		except:
			logger.error("Unable to connect to sprinkler system")
			sys.exit()
	else:
		try:
			sprinkler_duration = int(sys.argv[1]) # min
			try:
				f = urllib.urlopen(sprinkler_on)
				logger.info("Sprinklers enabled for %d minutes" % (sprinkler_duration))
				sleep(sprinkler_duration*60)
				f = urllib.urlopen(sprinkler_off)
				logger.info("Sprinklers disabled after %d minutes" % (sprinkler_duration))
			except:
				logger.error("Unable to connect to sprinkler system")
				sys.exit()
		except TypeError:
			logger.warning("No integer sprinkler interval supplied")
else:
    logger.warning("No sprinkler arguments supplied")
