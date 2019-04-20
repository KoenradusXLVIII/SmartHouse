# Local imports
from base import Session
from meas import Meas
from sensor import Sensor
from quantity import Quantity
from node import Node
from user import User

# Extract a session
session = Session()

# Extract all sensors
sensors = session.query(Sensor).all()
meass = session.query(Meas).limit(10)

for meas in meass:
    print('Sensor %s has value %.2f%s' % (meas.sensor.name, meas.value, meas.sensor.quantity.uom))