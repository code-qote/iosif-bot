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
        discord_id = int(server.discord_id)
        if not server:
            session.close()
            return {'exist': False}
        session.close()
        return {'exist': True, 'discord_id': discord_id}
    
    def get_by_discord_id(self, discord_id):
        session = create_session()
        discord_id = str(discord_id)
        server = session.query(Server).filter_by(discord_id=discord_id).first()
        if not server:
            session.close()
            return {'exist': False}
        server_id = server.id
        session.close()
        return {'exist': True, 'id': server_id}
    
    def add(self, discord_id):
        session = create_session()
        discord_id = str(discord_id)
        if not self.get_by_discord_id(discord_id)['exist']:
            server = Server(discord_id=discord_id)
            session.add(server)
            session.commit()
            session.close()
            requester = QueueRequester()
            requester.add(discord_id)      
            return {'success': True}
        return {'success': False}

class PlaylistRequester:
    def get_by_user_id_and_name(self, user_id, name):
        session = create_session()
        playlist = session.query(Playlist).filter_by(user_id=user_id, name=name).first()
        session.close()
        if not playlist:
            session.close()
            return {'exist': False}
        playlist_id = playlist.id
        session.close()
        return {'exist': True, 'id': playlist_id}
    
    def get_by_user_id(self, user_id):
        session = create_session()
        playlists = session.query(Playlist).filter_by(user_id=user_id).all()
        session.close()
        if not playlists:
            session.close()
            return {'exist': False}
        playlists = [playlist.name for playlist in playlists]
        session.close()
        return {'exist': True, 'playlists': playlists}

    def add(self, user_id, name):
        session = create_session()
        if not self.get_by_user_id_and_name(user_id, name)['exist']:
            requester = UserRequester()
            user_id = requester.get_by_discord_id(user_id)['id']
            playlist = Playlist(name=name, user_id=user_id)
            session.add(playlist)
            session.commit()
            session.close()
            return {'success': True}
        return {'success': False}

class QueueRequester:
    def get_by_server_id(self, server_id):
        session = create_session()
        server_id = discord_id_to_id(server_id)
        queue = session.query(Queue).filter_by(server_id=server_id).first()
        session.close()
        if not queue:
            session.close()
            return {'exist': False}
        queue_id = queue.id
        session.close()
        return {'exist': True, 'id': queue_id}

    def add(self, server_id):
        session = create_session()
        if not self.get_by_server_id(server_id)['exist']:
            queue = Queue(server_id=discord_id_to_id(server_id))
            session.add(queue)
            session.commit()
            session.close()
            return {'success': True}
        return {'success': False}

class SongRequester:
    def get_from_queue(self, server_id, position):
        session = create_session()
        server_id = discord_id_to_id(server_id)
        queue = session.query(Queue).filter_by(server_id=server_id).first()
        association = session.query(Association_queues_songs).filter_by(queue_id=queue.id, position=position).first()
        if not association:
            session.close()
            return {'success': False}
        song = association.song
        song_request = song.request
        session.close()
        return {'success': True, 'request' : song_request}
    
    def get_from_playlist(self, playlist_id, position):
        session = create_session()
        association = session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id, position=position).first()
        if not association:
            session.close()
            return {'success': False}
        song = association.song
        song_request = song.request
        session.close()
        return {'success': True, 'request' : song_request}

    def get_by_request(self, request):
        session = create_session()
        song = session.query(Song).filter_by(request=request).first()
        if not song:
            session.close()
            return {'exist': False}
        song_id = song.id
        session.close()
        return {'exist': True, 'id': song_id}
    
    def add(self, request):
        session = create_session()
        if not self.get_by_request(request)['exist']:
            song = Song(request=request)
            session.add(song)
            session.commit()
            session.close()
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
            session.close()
            return {'success': True}
        return {'success': False}
    
    def get_songs_list(self, server_id):
        session = create_session()
        server_id = discord_id_to_id(server_id)
        result = [{'request': item.song.request, 'position': item.position} for item in session.query(Association_queues_songs).filter_by(queue_id=server_id).all()]
        session.close()
        return result
    
    def remove_songs_by_server_id(self, server_id):
        session = create_session()
        server_id = discord_id_to_id(server_id)
        items = session.query(Association_queues_songs).filter_by(queue_id=server_id).all()
        for item in items:
            session.delete(item)
        session.commit()
        session.close()

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
            session.close()
            return {'success': True}
        session.close()
        return {'success': False}
    
    def get_songs_list(self, playlist_id):
        session = create_session()
        items = session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id).all()
        result = [{'request': item.song.request, 'position': item.position} for item in items]
        session.close()
        return result
    
    def remove_songs_by_playlist_id(self, playlist_id):
        session = create_session()
        items = session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id).all()
        for item in items:
            session.delete(item)
        session.commit()
        session.close()
    
    def remove_song_by_position(self, playlist_id, position):
        session = create_session()
        item = session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id, position=position).first()
        if item:
            items = list(filter(lambda x: x.position > position, session.query(Association_playlists_songs).filter_by(playlist_id=playlist_id).all()))
            session.delete(item)
            for item in items:
                item.position += 1
            session.commit()
            session.close()
            return {'success': True}
        session.close()
        return {'success': False}

class UserRequester:
    def get_by_discord_id(self, discord_id):
        session = create_session()
        discord_id = str(discord_id)
        user = session.query(User).filter_by(discord_id=discord_id).first()
        if not user:
            session.close()
            return {'exist': False}
        user_id = user.id
        session.close()
        return {'exist': True, 'id': user_id}
    
    def add(self, discord_id):
        session = create_session()
        discord_id = str(discord_id)
        if not self.get_by_discord_id(discord_id)['exist']:
            user = User(discord_id=discord_id)
            session.add(user)
            session.commit()
            session.close()
            return {'success': True}
        session.close()
        return {'success': False}
    
