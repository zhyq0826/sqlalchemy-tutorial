from gevent.monkey import patch_all
import gevent

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# engine = create_engine('mysql+pymysql://root:@localhost/sqlalchemy_lab?charset=utf8', encoding='utf8', echo=True)
engine = create_engine(
    'mysql+pymysql://root:@localhost/blog?charset=utf8',
    encoding='utf8',
    echo=False,
    pool_size=5,
    pool_recycle=60,
)
DBSession = sessionmaker(bind=engine)


class ConnectionCheck(gevent.Greenlet):

    def _run(self):
        while True:
            gevent.sleep(60)
            # print("loop_recycle_connection")
            # conn = engine.connect()
            # print(conn)
            # print(conn.connection)
            session = DBSession()
            session.execute("select 1")
            session.invalidate()
            session.close()


ccheck = ConnectionCheck()
ccheck.start()
