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
from sqlalchemy.sql import select
from sqlalchemy.sql import text


def sql_in():
    session = DBSession()
    sql = text("select * from tag where id in :id")
    print session.execute(sql, {'id': [10, 11, 12]}).fetchall()
    print session.execute(sql, {'id': [-1, -2, -3]}).fetchall()
    print session.execute(sql, {'id': [-1]}).first()
    sql = text("select count(*) from tag where id in :id")
    print session.execute(sql, {'id': [-1]}).first()
    print session.execute(sql, {'id': [-1]}).scalar()


if __name__ == '__main__':
    sql_in()
