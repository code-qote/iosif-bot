from random import shuffle
from time import sleep
from urllib import request
import discord
from discord.ext import commands
import asyncio
import itertools

from requests.sessions import session
from youtube import YTDLSource
from discord.ext.commands import bot
from discord.ext.commands.core import command
from data.db_session import create_session
from data.__all_models import Track_db
import spotipy


default_message_reactions = ['⏹️', '⏸️', '⏮️', '⏭️']
pause_message_reactions = ['⏹️', '▶️', '⏮️', '⏭️']
default_radio_message_reactions = ['⏹️', '⏸️', '⏭️', '👍']
pause_radion_message_reactions = ['⏹️', '▶️', '⏭️', '👍']
INTRO_URL = 'https://youtu.be/91D2V8W8Sy0'



def get_tracks_from_db(server_id):
    session = create_session()
    tracks = session.query(Track_db).filter_by(server_id=server_id).all()
    if not tracks:
        tracks = session.query(Track_db).limit(5).all()
    return tracks

class Artist:
    def __init__(self, info):
        self.id = info['id']
        self.uri = info['uri']
        self.name = info['name']

    def __str__(self):
        return str({'id': self.id, 'uri': self.uri, 'name': self.name})

class Album:
    def __init__(self, info):
        self.id = info['id']
        self.uri = info['uri']
        self.name = info['name']
        self.image_url = info['images'][0]['url']
        self.release_date = info['release_date']
        self.total_tracks = info['total_tracks']

    def __str__(self):
        return str({'id': self.id, 'uri': self.uri, 'name': self.name, 'image_url': self.image_url,
                    'release_date': self.release_date, 'total_tracks': self.total_tracks})

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
    
    async def _get_info_from_YT(self, keyword, bot, ctx):
        self.ctx = ctx
        self.source = await YTDLSource.from_url(keyword, loop=bot.loop)
        if self.source:
            try:
                author = self.source.data['artist']
            except KeyError:
                author = self.source.data['uploader']
            try:
                track = self.source.data['track']
            except KeyError:
                track = ''
            tracks = get_tracks_from_db(self.ctx.guild.id)
            for i in tracks:
                if i.name == self.source.title or i.name == track:
                    self.liked = True
            if track and author and not self.name and not self.artist:
                try:
                    self._get_info_from_Spotify(track, author)
                except Exception:
                    pass
            return True
        else:
            return None

    def _get_info_from_Spotify(self, name, artist, sp, track=None):
        if not track:
            info = sp.search(q='artist:' + artist + ' track:' +
                                  name, type='track', limit=1)
            track = info['tracks']['items'][0]
        album = Album(track['album'])
        artist_ = Artist(track['artists'][0])
        self.album = album
        self.artist = artist_
        self.id = track['id']
        self.uri = track['uri']
        self.name = track['name']
        self.popularity = track['popularity']
    
    async def refresh_message(self):
        embed = self.get_embed(True)
        await self.message.edit(embed=embed)

    def get_embed(self, radio_mode=False):
        colors = {True: discord.Color.red(), False: discord.Color.blurple()}
        if self.is_intro:
            embed = (discord.Embed(title='Iosif Radio', 
                                    color=discord.Color.red()).set_footer(text='Made with ❤️'))
            return embed
        if self.source:
            title = self.source.title
            author = self.source.data.get('artist', '')
            track = self.source.data.get('track', '')
            if not author:
                author = self.source.data['uploader']
            duration = self.convert_duration(self.source.data['duration'])
            url = self.source.data['webpage_url']
            thumbnail = self.source.data['thumbnails'][0]['url']
            tracks = get_tracks_from_db(self.ctx.guild.id)
            for i in tracks:
                if i.name == title or i.name == track:
                    self.liked = True
            embed = (discord.Embed(title='Now playing:',
                                   description=title, color=colors[radio_mode])
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

    def convert_duration(self, duration):
        h = duration // 3600
        duration %= 3600
        m = duration // 60
        duration %= 60
        s = duration
        return f'{int(h)}:{int(m)}:{int(s)}'

    def add_to_db(self, server_id):
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
        session = create_session()
        track = session.query(Track_db).filter_by(server_id=server_id, uri=uri).first()
        session.delete(track)
        session.commit()
        session.close()

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
        recommendations = []
        for i in range(0, len(seed_tracks), 5):
            rec = self.sp.recommendations(seed_tracks=seed_tracks[i:i+5], limit=5)
            recommendations.append(rec)
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
            await self.current.message.clear_reactions()
            self.voice.stop()
        if first:
            intro = Song(True)
            await intro._get_info_from_YT(INTRO_URL, self.bot, ctx)
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
            e = await track._get_info_from_YT(track.name + ' ' + track.artist.name, self.bot, ctx)
            if e:
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

            self.current.source.volume = 0.5
            if self.current.is_old:
                await self.current.refresh(self.bot)
            self.voice.play(self.current.source, after=self.play_next_song)

            self.current.is_old = True
            embed = self.current.get_embed(self.radio_mode)
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
            self.songs.clear()
            for i in range(ind, len(self.songs.list_to_show)):
                await self.songs.put(self.songs.list_to_show[i])
            self.voice.stop()

    async def back(self):
        ind = self.songs.list_to_show.index(self.current) - 1
        if ind >= 0:
            self.songs.clear()
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
