from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import mapper
from sqlalchemy.pool import QueuePool, NullPool

engine = create_engine('sqlite:///db', poolclass=QueuePool)
# disable pool
engine = create_engine('sqlite:///db', poolclass=NullPool)