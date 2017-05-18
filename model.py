from datetime import datetime

from sqlalchemy import Column, Integer, Text , VARCHAR, BLOB, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()


class Tag(Base):

    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(255), nullable=False)
    group_id = Column(Integer)
