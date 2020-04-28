# Public packages
from sqlalchemy import Column, VARCHAR

# Import base
from nebula_alchemy.base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(VARCHAR(length=36), primary_key=True)
    name = Column(VARCHAR(length=32))
    password = Column(VARCHAR(length=256))  # Todo: change column name in MySQL
    api_key = Column(VARCHAR(length=36))

    def __init__(self, name, password, api_key):
        self.name = name
        self.password = password
        self.api_key = api_key
