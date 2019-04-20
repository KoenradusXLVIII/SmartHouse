# Public packages
from sqlalchemy import Column, VARCHAR, Integer

# Import base
from nebula_alchemy.base import Base


class Quantity(Base):
    __tablename__ = 'quantities'

    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(length=100))
    uom = Column(VARCHAR(length=5))

    def __init__(self, name, uom):
        self.name = name
        self.uom = uom
