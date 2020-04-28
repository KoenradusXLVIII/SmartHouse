# Public packages
from sqlalchemy import Column, VARCHAR, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

# Import base
from nebula_alchemy.base import Base


class Sensor(Base):
    __tablename__ = 'sensors'

    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(length=100))
    quantity_id = Column(Integer, ForeignKey('quantities.id'))
    quantity = relationship('Quantity', backref=backref('sensor', uselist=False))
    node_id = Column(VARCHAR(length=36), ForeignKey('nodes.id'))
    node = relationship('Node', backref=backref('sensor', uselist=False))

    def __init__(self, name, quantity, node):
        self.name = name
        self.quantity = quantity
        self.node = node
