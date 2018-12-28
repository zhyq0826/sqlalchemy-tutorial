from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# engine = create_engine('mysql+pymysql://root:@localhost/sqlalchemy_lab?charset=utf8', encoding='utf8', echo=True)
engine = create_engine(
    'mysql+pymysql://root:@localhost/blog?charset=utf8',
    encoding='utf8',
    echo=False,
    pool_size=2,
    pool_recycle=10,
)
DBSession = sessionmaker(bind=engine)




