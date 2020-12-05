from api import *

def play_next(guild):
    guild = int(guild)
    current_song_id = get_current_song(guild)
    song = get_song(guild, current_song_id + 1)
    if song['exist']:
        change_current_song_id(guild, current_song_id + 1)
    else:
        change_current_song_id(guild, 1)

play_next('1')