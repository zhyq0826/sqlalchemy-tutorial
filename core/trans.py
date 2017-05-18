from model import addresses, users, engine


conn = engine.connect()

print conn.closed

trans = conn.begin()

try:
    r1 = conn.execute(users.select())
    conn.execute(users.insert().values(name='first jone', fullname=''))
    r2 = conn.execute(users.select())
    for i in r2:
        print i
    # trans.commit()
    # trans.rollback()
except Exception, e:
    trans.rollback()

print conn.closed

with engine.begin() as newconn:
    r1 = newconn.execute(users.select())
    newconn.execute(users.insert().values(name='second jone', fullname=''))
    r2 = newconn.execute(users.select())
    for i in r2:
        print i


r2 = conn.execute(users.select())
for i in r2:
    print i

