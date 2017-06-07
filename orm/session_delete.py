# -*- coding: utf-8 -*-
# noqa
import random
import time
from db import engine, DBSession
from model import Tag

from sqlalchemy import (
    func,
    or_,
    and_,
)
from sqlalchemy import inspect


# http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.delete
def delete():
    session = DBSession()
    session.query(Tag).filter(Tag.id == 999).delete()
    session.commit()


def delete_bull():
    session = DBSession()
    session.query(Tag).filter(Tag.id.in_([1, 2, 3, 4, 5])).delete()
    session.commit()
    # sqlalchemy.exc.InvalidRequestError: Could not evaluate current criteria
    # in Python. Specify 'fetch' or False for the synchronize_session
    # parameter.


def delete_bull_with_false():
    session = DBSession()
    session.query(Tag).filter(Tag.id.in_([1, 2, 3, 4, 5])).delete(
        synchronize_session=False)
    session.commit()


def delete_bull_with_fetch():
    session = DBSession()
    session.query(Tag).filter(Tag.id.in_([1, 2, 3, 4, 5])).delete(
        synchronize_session='fetch')
    session.commit()


def delete_bull_with_evaluate():
    session = DBSession()
    session.query(Tag).filter(Tag.id.in_([99])).all()
    session.query(Tag).filter(Tag.id.in_([99])).delete()
    session.commit()
    # sqlalchemy.exc.InvalidRequestError: Could not evaluate current criteria
    # in Python. Specify 'fetch' or False for the synchronize_session
    # parameter.


if __name__ == '__main__':
    delete_bull_with_evaluate()
