import sqlalchemy.pool as pool
import psycopg2


def getconn():
    c = psycopg2.connect(username='ed', host='127.0.0.1', dbname='test')
    return c


mypool = pool.QueuePool(getconn, max_overflow=10, pool_size=5)

# get a connection
# The return value of this method is a DBAPI connection that’s contained within a transparent proxy:
conn = mypool.connect()

# use it
cursor = conn.cursor()
cursor.execute("select foo")

# 1. The purpose of the transparent proxy is to intercept the close() call, such that instead of the DBAPI connection being closed, it is returned to the pool
# 2. The proxy also returns its contained DBAPI connection to the pool when it is garbage collected
# 3. The close() step also performs the important step of calling the rollback() method of the DBAPI connection. This is so that any existing transaction on the connection is removed, not only ensuring that no existing state remains on next usage, but also so that table and row locks are released as well as that any isolated data snapshots are removed. This behavior can be disabled using the reset_on_return option of Pool.

# "close" the connection.  Returns
# it to the pool.
conn.close()
