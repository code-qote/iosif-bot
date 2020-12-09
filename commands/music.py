import discord
from discord.ext import commands
import asyncio
from api import *
from consts import *
from youtube import YTDLSource
from .queue_music import queue_current_position


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def join(self, ctx, ctx_channel: discord.VoiceChannel = None):
        '''join to the voice channel'''
        try:
            channel = ctx.author.voice.channel
        except:
            channel = ctx_channel
        server_id = ctx.message.guild.id
        print(server_id)
        queue_current_position[server_id] = queue_current_position.get(server_id, 1)
        add_server(server_id)
        await channel.connect()
    
    @commands.command()
    async def play(self, ctx, *, keyword):
        '''[song name] - play song'''
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
        async with ctx.typing():
            player = await YTDLSource.from_url(keyword, loop=self.bot.loop)
            if player:
                ctx.voice_client.play(player)
        await ctx.send('Now playing: {}'.format(player.title))
    
    @commands.command()
    async def stop(self, ctx):
        '''stop'''
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()

    @commands.command()
    async def pause(self, ctx):
        '''pause'''
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
    
    @commands.command()
    async def resume(self, ctx):
        '''resume'''
        if not ctx.voice_client.is_playing():
            ctx.voice_client.resume()
    
    @commands.command()
    async def leave(self, ctx):
        '''leave the voice channel'''
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
