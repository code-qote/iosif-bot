import asyncio
import itertools
from random import choice, shuffle
import sys
import path
import datetime

folder = path.Path(__file__).abspath()
sys.path.append(folder.parent.parent.parent)
sys.path.append(folder.parent)

from data.__all_models import Default_track_db, Playlist_db
from data.db_session import create_session
from discord.ext import commands

from list_message import ListMessage
from song import Playlist, Song, SpotifyEngine, get_tracks_from_db

default_message_reactions = ['⏹️', '⏸️', '⏮️', '⏭️', '👍', '👎', '❌']
pause_message_reactions = ['⏹️', '▶️', '⏮️', '⏭️', '👍', '👎', '❌']
default_radio_message_reactions = ['⏹️', '⏸️', '⏭️', '👍', '👎', '❌']
pause_radio_message_reactions = ['⏹️', '▶️', '⏭️', '👍', '👎', '❌']
default_playlist_message_reactions = [
    '⏹️', '⏸️', '⏮️', '⏭️', '👍', '👎', '📻', '❌']
pause_playlist_message_reactions = ['⏹️', '▶️', '⏮️', '⏭️', '👍', '👎', '📻', '❌']
INTRO_URL = ['https://youtu.be/91D2V8W8Sy0',
             'https://youtu.be/-bEzhmi7vOg', 'https://youtu.be/Qt2U3Bb4_EU']


def get_default_tracks_from_db():
    session = create_session()
    tracks = session.query(Default_track_db).all()
    session.close()
    return tracks


def get_playlists_from_db(name):
    session = create_session()
    if name is None:
        playlists = session.query(Playlist_db).all()
    else:
        playlists = session.query(Playlist_db).filter(Playlist_db.__ts_vector__.match(
            name.replace(' ', '%').lower(), postgresql_regconfig='english')).all()
    session.close()
    return playlists


class SongQueue(asyncio.Queue):

    list_to_show = []

    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()
        self.list_to_show.clear()

    def remove(self, i):
        del self._queue[self._queue.index(self.list_to_show[i])]
        del self.list_to_show[i]

async def start(state):
    state.audio_player = state.bot.loop.create_task(state.audio_player_task())
    await asyncio.gather(state.audio_player)

class VoiceChannel:

    def __init__(self, bot: commands.Bot, ctx):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.radio_engine = None
        self.radio_mode = False
        self.playlist_mode = False
        self.playlist = None
        self.playlists_searching_message = None
        self.songs_list_message = None


    def __del__(self):
        self.audio_player.cancel()

    async def play_playlist(self, number):
        self.songs.clear()
        r = SpotifyEngine()
        playlist = Playlist(r.sp.playlist(
            self.playlists_searching_message.splitted_items[self.playlists_searching_message.current_page][number].uri))
        for song in playlist.songs:
            await self.songs.put(song)
            self.songs.list_to_show.append(song)
        if self.current:
            await self.current.message.clear_reactions()
        await self.playlists_searching_message.message.clear_reactions()
        self.voice.stop()
        self.playlist_mode = True

    async def send_songs_list(self, songs):
        if self.songs_list_message:
            await self.songs_list_message.message.clear_reactions()
        self.songs_list_message = ListMessage(songs, 'songs_list')
        self.songs_list_message.message = await self._ctx.send(embed=self.songs_list_message.get_embed())
        await self.songs_list_message.refresh_page()

    async def search_playlists(self, name=None):
        playlists = get_playlists_from_db(name)
        if self.playlists_searching_message:
            await self.playlists_searching_message.message.clear_reactions()
        self.playlists_searching_message = ListMessage(playlists, 'playlist')
        self.playlists_searching_message.message = await self._ctx.send(embed=self.playlists_searching_message.get_embed())
        await self.playlists_searching_message.refresh_page()

    async def radio(self, ctx, first=True, from_playlist=False):
        if from_playlist:
            tracks = self.current.playlist.songs_uri
            self.playlist_mode = False
        else:
            tracks = []
        await self.load_intro(ctx, first)
        await self.load_recommendations(ctx, tracks)

    async def load_intro(self, ctx, first=True):
        if (self.voice.is_playing() or self.voice.is_paused()) and first:
            self.songs.clear()
            if self.current:
                await self.current.message.clear_reactions()
            self.voice.stop()
        if first:
            intro = Song(True)
            intro.from_radio = True
            intro.keyword = choice(INTRO_URL)
            await self.songs.put(intro)

    async def load_recommendations(self, ctx: commands.Context, tracks):
        async with ctx.typing():
            await asyncio.sleep(1)

        if not tracks:
            tracks = get_tracks_from_db(ctx.guild.id)
            if not tracks:
                tracks = get_default_tracks_from_db()

        shuffle(tracks) # для более однородных рекомендаций

        self.radio_engine = SpotifyEngine()
        recommendations = self.radio_engine.get_recommendation(
            tracks)
        recommendations = recommendations[:-1]
        for track in recommendations:
            track.from_radio = True
            track.keyword = track.name + ' ' + track.artist.name
            await self.songs.put(track)
            self.radio_mode = True

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if self.current and not self.current.is_intro:
                await self.current.message.clear_reactions()

            new = await self.songs.get()

            # достаем новую песню до тех пор, пока не запустится

            crashed = True

            while crashed:
                try:
                    if self.radio_mode:
                        message = self.current.message

                    self.current = new

                    if self.radio_mode and not self.current.is_intro:
                        self.current.message = message

                    if self.current.is_old:
                        await self.current.refresh(self.bot)
                    else:
                        await self.current._get_info_from_YT(self.current.keyword, self.bot, self._ctx)
                except Exception:
                    if self.songs or self.current.source.data['age_limit'] != 0:
                        new = await self.songs.get()
                    else:
                        crashed = False
                else:
                    if self.current.source and self.current.source.data['age_limit'] == 0:
                        crashed = False

            # while await self.current._get_info_from_YT(self.current.keyword, self.bot, self._ctx) is None:
            #     print('f')
            #     new = await self.songs.get()

            #     if self.radio_mode:
            #         message = self.current.message

            #     self.current = new

            #     if self.radio_mode and not self.current.is_intro:
            #         self.current.message = message

            #     if self.current.is_old:
            #         await self.current.refresh(self.bot)
            #     else:
            #         await self.current._get_info_from_YT(self.current.keyword, self.bot, self._ctx)

            if self.current and self.current.source:
                self.current.source.volume = 0.5

                self.current.check_like_with_uri(self._ctx.guild.id)
                if self.voice:
                    self.voice.play(self.current.source, after=self.play_next_song)
                    ################################
                    user = await self.bot.fetch_user(315109612674220035)
                    if self.current.name:
                        await user.send(f'{self.current.name} {str(datetime.datetime.now())} {self.current.source.data["age_limit"]}')
                    # print(self.current.name, datetime.datetime.now())
                    ################################
                self.current.is_old = True
                embed = self.current.get_embed()

                if not self.radio_mode or self.current.is_intro:
                    self.current.message = await self.current.ctx.send(embed=embed)
                else:
                    await self.current.message.edit(embed=embed)

                if self.playlist_mode:
                    await self.current.update_message_reactions(default_playlist_message_reactions)

                if not self.current.is_intro and not self.radio_mode and not self.playlist_mode:
                    await self.current.update_message_reactions(default_message_reactions)

                elif self.radio_mode and not self.current.is_intro:
                    await self.current.update_message_reactions(default_radio_message_reactions)

            if self.radio_mode and not self.songs:
                await self.radio(self._ctx, first=False)

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            print(error)
        else:
            self.next.set()

    def skip(self):
        self.voice.stop()

    async def jump(self, ind):
        if 0 <= ind < len(self.songs.list_to_show):
            self.songs._queue.clear()
            for i in range(ind, len(self.songs.list_to_show)):
                await self.songs.put(self.songs.list_to_show[i])
            self.voice.stop()

    async def back(self):
        ind = self.songs.list_to_show.index(self.current) - 1
        if ind >= 0:
            self.songs._queue.clear()
            for i in range(ind, len(self.songs.list_to_show)):
                await self.songs.put(self.songs.list_to_show[i])
            self.voice.stop()

    @property
    def is_playing(self):
        return self.voice and self.current

    async def leave(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None
