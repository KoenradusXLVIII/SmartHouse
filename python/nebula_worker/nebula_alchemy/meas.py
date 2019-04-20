# Public packages
from sqlalchemy import Column, Integer, TIMESTAMP, Float, ForeignKey
from sqlalchemy.orm import relationship, backref

# Import base
from nebula_alchemy.base import Base


class Meas(Base):
    __tablename__ = 'meas'

    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP)
    sensor_id = Column(Integer, ForeignKey('sensors.id'))
    sensor = relationship('Sensor', backref=backref('meas', uselist=False))
    value = Column(Float)

    def __init__(self, sensor, value):
        self.sensor = sensor
        self.value = value
