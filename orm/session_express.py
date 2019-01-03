# -*- coding: utf-8 -*-
# noqa

from db import engine, DBSession

import gevent

import random
import threading
import time
from model import Tag

from sqlalchemy import (
    func,
    or_,
    and_,
)
from sqlalchemy import inspect


def create_tables():
    Tag.__table__.create(engine)


def init_data():
    session = DBSession()
    for i in range(0, 1000):
        t = Tag()
        t.name = random.choice('abcdefgjoiuytreqzxcvbnml')
        t.group_id = random.choice([1, 2, 3, 4, 5])
        session.add(t)
    session.commit()


def insert():
    session = DBSession()
    t = Tag()
    t.name = random.choice('abcdefgjoiuytreqzxcvbnml')
    t.group_id = random.choice([1, 2, 3, 4, 5])
    session.add(t)
    session.commit()


def update():
    session = DBSession()
    t = session.query(Tag).filter(Tag.id == 1).first()
    t.name = 'c'
    session.commit()


def update2():
    session = DBSession()
    t = session.query(Tag).filter(Tag.id == 1).update({
        "name": "c"})
    t = session.query(Tag).filter(Tag.id == 2).update({Tag.name: "c"})
    session.commit()


#http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.delete
def delete():
    session = DBSession()
    session.query(Tag).filter(Tag.id == 999).delete()
    session.commit()


def order_by():
    session = DBSession()
    for i in session.query(Tag).limit(1):
        pass
        # print i.id

    # time.sleep(2)
    session.close()


def limit_offset():
    session = DBSession()
    for i in session.query(Tag).limit(10).offset(10):
        print i.id


def group_by():
    session = DBSession()
    for i in session.query(
            Tag.group_id, func.max(Tag.id).label('id')).group_by(Tag.group_id):
        print i.id


def select_columns():
    session = DBSession()
    for i in session.query(Tag).add_columns(Tag.id, Tag.name).all():
        print i.name


def distinct():
    session = DBSession()
    for i in session.query(func.distinct(Tag.group_id).label('gid')).all():
        print i.gid


def in_():
    session = DBSession()
    for i in session.query(Tag).filter(Tag.id.in_([1, 3, 4])).all():
        print i.id
    session.close()
    print i.id


def count():
    session = DBSession()
    print session.query(Tag).count()
    print session.query(func.count(func.distinct(Tag.group_id)).label('num')).first().num
    print session.query(func.count(func.distinct(Tag.group_id)).label('num')).first().num
    # Return the first element of the first result or None if no rows present. If multiple rows are returned, raises MultipleResultsFound.
    print session.query(func.count(func.distinct(Tag.group_id))).scalar()
    print session.query(Tag.id > 1).count()
    query = session.query(Tag).filter(Tag.id > 100)
    print query.count()


def label():
    session = DBSession()
    # Return the full SELECT statement represented by this Query, converted to a scalar subquery with a label of the given name.
    print session.query(Tag).filter(Tag.id == 10).label('tag')
    print session.query(Tag).filter(Tag.id == 10).statement


def label_order_by():
    session = DBSession()
    for i in session.query(
            Tag.group_id, func.max(Tag.id).label('id')).group_by(
                Tag.group_id).order_by('id'):
        print i.id


# http://docs.sqlalchemy.org/en/latest/orm/tutorial.html#common-filter-operators
def or_query():
    session = DBSession()
    for i in session.query(Tag).filter(or_(Tag.id == 10, Tag.id == 11)).all():
        print i.id


def print_insp_state(insp):
    print('======>')
    print('transient: %s ' % getattr(insp, 'transient', None))
    print('pending: %s ' % getattr(insp, 'pending', None))
    print('persistent: %s ' % getattr(insp, 'persistent', None))
    print('deleted: %s ' % getattr(insp, 'deleted', None))
    print('detached: %s ' % getattr(insp, 'detached', None))
    print('attrs id %s' % insp.attrs.id.loaded_value)
    print('attrs name %s' % insp.attrs.name.loaded_value)
    print('<======')


def insert_id_0():
    """
    调用 close session 会调用 expunge_all, session 移除 instance
    session.expire 会让 instance attr 失效，next access will load from dbs
    
    http://docs.sqlalchemy.org/en/latest/orm/internals.html#sqlalchemy.orm.state.AttributeState.loaded_value
    explain 0
    https://dev.mysql.com/doc/refman/5.7/en/sql-mode.html#sqlmode_no_auto_value_on_zero
    在 commit 发生之后，id attrs 变为 symbol('NO_VALUE')，再次取的时候会从数据库加载，但是根据这个主键已经找不到数据了
    """
    session = DBSession()
    t = Tag()
    t.id = 0
    t.name = random.choice('abcdefgjoiuytreqzxcvbnml')
    t.group_id = random.choice([1, 2, 3, 4, 5])
    insp = inspect(t)
    session.add(t)
    session.commit()
    print_insp_state(insp)
    print t.id


def with_thread_test_pool_recyle():
    thread_list = []
    for _ in range(5):
        t = threading.Thread(target=order_by)
        thread_list.append(t)

    for t in thread_list:
        t.start()

    for t in thread_list:
        t.join()


def test_pool_recyle():
    while 1:
        print('thread start')
        with_thread_test_pool_recyle()
        print('thread end')
        gevent.sleep(300)
        # print('one query start')
        # order_by()
        # order_by()
        # order_by()
        # order_by()
        # order_by()
        # order_by()
        # order_by()
        # print('one query end')
        # time.sleep(30)


if __name__ == '__main__':
    # label_order_by()
    # count()
    # in_()
    # distinct()
    # select_columns()
    # group_by()
    # order_by()
    # limit_offset()
    # delete()
    # update()
    # insert()
    # insert_id_0()
    # or_query()
    # order_by()
    test_pool_recyle()