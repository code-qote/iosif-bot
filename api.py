from requests import get
from db_requesters import *
from consts import API_URL_SERVER, API_URL_SONG

def add_server(server_id):
    requester = ServerRequester()
    return requester.add(server_id)

def add_song(request):
    requester = SongRequester()
    requester.add(request)

def add_song_to_queue(request, server_id):
    requester = QueueSongRequester()
    requester.connect_song_queue(request, server_id)

def get_queue(server_id):
    requester = QueueRequester()
    return requester.get_by_server_id(server_id)

def songs_list_from_queue(server_id):
    queue = get_queue(server_id)
    print(queue)
    if queue['exist']:
        requester = QueueSongRequester()
        return requester.get_songs_list(server_id)
    return False

def clear_queue(server_id):
    requester = QueueSongRequester()
    requester.remove_songs_by_server_id(server_id)

def get_song_from_queue(server_id, position):
    requester = SongRequester()
    song = requester.get_from_queue(server_id, position)
    if song['success']:
        return song['request']
    return False
