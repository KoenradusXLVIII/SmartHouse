# Public packages
from sqlalchemy import Column, Integer, TIMESTAMP, Float, ForeignKey
from sqlalchemy.orm import relationship, backref

# Import base
from nebula_alchemy.base import Base


class Processed(Base):
    __tablename__ = 'processed'

    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP)
    sensor_id = Column(Integer, ForeignKey('sensors.id'))
    sensor = relationship('Sensor', backref=backref('processed', uselist=True))
    value = Column(Float)
    interval_id = Column(Integer, ForeignKey('intervals.id'))
    interval = relationship('Interval', backref=backref('processed', uselist=True))
    algorithm_id = Column(Integer, ForeignKey('algorithms.id'))
    algorithm = relationship('Algorithm', backref=backref('processed', uselist=True))

    def __init__(self, timestamp, sensor, value, interval_id, algorithm_id):
        self.timestamp = timestamp
        self.sensor = sensor
        self.value = value
        self.interval = interval_id
        self.algorithm = algorithm_id
