from sqlalchemy import create_engine
import sqlalchemy.pool as pool
import psycopg2


def getconn():
    c = psycopg2.connect(username='ed', host='127.0.0.1', dbname='test')
    # do things with 'c' to set up
    return c

# creator is there as a last resort for when a DBAPI has some form of connect that is not at all supported by SQLAlchemy
engine = create_engine('postgresql+psycopg2://', creator=getconn)


