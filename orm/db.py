from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql+pymysql://root:@localhost/sqlalchemy_lab?charset=utf8', encoding='utf8', echo=True)
DBSession = sessionmaker(bind=engine)
