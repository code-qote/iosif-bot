import asyncio
import itertools
import random
import string
from random import shuffle
from time import sleep
from urllib import request

import aiohttp
import discord
import spotipy
from data.__all_models import Track_db
from data.db_session import create_session
from discord.ext import commands
from discord.ext.commands import bot
from discord.ext.commands.core import command
from requests import get
from requests.sessions import session
from sqlalchemy.sql.expression import func
from youtube import YTDLSource

default_message_reactions = ['⏹️', '⏸️', '⏮️', '⏭️', '👍', '👎', '❌']
pause_message_reactions = ['⏹️', '▶️', '⏮️', '⏭️', '👍', '👎', '❌']
default_radio_message_reactions = ['⏹️', '⏸️', '⏭️', '👍', '👎', '❌']
pause_radio_message_reactions = ['⏹️', '▶️', '⏭️', '👍', '👎', '❌']
INTRO_URL = ['https://youtu.be/91D2V8W8Sy0', 'https://youtu.be/-bEzhmi7vOg']


def get_tracks_from_db(server_id):
    server_id = str(server_id)
    session = create_session()
    tracks = session.query(Track_db).filter_by(server_id=server_id).all()
    # TODO: проверить shuffle
    if not tracks:
        tracks = session.query(Track_db).order_by(func.random().limit(5)).all()
    return tracks

class Artist:
    def __init__(self, info):
        self.id = info['id']
        self.uri = info['uri']
        self.name = info['name']

class Album:
    def __init__(self, info):
        self.id = info['id']
        self.uri = info['uri']
        self.name = info['name']
        self.release_date = info['release_date']
        self.total_tracks = info['total_tracks']

class Song:
    def __init__(self, is_intro=False):
        self.source = None
        self.ctx = None
        self.is_old = False
        self.message = None
        self.id = None
        self.uri = None
        self.album = None
        self.artist = None
        self.popularity = None
        self.name = None
        self.liked = False
        self.is_intro = is_intro
        self.from_radio = False
        self.keyword = None
        self.is_message_updating = False
    
    def check_like_with_uri(self, server_id):
        server_id = str(server_id)
        session = create_session()
        track = session.query(Track_db).filter_by(server_id=server_id, uri=self.uri).first()
        if track:
            self.liked = True
        else:
            self.liked = False
        session.close()
    
    # На случай, если испольнитель не считается таковым на YT
    async def _get_info_from_Deezer(self, keyword):
        new = ''
        for i in keyword:
            if i in string.printable or i == ' ':
                new += i
        keyword = new
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.deezer.com/search?q=' + keyword) as response:
                json = await response.json()
                data = json.get('data', None)
                if data:
                    data = data[0]
                    name = data['title']
                    artist = data['artist']['name']
                    return name, artist
        return None, None
    
    async def _get_info_from_YT(self, keyword, bot, ctx):
        self.ctx = ctx
        self.source = await YTDLSource.from_url(keyword, loop=bot.loop)
        if self.source:
            author = self.source.data.get('artist', '')
            track = self.source.data.get('track', '')
            track, author = await self._get_info_from_Deezer(self.source.title)
            self.liked = self.is_liked(self.source.title, track)
            if track and author and not self.name and not self.artist:
                r = RadioEngine()
                self._get_info_from_Spotify(track, author, r.sp)
            return True
        else:
            return None

    def _get_info_from_Spotify(self, name, artist, sp, track=None):
        if track is None:
            info = sp.search(q='artist:' + artist + ' track:' +
                                  name, type='track', limit=1)
            try:
                track = info['tracks']['items'][0]
            except IndexError:
                return
        album = Album(track['album'])
        artist_ = Artist(track['artists'][0])
        self.album = album
        self.artist = artist_
        self.id = track['id']
        self.uri = track['uri']
        self.name = track['name']
        self.popularity = track['popularity']
    
    # Обновление Embed
    async def refresh_message(self):
        embed = self.get_embed()
        await self.message.edit(embed=embed)

    def get_embed(self):
        colors = {True: discord.Color.red(), False: discord.Color.blurple()}
        if self.is_intro:
            embed = (discord.Embed(title='Iosif Radio', 
                                    color=discord.Color.red()).set_footer(text='Made with ❤️'))
            return embed
        if self.source:
            title, author, track, duration, url, thumbnail = self._get_info_from_source_data()
            self.liked = self.is_liked(title, track) or self.liked
            embed = (discord.Embed(title='Now playing:',
                                   description=title, color=colors[self.from_radio])
                     .add_field(name='Author', value=author)
                     .add_field(name='Duration', value=duration)
                     .add_field(name='URL', value=url)
                     .set_thumbnail(url=thumbnail)
                     .set_footer(text='Made with ❤️'))
            if self.liked:
                embed.add_field(name='Liked', value='🙂')
            else:
                embed.add_field(name='Liked', value='😐')
            return embed

    def _get_info_from_source_data(self):
        title = self.source.title
        author = self.source.data.get('artist', '')
        track = self.source.data.get('track', '')
        if not author:
            author = self.source.data['uploader']
        duration = self.convert_duration(self.source.data['duration'])
        url = self.source.data['webpage_url']
        thumbnail = self.source.data['thumbnails'][0]['url']
        return title, author, track, duration, url, thumbnail

    def is_liked(self, title, track):
        tracks = get_tracks_from_db(self.ctx.guild.id)
        for i in tracks:
            if i.name == title or i.name == track:
                return True
        return False

    def convert_duration(self, duration):
        h = duration // 3600
        duration %= 3600
        m = duration // 60
        duration %= 60
        s = duration
        return f'{int(h)}:{int(m)}:{int(s)}'

    def add_to_db(self, server_id):
        server_id = str(server_id)
        session = create_session()
        if not session.query(Track_db).filter_by(spotify_id=self.id).first():
            track_to_bd = Track_db(
                spotify_id=self.id,
                uri=self.uri,
                name=self.name,
                artist=self.artist.name,
                server_id=str(server_id)
            )
            session.add(track_to_bd)
            session.commit()
        session.close()
    
    def remove_from_db(self, server_id, uri):
        server_id = str(server_id)
        session = create_session()
        track = session.query(Track_db).filter_by(server_id=server_id, uri=uri).first()
        session.delete(track)
        session.commit()
        session.close()

    # обновление source для повторного запуска
    async def refresh(self, bot):
        self.source = await YTDLSource.from_url(self.source.title, loop=bot.loop)
        self.is_old = False

    async def update_message_reactions(self, reactions, from_radio=False):
        await self.message.clear_reactions()
        for reaction in reactions:
            if reaction == '👎':
                if self.liked:
                    await self.message.add_reaction(emoji=reaction)
            elif reaction == '👍':
                if not self.liked:
                    await self.message.add_reaction(emoji=reaction)
            else:
                await self.message.add_reaction(emoji=reaction)

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
    
class RadioEngine:
    client_id = '44897430b3ff40e1b8e5cebbf31b7989'
    client_secret = '97873e4eca264471b40d1f15de216a82'
    username = 'Iosif Radio'
    scope = "playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative"
    redirect_uri = 'https://iosif.herokuapp.com/'

    def __init__(self):
        client_credentials_manager = spotipy.SpotifyClientCredentials(client_id=self.client_id,
                                                                      client_secret=self.client_secret)

        sp = spotipy.Spotify(
            client_credentials_manager=client_credentials_manager)
        token = spotipy.util.prompt_for_user_token(
            self.username, self.scope, self.client_id, self.client_secret, self.redirect_uri)

        self.sp = spotipy.Spotify(auth=token)

    def get_recommendation(self, seed_tracks):
        tracks = []
        for track in seed_tracks:
            song = Song()
            song._get_info_from_Spotify(track.name, track.artist, self.sp)
            tracks.append(song)
        seed_tracks = [track.uri for track in tracks]

        # Существует ограничение в 5 seed треков в spotify, поэтому делим их по 5
        recommendations = [self.sp.recommendations(seed_tracks=seed_tracks[i:i+5], limit=5) 
                            for i in range(0, len(seed_tracks), 5)]

        recommendations_new = []
        for recs in recommendations:
            for track in recs['tracks']:
                song = Song()
                song._get_info_from_Spotify('', '', self.sp, track)
                recommendations_new.append(song)
        return recommendations_new

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

        self.audio_player = self.bot.loop.create_task(self.audio_player_task())
        asyncio.gather(self.audio_player)

    def __del__(self):
        self.audio_player.cancel()

    async def radio(self, ctx, first=True):
        await self.load_intro(ctx, first)
        await self.load_recommendations(ctx)

    async def load_intro(self, ctx, first=True):
        if (self.voice.is_playing() or self.voice.is_paused()) and first:
            self.songs.clear()
            if self.current:
                await self.current.message.clear_reactions()
            self.voice.stop()
        if first:
            intro = Song(True)
            intro.from_radio = True
            intro.keyword = random.choice(INTRO_URL)
            await self.songs.put(intro)

    async def load_recommendations(self, ctx: commands.Context):
        async with ctx.typing():
            await asyncio.sleep(3)
        tracks = get_tracks_from_db(ctx.guild.id)
        shuffle(tracks)
        self.radio_engine = RadioEngine()
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

            if self.radio_mode:
                message = self.current.message

            self.current = new

            if self.radio_mode and not self.current.is_intro:
                self.current.message = message

            if self.current.is_old:
                await self.current.refresh(self.bot)
            else:
                await self.current._get_info_from_YT(self.current.keyword, self.bot, self._ctx)
            
            while await self.current._get_info_from_YT(self.current.keyword, self.bot, self._ctx) is None:
                print('f')
                new = await self.songs.get()

                if self.radio_mode:
                    message = self.current.message

                self.current = new

                if self.radio_mode and not self.current.is_intro:
                    self.current.message = message

                if self.current.is_old:
                    await self.current.refresh(self.bot)
                else:
                    await self.current._get_info_from_YT(self.current.keyword, self.bot, self._ctx)

            self.current.source.volume = 0.5

            self.current.check_like_with_uri(self._ctx.guild.id)
            if self.voice:
                self.voice.play(self.current.source, after=self.play_next_song)
            self.current.is_old = True
            embed = self.current.get_embed()

            if not self.radio_mode or self.current.is_intro:
                self.current.message = await self.current.ctx.send(embed=embed)
            else:
                await self.current.message.edit(embed=embed)

            if not self.current.is_intro and not self.radio_mode:
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
