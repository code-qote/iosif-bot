import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.declarative import declarative_base


class Association_playlists_songs(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'playlists_songs'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    playlist_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('playlists.id'))
    song_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('songs.id'))
    position = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    song = orm.relationship('Song', back_populates='playlists')
    playlist = orm.relationship('Playlist', back_populates='songs')

class Association_queues_songs(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'queues_songs'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    queue_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('queues.id'))
    song_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('songs.id'))
    position = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    song = orm.relationship('Song', back_populates='queues')
    queue = orm.relationship('Queue', back_populates='songs')    

class Server(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'servers'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    discord_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    discord_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    playlists = orm.relationship('Playlist')

class Playlist(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'playlists'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), nullable=False)
    songs = orm.relationship('Association_playlists_songs', back_populates='playlist')

class Queue(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'queues'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    server_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('servers.id'))
    songs = orm.relationship('Association_queues_songs', back_populates='queue')

class Song(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'songs'
    
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    request = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)
    playlists = orm.relationship('Association_playlists_songs', back_populates='song')
    queues = orm.relationship('Association_queues_songs', back_populates='song')

