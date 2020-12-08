from requests import get
from db_requesters import *
from consts import API_URL_SERVER, API_URL_SONG

def add_server(server_id):
    requester = ServerRequester()
    return requester.add(server_id)

def add_song(request):
    requester = SongRequester()
    requester.add(request)

def add_playlist(user_id, name):
    requester = PlaylistRequester()
    return requester.add(user_id, name)

def playlist_list(user_id):
    requester = UserRequester()
    user_id = requester.get_by_discord_id(user_id)['id']
    requester = PlaylistRequester()
    return requester.get_by_user_id(user_id)

def add_user(discord_id):
    requester = UserRequester()
    requester.add(discord_id)

def add_song_to_queue(request, server_id):
    requester = QueueSongRequester()
    requester.connect_song_queue(request, server_id)

def add_song_to_playlist(request, playlist_id):
    requester = PlaylistSongRequester()
    requester.connect_playlist_queue(request, playlist_id)

def get_queue(server_id):
    requester = QueueRequester()
    return requester.get_by_server_id(server_id)

def get_user(user_id):
    requester = UserRequester()
    return requester.get_by_discord_id(user_id)

def get_playlist_by_user_id_and_name(user_id, name):
    requester = UserRequester()
    user_id = requester.get_by_discord_id(user_id)['id']
    requester = PlaylistRequester()
    return requester.get_by_user_id_and_name(user_id, name)

def songs_list_from_queue(server_id):
    queue = get_queue(server_id)
    if queue['exist']:
        requester = QueueSongRequester()
        return requester.get_songs_list(server_id)
    return False

def songs_list_from_playlist(playlist_id):
    requester = PlaylistSongRequester()
    return requester.get_songs_list(playlist_id)

def clear_queue(server_id):
    requester = QueueSongRequester()
    requester.remove_songs_by_server_id(server_id)

def clear_playlist(playlist_id):
    requester = PlaylistSongRequester()
    requester.remove_songs_by_playlist_id(playlist_id)

def remove_song_from_playlist(playlist_id, position):
    requester = PlaylistSongRequester()
    return requester.remove_song_by_position(playlist_id, position)

def get_song_from_queue(server_id, position):
    requester = SongRequester()
    song = requester.get_from_queue(server_id, position)
    if song['success']:
        return song['request']
    return False

def get_song_from_playlist(playlist):
    requester = SongRequester()
    song = requester.get_from_playlist(playlist['id'], playlist['position'])
    if song['success']:
        return song['request']
    return False
