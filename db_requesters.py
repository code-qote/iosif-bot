from data.__all_models import *
from data.db_session import create_session
from sqlalchemy import func


def discord_id_to_id(server_id):
    requester = ServerRequester()
    return requester.get_by_discord_id(server_id)['id']

class ServerRequester:
    def get_by_id(self, id):
        session = create_session()
        server = session.query(Server).get(id)
        if not server:
            return {'exist': False}
        return {'exist': True, 'discord_id': int(server.discord_id)}
    
    def get_by_discord_id(self, discord_id):
        session = create_session()
        discord_id = str(discord_id)
        server = session.query(Server).filter_by(discord_id=discord_id).first()
        if not server:
            return {'exist': False}
        return {'exist': True, 'id': server.id}
    
    def add(self, discord_id):
        session = create_session()
        discord_id = str(discord_id)
        if not self.get_by_discord_id(discord_id)['exist']:
            server = Server(discord_id=discord_id)
            session.add(server)
            session.commit()
            requester = QueueRequester()
            requester.add(discord_id)
            return {'success': True}
        return {'success': False}

class PlaylistRequester:
    def get_by_user_id_and_name(self, user_id, name):
        session = create_session()
        playlist = session.query(Playlist).filter_by(user_id=user_id, name=name).first()
        if not playlist:
            return {'exist': False}
        return {'exist': True, 'id': playlist.id}
    
    def get_by_user_id(self, user_id):
        session = create_session()
        playlists = session.query(Playlist).filter_by(user_id=user_id).all()
        if not playlists:
            return {'exist': False}
        return {'exist': True, 'playlists': [playlist.name for playlist in playlists]}

    def add(self, user_id, name):
        session = create_session()
        if not self.get_by_user_id_and_name(user_id, name)['exist']:
            requester = UserRequester()
            user_id = requester.get_by_discord_id(user_id)['id']
            playlist = Playlist(name=name, user_id=user_id)
            session.add(playlist)
            session.commit()
            return {'success': True}
        return {'success': False}

class QueueRequester:
    def get_by_server_id(self, server_id):
        session = create_session()
        server_id = discord_id_to_id(server_id)
        queue = session.query(Queue).filter_by(server_id=server_id).first()
        if not queue:
            return {'exist': False}
        return {'exist': True, 'id': queue.id}

    def add(self, server_id):
        session = create_session()
        if not self.get_by_server_id(server_id)['exist']:
            queue = Queue(server_id=discord_id_to_id(server_id))
            session.add(queue)
            session.commit()
            return {'success': True}
        return {'success': False}

class SongRequester:
    def get_from_queue(self, server_id, position):
        session = create_session()
        server_id = discord_id_to_id(server_id)
        queue = session.query(Queue).filter_by(server_id=server_id).first()
        association = session.query(Association_queues_songs).filter_by(queue_id=queue.id, position=position).first()
        if not association:
            return {'success': False}
        song = association.song
        return {'success': True, 'request' : song.request}
    
    def get_from_playlist(self, playlist_id, position):
        session = create_session()
        association = session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id, position=position).first()
        if not association:
            return {'success': False}
        song = association.song
        return {'success': True, 'request' : song.request}

    def get_by_request(self, request):
        session = create_session()
        song = session.query(Song).filter_by(request=request).first()
        if not song:
            return {'exist': False}
        return {'exist': True, 'id': song.id}
    
    def add(self, request):
        session = create_session()
        if not self.get_by_request(request)['exist']:
            song = Song(request=request)
            session.add(song)
            session.commit()
            return {'success': True}
        return {'success': False}

class QueueSongRequester:
    def connect_song_queue(self, request, server_id):
        session = create_session()
        server_id = str(server_id)
        requester = SongRequester()
        song = requester.get_by_request(request)
        requester = QueueRequester()
        queue = requester.get_by_server_id(server_id)
        server_id = discord_id_to_id(server_id)
        items = session.query(Association_queues_songs).filter_by(queue_id=server_id).all()
        if items:
            position = max(items, key=lambda x: x.position).position + 1
        else:
            position = 1
        if song['exist'] and queue['exist']:
            associtiation = Association_queues_songs(
                queue_id=queue['id'],
                song_id=song['id'],
                position=position,
                queue=session.query(Queue).get(queue['id']),
                song=session.query(Song).get(song['id'])
            )
            session.add(associtiation)
            session.commit()
            return {'success': True}
        return {'success': False}
    
    def get_songs_list(self, server_id):
        session = create_session()
        server_id = discord_id_to_id(server_id)
        return [{'request': item.song.request, 'position': item.position} for item in session.query(Association_queues_songs).filter_by(queue_id=server_id).all()]
    
    def remove_songs_by_server_id(self, server_id):
        session = create_session()
        server_id = discord_id_to_id(server_id)
        items = session.query(Association_queues_songs).filter_by(queue_id=server_id).all()
        for item in items:
            session.delete(item)
        session.commit()

class PlaylistSongRequester:
    def connect_playlist_queue(self, request, playlist_id):
        session = create_session()
        requester = SongRequester()
        song = requester.get_by_request(request)
        items = session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id).all()
        if items:
            position = max(items, key=lambda x: x.position).position + 1
        else:
            position = 1
        if song['exist']:
            association = Association_playlists_songs(
                playlist_id=playlist_id,
                song_id=song['id'],
                position=position,
                playlist=session.query(Playlist).get(playlist_id),
                song=session.query(Song).get(song['id'])
            )
            session.add(association)
            session.commit()
            return {'success': True}
        return {'success': False}
    
    def get_songs_list(self, playlist_id):
        session = create_session()
        return [{'request': item.song.request, 'position': item.position} for item in session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id).all()]
    
    def remove_songs_by_playlist_id(self, playlist_id):
        session = create_session()
        items = session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id).all()
        for item in items:
            session.delete(item)
        session.commit()
    
    def remove_song_by_position(self, playlist_id, position):
        session = create_session()
        item = session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id, position=position).first()
        if item:
            items = list(filter(lambda x: x.position > position, session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id).all()))
            session.delete(item)
            for item in items:
                item.position += 1
            session.commit()
            return {'success': True}
        return {'success': False}

class UserRequester:
    def get_by_discord_id(self, discord_id):
        session = create_session()
        discord_id = str(discord_id)
        user = session.query(User).filter_by(discord_id=discord_id).first()
        if not user:
            return {'exist': False}
        return {'exist': True, 'id': user.id}
    
    def add(self, discord_id):
        session = create_session()
        discord_id = str(discord_id)
        if not self.get_by_discord_id(discord_id)['exist']:
            user = User(discord_id=discord_id)
            session.add(user)
            session.commit()
            return {'success': True}
        return {'success': False}
    
