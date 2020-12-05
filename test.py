from data import db_session
from flask import Flask
from flask_restful import Resource, Api
from resources.servers_resources import ServerResource
from resources.songs_resources import SongResource


app = Flask(__name__)
api = Api(app)

if __name__ == '__main__':
    db_session.global_init('data/db.db')
    api.add_resource(ServerResource, '/api/server')
    api.add_resource(SongResource, '/api/song')
    app.run()