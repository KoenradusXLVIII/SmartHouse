import datetime
import sunrise

s = sunrise.sun(lat=51.441642,long=5.4697225)
sun_rise = s.sunrise(when=datetime.datetime.now())
sun_rise = datetime.time(0,0) + datetime.timedelta(hours=2)
print('sunrise at ',sun_ris)
