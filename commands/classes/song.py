import itertools
import string
import sys

import aiohttp
import discord
import path
import spotipy
from data.__all_models import Track_db
from data.db_session import create_session
from discord.ext import commands
from youtube import YTDLSource

folder = path.Path(__file__).abspath()
sys.path.append(folder.parent.parent.parent)


class SpotifyEngine:
    """Engine that provides Spotify API"""

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

    def get_recommendation(self, seed_tracks: list) -> list:
        """Function that returns a list of recommendations

        Args:
            seed_tracks (list): base tracks

        Returns:
            list: recommendations
        """
        tracks = []
        for track in seed_tracks:
            song = Song()
            if type(track) is dict:
                song._get_info_from_Spotify('', '', self.sp, track=track)
            else:
                song._get_info_from_Spotify(track.name, track.artist, self.sp)
            tracks.append(song)
        seed_tracks = [track.uri for track in tracks if track.uri]

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


def get_tracks_from_db(server_id: int) -> list:
    """Function that returns a list of tracks from the database

    Args:
        server_id (int): guild id

    Returns:
        list: tracks from database
    """
    server_id = str(server_id)
    session = create_session()
    tracks = session.query(Track_db).filter_by(server_id=server_id).all()
    session.close()
    return tracks


class Playlist:
    """Playlist class"""

    def __init__(self, json, tracks_db=None):
        if not tracks_db:
            self.name = json['name']
            r = SpotifyEngine()
            self.songs = []
            self.songs_uri = []
            for track in json['tracks']['items']:
                song = Song()
                song._get_info_from_Spotify('', '', r.sp, track=track['track'])
                song.playlist = self
                song.from_playlist = True
                self.songs.append(song)
                self.songs_uri.append(track['track'])
        else:
            r = SpotifyEngine()
            self.songs = []
            self.songs_uri = []
            for track in tracks_db:
                song = Song()
                song._get_info_from_Spotify('', '', r.sp, track=track['track'])
                song.playlist = self
                song.from_playlist = True
                self.songs.append(song)
                self.songs_uri.append(song.uri)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self.songs, item.start, item.stop, item.step))
        else:
            return self.songs[item]


class Artist:
    """Artist class"""

    def __init__(self, info):
        self.id = info['id']
        self.uri = info['uri']
        self.name = info['name']


class Album:
    """Album class"""

    def __init__(self, info):
        self.id = info['id']
        self.uri = info['uri']
        self.name = info['name']
        self.release_date = info['release_date']
        self.total_tracks = info.get('total_tracks', 1)


class Song:
    """Song class"""

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
        self.playlist = None
        self.from_playlist = False
        self.is_updating_reactions = False

    def check_like_with_uri(self, server_id: int) -> None:
        """Function that sets self.liked by using uri

        Args:
            server_id (int): guild id
        """
        server_id = str(server_id)
        session = create_session()
        track = session.query(Track_db).filter_by(
            server_id=server_id, uri=self.uri).first()
        if track:
            self.liked = True
        else:
            self.liked = False
        session.close()

    # На случай, если испольнитель не считается таковым на YT
    async def _get_info_from_Deezer(self, keyword: str) -> tuple:
        """Function that returns name and artist of the song from Deezer

        Args:
            keyword (str): Yotube keyword

        Returns:
            tuple: name, artist
        """
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

    async def _get_info_from_YT(self, keyword: str, bot: commands.Bot, ctx: commands.Context) -> bool:
        """Function that sets name and artist of the song from Yotube. Returns True if successful and None if not

        Args:
            keyword (str): Youtube keyword
            bot (commands.Bot): bot
            ctx (commands.Context): guild Context

        Returns:
            bool: Succcessful or not
        """
        self.ctx = ctx
        self.source = await YTDLSource.from_url(keyword, loop=bot.loop)
        if self.source:
            author = self.source.data.get('artist', '')
            track = self.source.data.get('track', '')
            track, author = await self._get_info_from_Deezer(self.source.title)
            self.liked = self.is_liked(self.source.title, track)
            if track and author and not self.name and not self.artist:
                r = SpotifyEngine()
                self._get_info_from_Spotify(track, author, r.sp)
            return True
        return None

    def _get_info_from_Spotify(self, name: str , artist: Artist, sp: spotipy.Spotify, track: dict=None) -> None:
        """Function that sets name and artist of the song from Spotify

        Args:
            name (str): the name of the song
            artist (Artist): Artist object
            sp (spotipy.Spotify): Spotify API
            track (dict, optional): if info is dictionary. Defaults to None.
        """
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
        self.keyword = self.name + ' ' + self.artist.name

    # Обновление Embed
    async def refresh_message(self):
        """Embed refresh"""
        embed = self.get_embed()
        await self.message.edit(embed=embed)

    def get_embed(self) -> discord.Embed:
        if self.from_radio:
            color = discord.Color.red()
        elif self.from_playlist:
            color = discord.Color.green()
        else:
            color = discord.Color.blurple()

        if self.is_intro:
            embed = (discord.Embed(title='Iosif Radio',
                                   color=discord.Color.red()).set_footer(text='Made with ❤️'))
            return embed

        if self.source:
            title, author, track, duration, url, thumbnail = self._get_info_from_source_data()
            self.liked = self.is_liked(title, track) or self.liked
            embed = (discord.Embed(title='Now playing:',
                                   description=title, color=color)
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

    def _get_info_from_source_data(self) -> tuple:
        """Function that sets name and artist of the song from Youtube_dl source

        Returns:
            tuple: title, author, track, duration, url, thumbnail
        """
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
        h = str(duration // 3600)
        if len(h) == 1:
            h = '0' + h
        duration %= 3600
        m = str(duration // 60)
        if len(m) == 1:
            m = '0' + m
        duration %= 60
        s = str(duration)
        if len(s) == 1:
            s = '0' + s
        return f'{h}:{m}:{s}'

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
        track = session.query(Track_db).filter_by(
            server_id=server_id, uri=uri).first()
        session.delete(track)
        session.commit()
        session.close()

    # обновление source для повторного запуска
    async def refresh(self, bot: commands.Bot) -> None:
        """Function that updates the song source

        Args:
            bot (commands.Bot): bot
        """
        self.source = await YTDLSource.from_url(self.source.title, loop=bot.loop)
        self.is_old = False

    async def update_message_reactions(self, reactions, from_radio=False):
        self.is_updating_reactions = True
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
        self.is_updating_reactions = False
        # if self.from_playlist:
        #     await self.message.add_reaction(emoji='📻')
