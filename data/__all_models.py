import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import sqlite, postgresql

def create_tsvector(*args):
    exp = args[0]
    for e in args[1:]:
        exp += ' ' + e
    return sqlalchemy.func.to_tsvector('english', exp)

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


class Default_track_db(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'default_tracks'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)
    artist = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)

class Holiday(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'holiday'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)

class Playlist_db(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'playlists'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    uri = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    to_search = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    __ts_vector__ = create_tsvector(
        sqlalchemy.cast(sqlalchemy.func.coalesce(to_search, ''), postgresql.TEXT)
    )

    __table_args__ = tuple([(
        sqlalchemy.Index(
            'idx_person_fts',
            __ts_vector__,
            postgresql_using='gin'
        )
    )])
