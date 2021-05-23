import asyncio
from http import server
import io
import itertools
from urllib import request

import discord
from data.__all_models import Track_db
from data.db_session import create_session
from discord.ext import commands
from discord.ext.commands import bot
from discord.ext.commands.core import command
from requests.sessions import session
from youtube import YTDLSource

from ._all_classes import *
from data.db_session import create_session
from data.__all_models import Holiday

default_message_reactions = ['⏹️', '⏸️', '⏮️', '⏭️', '👍', '👎', '❌']
pause_message_reactions = ['⏹️', '▶️', '⏮️', '⏭️', '👍', '👎', '❌']
default_radio_message_reactions = ['⏹️', '⏸️', '⏭️', '👍', '👎', '❌']
pause_radio_message_reactions = ['⏹️', '▶️', '⏭️', '👍', '👎', '❌']
default_playlist_message_reactions = [
    '⏹️', '⏸️', '⏮️', '⏭️', '👍', '👎', '📻', '❌']
pause_playlist_message_reactions = ['⏹️', '▶️', '⏮️', '⏭️', '👍', '👎', '📻', '❌']


async def send_info(ctx, title, message):
    await ctx.send(embed=discord.Embed(title=title, description=message, color=discord.Color.greyple()))


async def send_error(ctx, message):
    await ctx.send(embed=discord.Embed(title=message, color=discord.Color.red()))


async def send_success(ctx, message):
    await ctx.send(embed=discord.Embed(title=message, color=discord.Color.green()))

def check_blocking(func):
    async def wrapper(*args, **kwargs):
        if func.__name__ not in args[0].blocked_commands:
            return await func(*args, **kwargs)
    return wrapper

class Music(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_channels = dict()

        self.blocked_commands = []
    
    async def _play_playlist(self, ctx, number):
        server_id = ctx.guild.id
        if self.voice_channels[server_id].playlists_searching_message:
            if not self.voice_channels[server_id].playlists_searching_message.is_updating_reactions:
                async with ctx.typing():
                    await self.voice_channels[server_id].play_playlist(number)

    async def like_song(self, ctx):
        voice_channel = self.get_voice_channel(ctx)
        current = voice_channel.current
        if current:
            if not current.is_updating_reactions:
                try:
                    current.add_to_db(ctx.guild.id)
                except Exception:
                    pass
                current.liked = True
                await current.refresh_message()

                if self.voice_channels[ctx.guild.id].current.from_radio:
                    reactions = {'default': default_radio_message_reactions,
                                 'pause': pause_radio_message_reactions}
                elif self.voice_channels[ctx.guild.id].current.from_playlist:
                    reactions = {'default': default_playlist_message_reactions,
                                 'pause': pause_playlist_message_reactions}
                else:
                    reactions = {'default': default_message_reactions,
                                 'pause': pause_message_reactions}

                if self.voice_channels[ctx.guild.id].voice.is_playing():
                    await self.voice_channels[ctx.guild.id].current.update_message_reactions(
                        reactions['default'])
                elif self.voice_channels[ctx.guild.id].voice.is_paused():
                    await self.voice_channels[ctx.guild.id].current.update_message_reactions(
                        reactions['pause'])

    async def unlike_song(self, ctx):
        voice_channel = self.get_voice_channel(ctx)
        current = voice_channel.current
        if current:
            if not current.is_updating_reactions:
                try:
                    current.remove_from_db(ctx.guild.id, current.uri)
                except Exception:
                    pass
                current.liked = False
                await current.refresh_message()

                if self.voice_channels[ctx.guild.id].current.from_radio:
                    reactions = {'default': default_radio_message_reactions,
                                 'pause': pause_radio_message_reactions}
                elif self.voice_channels[ctx.guild.id].current.from_playlist:
                    reactions = {'default': default_playlist_message_reactions,
                                 'pause': pause_playlist_message_reactions}
                else:
                    reactions = {'default': default_message_reactions,
                                 'pause': pause_message_reactions}

                if self.voice_channels[ctx.guild.id].voice.is_playing():
                    await self.voice_channels[ctx.guild.id].current.update_message_reactions(
                        reactions['default'])
                elif self.voice_channels[ctx.guild.id].voice.is_paused():
                    await self.voice_channels[ctx.guild.id].current.update_message_reactions(
                        reactions['pause'])

    def get_voice_channel(self, ctx):
        server_id = ctx.guild.id
        state = self.voice_channels.get(server_id)
        if not state:
            state = VoiceChannel(self.bot, ctx)
            self.voice_channels[server_id] = state
        return state

    async def _next_playlist_page(self, ctx: commands.Context, message: discord.Message):
        server_id = ctx.guild.id
        if self.voice_channels[server_id].playlists_searching_message or self.voice_channels[server_id].songs_list_message:
            if message == self.voice_channels[server_id].playlists_searching_message.message:
                if not self.voice_channels[server_id].playlists_searching_message.is_updating_reactions:
                    self.voice_channels[server_id].playlists_searching_message.next_page(
                    )
                    await self.voice_channels[server_id].playlists_searching_message.refresh_page()
            elif message == self.voice_channels[server_id].songs_list_message.message:
                if not self.voice_channels[server_id].songs_list_message.is_updating_reactions:
                    self.voice_channels[server_id].songs_list_message.next_page(
                    )
                    await self.voice_channels[server_id].songs_list_message.refresh_page()

    async def _previous_playlist_page(self, ctx: commands.Context, message: discord.Message):
        server_id = ctx.guild.id
        if self.voice_channels[server_id].playlists_searching_message or self.voice_channels[server_id].songs_list_message:
            if message == self.voice_channels[server_id].playlists_searching_message.message:
                if not self.voice_channels[server_id].playlists_searching_message.is_updating_reactions:
                    self.voice_channels[server_id].playlists_searching_message.previous_page(
                    )
                    await self.voice_channels[server_id].playlists_searching_message.refresh_page()
            elif message == self.voice_channels[server_id].songs_list_message.message:
                if not self.voice_channels[server_id].songs_list_message.is_updating_reactions:
                    self.voice_channels[server_id].songs_list_message.previous_page(
                    )
                    await self.voice_channels[server_id].songs_list_message.refresh_page()

    @commands.command(name='playlist')
    #@check_blocking
    async def _playlist(self, ctx: commands.Context, *, keyword):
        '''!playlist [name of playlist]. Searching playlist'''
        server_id = ctx.guild.id
        await self.voice_channels[server_id].search_playlists(keyword)

    @commands.command(name='all_playlists')
    #@check_blocking
    async def _all_playlists(self, ctx: commands.Context):
        server_id = ctx.guild.id
        await self.voice_channels[server_id].search_playlists()

    @commands.command(name='join')
    #@check_blocking
    async def _join(self, ctx: commands.Context, ctx_channel=None):
        '''Join Iosif to your voice channel'''
        try:
            channel = ctx.author.voice.channel
        except:
            channel = ctx_channel
        server_id = ctx.guild.id
        self.voice_channels[server_id] = self.get_voice_channel(ctx)
        self.voice_channels[server_id].voice = await channel.connect()

    @commands.command(name='leave')
    #@check_blocking
    async def _leave(self, ctx: commands.Context):
        '''Leave Iosif alone'''
        await self._stop(ctx)
        server_id = ctx.guild.id
        if self.voice_channels[server_id].current:
            if not self.voice_channels[server_id].current.is_updating_reactions:
                await self.voice_channels[ctx.guild.id].leave()

    @commands.command(name='skip')
    #@check_blocking
    async def _skip(self, ctx: commands.Context):
        '''Skip a song'''
        server_id = ctx.guild.id
        if self.voice_channels[server_id].current:
            if self.voice_channels[server_id].current:
                if not self.voice_channels[server_id].current.is_updating_reactions:
                    try:
                        async with ctx.typing():
                            await self.voice_channels[ctx.guild.id].skip()
                    except:
                        pass

    @commands.command(name='back')
    #@check_blocking
    async def _back(self, ctx: commands.Context):
        '''Go back'''
        server_id = ctx.guild.id
        if self.voice_channels[server_id].current:
            if self.voice_channels[server_id].current:
                if not self.voice_channels[server_id].current.is_updating_reactions:
                    try:
                        async with ctx.typing():
                            await self.voice_channels[ctx.guild.id].back()
                    except:
                        pass

    @commands.command(name='jump')
    #@check_blocking
    async def _jump(self, ctx: commands.Context, i):
        '''Jump to song'''
        try:
            async with ctx.typing():
                await self.voice_channels[ctx.guild.id].jump(int(i) - 1)
        except:
            pass

    @commands.command(name='play')
    #@check_blocking
    async def _play(self, ctx: commands.Context, *, keyword):
        '''Hey, Iosif. Light up the dance floor!'''
        async with ctx.typing():
            server_id = ctx.guild.id
            if not self.voice_channels[server_id].radio_mode and not self.voice_channels[server_id].playlist_mode:
                source = await YTDLSource.from_url(keyword, loop=self.bot.loop)
                song = Song()
                song.keyword = keyword
                # await song._get_info_from_YT(keyword, self.bot, ctx)
                await self.voice_channels[server_id].songs.put(song)
                self.voice_channels[server_id].songs.list_to_show.append(song)
                await send_success(ctx, 'Added to queue {}'.format(source.title))
            elif self.voice_channels[server_id].radio_mode:
                await send_error(ctx, 'You must stop radio at first!')
            else:
                await send_error(ctx, 'You must stop playling playlist at first!')

    # @commands.command(name='remove')
    # async def _remove(self, ctx: commands.Context, i):
    #     self.voice_channels[ctx.guild.id].remove(i - 1)

    @commands.command(name='radio')
    #@check_blocking
    async def _radio(self, ctx: commands.Context):
        '''Turn on the radio'''
        await self.voice_channels[ctx.guild.id].radio(ctx)

    async def _radio_from_playlist(self, ctx: commands.Context):
        server_id = ctx.guild.id
        if self.voice_channels[server_id].current:
            if not self.voice_channels[server_id].current.is_updating_reactions:
                await self.voice_channels[ctx.guild.id].radio(ctx, from_playlist=True)

    @commands.command(name='stop')
    #@check_blocking
    async def _stop(self, ctx: commands.Context):
        '''Have a rest'''
        server_id = ctx.guild.id
        if self.voice_channels[server_id].current:
            if not self.voice_channels[server_id].current.is_updating_reactions:
                self.voice_channels[ctx.guild.id].radio_mode = False
                self.voice_channels[ctx.guild.id].playlist_mode = False
                self.voice_channels[ctx.guild.id].is_loading = False
                self.voice_channels[ctx.guild.id].songs.clear()
                await self.voice_channels[ctx.guild.id].current.message.clear_reactions()
                self.voice_channels[ctx.guild.id].voice.stop()

    @commands.command(name='pause')
    #@check_blocking
    async def _pause(self, ctx: commands.Context):
        '''Wait please'''
        server_id = ctx.guild.id
        if self.voice_channels[server_id].current:
            if not self.voice_channels[server_id].current.is_updating_reactions:
                self.voice_channels[ctx.guild.id].voice.pause()
                if not self.voice_channels[ctx.guild.id].radio_mode:
                    await self.voice_channels[ctx.guild.id].current.update_message_reactions(
                        pause_message_reactions)
                else:
                    await self.voice_channels[ctx.guild.id].current.update_message_reactions(
                        pause_radio_message_reactions)

    @commands.command(name='resume')
    #@check_blocking
    async def _resume(self, ctx: commands.Context):
        '''Yeah, go on'''
        server_id = ctx.guild.id
        if self.voice_channels[server_id].current:
            if not self.voice_channels[server_id].current.is_updating_reactions:
                self.voice_channels[ctx.guild.id].voice.resume()
                if not self.voice_channels[ctx.guild.id].radio_mode:
                    await self.voice_channels[ctx.guild.id].current.update_message_reactions(
                        default_message_reactions)
                else:
                    await self.voice_channels[ctx.guild.id].current.update_message_reactions(
                        default_radio_message_reactions)

    @commands.command(name='list')
    #@check_blocking
    async def _list(self, ctx: commands.Context):
        '''Show list of the next songs'''
        async with ctx.typing():
            res = []
            for v in self.voice_channels[ctx.guild.id].songs.list_to_show:
                if v.source:
                    res.append(v.source.title)
                else:
                    res.append(v.keyword)
            if res:
                await self.voice_channels[ctx.guild.id].send_songs_list(res)
            else:
                await send_info(ctx, 'List', 'The queue is empty.')

    @commands.command(name='update')
    #@check_blocking
    async def _update(self, ctx: commands.Context):
        '''Get information about last update'''
        async with ctx.typing():
            with io.open('patch-note.txt', 'r', encoding='utf-8') as file:
                text = file.read()
                await send_info(ctx, 'Patch Note', text)

    # не относится к music
    @commands.command(name='holiday')
    #@check_blocking
    async def _holiday(self, ctx: commands.Context):
        '''What is holiday today? (Not real)'''
        async with ctx.typing():
            session = create_session()
            holiday = session.query(Holiday).limit(1).first()
            if holiday:
                await send_success(ctx, holiday.name)
            session.close()
