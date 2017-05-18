# noqa
import random
from db import engine, DBSession
from model import Tag

from sqlalchemy import func


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


def delete():
    session = DBSession()
    session.query(Tag).filter(Tag.id == 999).delete()
    session.commit()


def order_by():
    session = DBSession()
    for i in session.query(Tag).order_by(Tag.id.desc()).limit(10):
        print i.id


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
        print i.id


def in_():
    session = DBSession()
    for i in session.query(Tag).filter(Tag.id.in_([1, 3, 4])).all():
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


if __name__ == '__main__':
    # label_order_by()
    count()
    # in_()
    # distinct()
    # select_columns()
    # group_by()
    # order_by()
    # limit_offset()
    # delete()
    # update()
    # insert()
