import urllib
import sys
from time import sleep

sprinkler_on = "http://192.168.1.112/water_mode/manual"
sprinkler_off = "http://192.168.1.112/water_mode/auto"

if(len(sys.argv) > 1):
    try:
        sprinkler_duration = int(sys.argv[1]) # min
        try:
            f = urllib.urlopen(sprinkler_on)
            print "Sprinklers enabled for %d minutes" % (sprinkler_duration)
            sleep(sprinkler_duration*60)
            f = urllib.urlopen(sprinkler_off)
            print "Sprinklers disabled after %d minutes" % (sprinkler_duration)
        except:
            print "Unable to connect to sprinkler system"
            sys.exit()
    except TypeError:
        print "[ERROR]: No integer sprinkler interval supplied"
else:
    print "[ERROR]: No sprinkler interval supplied"
