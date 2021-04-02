import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
import os

SqlAlchemyBase = dec.declarative_base()

__factory = None

def global_init(db_file=''):
    global __factory

    if __factory:
        return

    if 'DATABASE_URL' in os.environ:
       conn_str = os.environ['DATABASE_URL']  # сработает на Heroku
    else:
       conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    engine = sa.create_engine(conn_str, echo=False, pool_size=100)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()