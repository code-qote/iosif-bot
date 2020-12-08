import discord
from discord.ext import commands
import asyncio
from api import *
from consts import *
from youtube import YTDLSource


queue_current_position = dict()


class QueueMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def qnext(self, ctx):
        '''next song'''
        await self.play_next(ctx)
    
    @commands.command()
    async def qprev(self, ctx):
        '''previous song'''
        await self.play_previous(ctx)
    
    async def play_previous(self, ctx):
        server_id = ctx.message.guild.id
        queue_current_position[server_id] -= 1
        if queue_current_position[server_id] == 0:
            await ctx.send('This is the first song')
        else:
            request = get_song_from_queue(server_id, queue_current_position[server_id])
            if request:
                await self.qplay(ctx)
            else:
                await ctx.send('Error')

    async def play_next(self, ctx):
        server_id = ctx.message.guild.id
        queue_current_position[server_id] += 1
        request = get_song_from_queue(server_id, queue_current_position[server_id])
        if request:
            await self.qplay(ctx)
        elif not request and queue_current_position[server_id] == 1:
            await ctx.send('Queue is clear')
        else:
            queue_current_position[server_id] = 0
            await self.play_next(ctx)
    
    @commands.command()
    async def qjump(self, ctx, *, keyword):
        '''[song position] - jump to position in queue'''
        server_id = ctx.message.guild.id
        try:
            position = int(keyword)
            request = get_song_from_queue(server_id, position)
            if request:
                queue_current_position[server_id] = position
                await self.qplay(ctx)
            else:
                await ctx.send('Error')
        except ValueError:
            await ctx.send('Argument must be integer')

    
    @commands.command()
    async def qplay(self, ctx):
        '''play server queue'''
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
        async with ctx.typing():
            server_id = ctx.message.guild.id
            request = get_song_from_queue(server_id, queue_current_position[server_id])
            if not request:
                await ctx.send('Queue is clear')
            else:
                player = await YTDLSource.from_url(request, loop=self.bot.loop)
                if player:
                    ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
            await ctx.send('Now playing: {}'.format(player.title))
    
    @commands.command()
    async def qadd(self, ctx, *, keyword):
        '''[song name] - add song'''
        server_id = ctx.message.guild.id
        add_song(keyword)
        add_song_to_queue(keyword, server_id)
        await self.qlist(ctx)
    
    @commands.command()
    async def qlist(self, ctx):
        '''show all songs in queue'''
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
        '''clear queue'''
        server_id = ctx.message.guild.id
        clear_queue(server_id)
        await ctx.send('Queue is cleared!')
