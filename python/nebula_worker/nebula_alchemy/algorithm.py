# Public packages
from sqlalchemy import Column, Integer, VARCHAR

# Import base
from nebula_alchemy.base import Base


class Algorithm(Base):
    __tablename__ = 'algorithms'

    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(length=32))


    def __init__(self, name):
        self.name = name
