import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.declarative import declarative_base


class Track_db(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'tracks'
    
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    spotify_id = sqlalchemy.Column(
        sqlalchemy.String(length=100), nullable=False)
    uri = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)
    artist = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)
    server_id = sqlalchemy.Column(sqlalchemy.String, nullable=False)

