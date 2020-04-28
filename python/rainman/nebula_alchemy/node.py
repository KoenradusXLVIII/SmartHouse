# Public packages
from sqlalchemy import Column, VARCHAR, ForeignKey
from sqlalchemy.orm import relationship, backref

# Import base
from nebula_alchemy.base import Base


class Node(Base):
    __tablename__ = 'nodes'

    id = Column(VARCHAR(length=36), primary_key=True)
    name = Column(VARCHAR(length=100))
    user_id = Column(VARCHAR(length=36), ForeignKey('users.id'))
    user = relationship('User', backref=backref('node', uselist=False))

    def __init__(self, name, user):
        self.name = name
        self.user = user
