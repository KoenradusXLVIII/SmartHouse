# Public packages
from sqlalchemy import Column, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship, backref

# Import base
from nebula_alchemy.base import Base

schedules_sensors_association = Table(
    'schedules_sensors', Base.metadata,
    Column('schedule_id', Integer, ForeignKey('schedules.id')),
    Column('sensor_id', Integer, ForeignKey('sensors.id'))
)

class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True)
    interval_id = Column(Integer, ForeignKey('intervals.id'))
    interval = relationship('Interval', backref=backref('schedule', uselist=False))
    algorithm_id = Column(Integer, ForeignKey('algorithms.id'))
    algorithm = relationship('Algorithm', backref=backref('schedule', uselist=False))
    sensors = relationship("Sensor", secondary=schedules_sensors_association)


    def __init__(self, interval, algorithm):
        self.interval = interval
        self.algorithm = algorithm
