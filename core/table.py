from model import *

ins = users.insert()

print ins   # INSERT INTO users (id, name, fullname) VALUES (:id, :name, :fullname)


ins = users.insert().values(name='jack', fullname='jack jones')

print ins  # INSERT INTO users (name, fullname) VALUES (:name, :fullname)


print users.update().where(users.c.id == 1).values(name='hello') # UPDATE users SET name=:name WHERE users.id = :id_1

# bind params  since the data consists of literal values, SQLAlchemy automatically generates bind parameters for them.
print ins.compile().params  # {'fullname': 'jack jones', 'name': 'jack'}

conn = engine.connect()  # <sqlalchemy.engine.base.Connection object at 0x10e9ec410>

print conn


result = conn.execute(ins)


print result  # <sqlalchemy.engine.result.ResultProxy object at 0x10978f7d0>

print result.inserted_primary_key # [1]


ins = users.insert()
conn.execute(ins, id=2, name='wendy', fullname='Wendy Williams')  # can be less three values 

"""
each dictionary must have the same set of keys; i.e. you cant have fewer keys in some dictionaries than others. This is because the Insert statement is compiled against the first dictionary in the list, and its assumed that all subsequent argument dictionaries are compatible with that statement.
"""

# based on first dict compile params

conn.execute(addresses.insert(), [
    {'user_id': 1, 'email_address': 'jack@yahoo.com'},
    {'user_id': 1, 'email_address': 'jack@msn.com'},
    {'user_id': 2, 'email_address': 'www@www.org'},
    {'user_id': 2, 'email_address': 'wendy@aol.com'},
])


from sqlalchemy.sql import select


s = select([users])

print s  # SELECT users.id, users.name, users.fullname FROM users

result = conn.execute(s)

print result  # <sqlalchemy.engine.result.ResultProxy object at 0x10acc1e10>

row = result.fetchone()  

# through dictionary access
print("name:", row['name'], "; fullname:", row['fullname'])
# through index access
print("name:", row[1], "; fullname:", row[2])
# through users columns 
print("name:", row[users.c.name], "; fullname:", row[users.c.fullname])

for i in result:
    print i   # tuple-like result.  (1, u'jack', u'jack jones')

result.close()


for i in conn.execute(select([users.c.fullname, users.c.name])):
    print i   # (u'jack jones', u'jack')


s = select([users, addresses]).where(users.c.id == addresses.c.user_id)

print s  #  SELECT users.id, users.name, users.fullname, addresses.id, addresses.user_id, addresses.email_address FROM users, addresses

for row in conn.execute(s):
    print row

# am binary expression
print str(users.c.id == addresses.c.user_id)  # users.id = addresses.user_id


print(users.c.id == 7)  # users.id = :id_1

print (users.c.id == 7).compile().params  # {u'id_1': 7}

print('fred' > users.c.name)   # users.name < :name_1

print(users.c.name == None)   # users.name IS NULL

print(users.c.name + users.c.fullname)  # users.name || users.fullname  concat column


from sqlalchemy.sql import and_, or_, not_

# users.name LIKE :name_1 AND users.id = addresses.user_id AND (addresses.email_address = :email_address_1 OR addresses.email_address = :email_address_2) AND users.id <= :id_1

print(and_(
        users.c.name.like('j%'),
        users.c.id == addresses.c.user_id,
        or_(
              addresses.c.email_address == 'wendy@aol.com',
              addresses.c.email_address == 'jack@yahoo.com'
        ),
        not_(users.c.id > 5)
       )
  )


s = select([(users.c.fullname +
               ", " + addresses.c.email_address).
                label('title')]).\
        where(
           and_(
               users.c.id == addresses.c.user_id,
               users.c.name.between('m', 'z'),
               or_(
                  addresses.c.email_address.like('%@aol.com'),
                  addresses.c.email_address.like('%@msn.com')
               )
           )
        )

print s.compile()
for i in conn.execute(s):
    print i


# user multi where replace and
s = select([(users.c.fullname +
               ", " + addresses.c.email_address).
                label('title')]).\
        where(users.c.id == addresses.c.user_id).\
        where(users.c.name.between('m', 'z')).\
        where(
               or_(
                  addresses.c.email_address.like('%@aol.com'),
                  addresses.c.email_address.like('%@msn.com')
               )
        )

from sqlalchemy.sql import text
s = text(
     "SELECT users.fullname || ', ' || addresses.email_address AS title "
         "FROM users, addresses "
         "WHERE users.id = addresses.user_id "
         "AND users.name BETWEEN :x AND :y "
         "AND (addresses.email_address LIKE :e1 "
             "OR addresses.email_address LIKE :e2)")
conn.execute(s, x='m', y='z', e1='%@aol.com', e2='%@msn.com').fetchall()


stmt = text("SELECT * FROM users WHERE users.name BETWEEN :x AND :y")
print stmt  # SELECT * FROM users WHERE users.name BETWEEN :x AND :y
stmt = stmt.bindparams(x="m", y="z")
print stmt  # SELECT * FROM users WHERE users.name BETWEEN :x AND :y
