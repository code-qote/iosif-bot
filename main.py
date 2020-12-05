import discord
from discord.ext import commands
import youtube_dl
import asyncio
from discord import FFmpegPCMAudio
from requests import get
from consts import *
import os
import time
from data import db_session
from api import *

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


queues_current_position = dict()
playlists_current_position = dict()


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        except Exception():
            return False
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as E:
            print(E)
        return cls(discord.FFmpegPCMAudio(filename, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", **FFMPEG_OPTIONS), data=data)
    

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def qnext(self, ctx):
        await self.play_next(ctx)
    
    @commands.command()
    async def qprev(self, ctx):
        await self.play_previous(ctx)
    
    async def play_previous(self, ctx):
        global bot
        server_id = ctx.message.guild.id
        queues_current_position[server_id] -= 1
        if queues_current_position[server_id] == 0:
            await ctx.send('This is the first song')
        else:
            request = get_song_from_queue(server_id, queues_current_position[server_id])
            if request:
                await self.qplay(ctx)
            else:
                await ctx.send('Error')

    async def play_next(self, ctx):
        global bot
        server_id = ctx.message.guild.id
        queues_current_position[server_id] += 1
        request = get_song_from_queue(server_id, queues_current_position[server_id])
        if request:
            await self.qplay(ctx)
        elif not request and queues_current_position[server_id] == 1:
            await ctx.send('Queue is clear')
        else:
            queues_current_position[server_id] = 0
            await self.qplay(ctx)

    @commands.command()
    async def join(self, ctx, ctx_channel: discord.VoiceChannel = None):
        global bot
        try:
            channel = ctx.author.voice.channel
        except:
            channel = ctx_channel
        server_id = ctx.message.guild.id
        queues_current_position[server_id] = queues_current_position.get(server_id, 1)
        add_server(server_id)
        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, keyword):
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
        async with ctx.typing():
            player = await YTDLSource.from_url(keyword, loop=self.bot.loop)
            if player:
                ctx.voice_client.play(player)
        await ctx.send('Now playing: {}'.format(player.title))
    
    @commands.command()
    async def qplay(self, ctx):
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
        async with ctx.typing():
            server_id = ctx.message.guild.id
            request = get_song_from_queue(server_id, queues_current_position[server_id])
            if not request:
                await ctx.send('Queue is clear')
            else:
                player = await YTDLSource.from_url(request, loop=self.bot.loop)
                if player:
                    ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
                await ctx.send('Now playing: {}'.format(player.title))
    
    @commands.command()
    async def qadd(self, ctx, *, keyword):
        server_id = ctx.message.guild.id
        add_song(keyword)
        add_song_to_queue(keyword, server_id)
        await self.qlist(ctx)
    
    @commands.command()
    async def qlist(self, ctx):
        server_id = ctx.message.guild.id
        songs = songs_list_from_queue(server_id)
        async with ctx.typing():
            text = ''
            if songs:
                for song in songs:
                    text += f'{song["position"]}. {song["request"]}\n'
            else:
                text = 'Queue is clear'
        await ctx.send(text)
    
    @commands.command()
    async def qclear(self, ctx):
        server_id = ctx.message.guild.id
        clear_queue(server_id)
        await ctx.send('Queue is cleared!')
    
    @commands.command()
    async def play_queue(self, ctx):
        server_id = ctx.message.guild.id
        queue = get_queue(server_id)
        request = get_song_from_queue(server_id, queues_current_position[server_id])
        if request['success']:
            self.play(ctx, keyword=request)
        else:
            await ctx.send('Not found')
    
    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
    
    @commands.command()
    async def resume(self, ctx):
        if not ctx.voice_client.is_playing():
            ctx.voice_client.resume()
    
    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()


if __name__ == '__main__':
    db_session.global_init('data/db.db')
    bot = commands.Bot(command_prefix='!')

    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

    bot.add_cog(Music(bot))
    bot.run(TOKEN_TEST)

    @bot.event
    async def on_ready():
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')
        discord.opus.load_opus('libopus.so')
    
