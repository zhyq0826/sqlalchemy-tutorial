
```shell
>>> from sqlalchemy import inspect
>>> from datetime import datetime
>>> from models.blog import Tag
>>> from db.conn import DBSession
>>> tag = Tag()
>>> tag.name = 'tag'
>>> tag.atime = datetime.now()
>>> insp = inspect(tag)
>>> insp.transient           # 没有 primary key 且没有和 session 关联的实例，
True
>>> session = DBSession()
>>> session.add(tag)
>>> insp.transient          
False
>>> insp.pending            # not flush to database
True
>>> session.flush()         # flush failed
"Can't connect to MySQL server on %r (%s)" % (self.host, e)
OperationalError: (OperationalError) (2003, "Can't connect to MySQL server on 'l
ocalhost' ([Errno 61] Connection refused)") None None                         
>>> tag.id
>>> insp.persistent
False
>>> insp.pending
False
>>> insp.transient          # flush 失败，transaction 发生 rollback
True
>>> session.add(tag)
>>> insp.pending
True
>>> session.flush()       # 前一次 flush 失败，在这里必须显式 rollback，即使底层已经发生了 rollback，之后才能继续 flush
"InvalidRequestError: This Session's transaction has been rolled back due to a previous exception during flush. 
To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (OperationalError)"
>>> session.rollback()  # rollback 之后，之前 session 中的实例状态将发生改变
/sqlalchemy/orm/session.py:729: SAWarning: Session state has been changed on a non-active transaction - this state will be discarded.
self.transaction.rollback()
>>> insp.transient    # tag 又回到最初的状态
True
>>> session.add(tag)  # add again
>>> session.flush()
2016-12-30 11:33:55,346 INFO sqlalchemy.engine.base.Engine SELECT DATABASE()
2016-12-30 11:33:55,351 INFO sqlalchemy.engine.base.Engine ()
2016-12-30 11:33:55,367 INFO sqlalchemy.engine.base.Engine SHOW VARIABLES LIKE 'character_set%%'
2016-12-30 11:33:55,373 INFO sqlalchemy.engine.base.Engine ()
2016-12-30 11:33:55,386 INFO sqlalchemy.engine.base.Engine SHOW VARIABLES LIKE 'sql_mode'
2016-12-30 11:33:55,392 INFO sqlalchemy.engine.base.Engine ()
2016-12-30 11:33:55,400 INFO sqlalchemy.engine.base.Engine BEGIN (implicit)
2016-12-30 11:33:55,410 INFO sqlalchemy.engine.base.Engine INSERT INTO tag (name, atime) VALUES (%s, %s)
2016-12-30 11:33:55,416 INFO sqlalchemy.engine.base.Engine ('tag', datetime.datetime(2016, 12, 30, 11, 28, 23, 489066))
>>> tag.id
25
>>> insp.persistent   # persistent 表示 flush 成功，不表示在数据库中有对应的 row
True
>>> session.delete(tag)  # delete tag from session 
>>> insp.deleted         
False
>>> insp.detached
False
>>> insp.persistent
True
>>> session.flush()      
2016-12-30 12:02:06,969 INFO sqlalchemy.engine.base.Engine DELETE FROM tag WHERE tag.id = %s
2016-12-30 12:02:06,975 INFO sqlalchemy.engine.base.Engine (25,)
>>> insp.persistent
False
>>> insp.deleted       # deleted 表示 flush 发生了，如果 detachd 是 false 表示 commit 未发生，transaction 未结束
True
>>> insp.detached
False
>>> session.commit()
2016-12-30 12:07:22,279 INFO sqlalchemy.engine.base.Engine COMMIT
>>> insp.detached   # commit 结束，transaction 结束，detached is true
True
>>> 
```

session 中的 entity 状态

**transient**

instance 没有和 session 产生关联

```shell
>>> tag = Tag()
>>> tag.id = 90
>>> tag.atime = datetime.now()
>>> tag.name = 'tag'
>>> insp = inspect(tag)
>>> insp.transient
True
```

**pendding**

instance 和 session 产生关联，但是没有对应主键或者有主键还不确定是否有对应row

```shell
>>> tag = Tag()
>>> tag.id = 90
>>> tag.atime = datetime.now()
>>> tag.name = 'tag'
>>> insp = inspect(tag)
>>> insp.transient
True
>>> session.add(tag)
>>> insp.transient
False
>>> insp.pending
True
>>> 
```

**persistent**

instance which is loaded from db, associated with session and flushed to db.

实例来自 db 或和 session 关联之后调用过 flush，代表 instance was persistent，如果不调用 commit，实例并不会最终出现在 db 中。


```shell
>>> tag = session.query(Tag).first()
2016-12-30 13:23:19,565 INFO sqlalchemy.engine.base.Engine BEGIN (implicit)
2016-12-30 13:23:19,569 INFO sqlalchemy.engine.base.Engine INSERT INTO tag (id, name, atime) VALUES (%s, %s, %s)
2016-12-30 13:23:19,573 INFO sqlalchemy.engine.base.Engine (90, 'tag', datetime.datetime(2016, 12, 30, 13, 20, 53, 109607))
2016-12-30 13:23:19,580 INFO sqlalchemy.engine.base.Engine SELECT tag.id AS tag_id, tag.name AS tag_name, tag.atime AS tag_atime 
FROM tag 
 LIMIT %s
2016-12-30 13:23:19,586 INFO sqlalchemy.engine.base.Engine (1,)
>>> insp = inspect(tag)
>>> insp.transient
False
>>> insp.pending
False
>>> insp.persistent
True
```

**deleted**

persisted instance is deleted from session and flush

具有持久化状态的实例从 session 中删除，并且调用 flush，实例状态改变为 deleted

**detached**

具有持久化状态的 instance 不在 session 中
