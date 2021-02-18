from urllib import request
import discord
from discord.ext import commands
import asyncio
import itertools
from youtube import YTDLSource
from discord.ext.commands import bot
from discord.ext.commands.core import command


default_message_reactions = ['⏹️', '⏸️', '⏮️', '⏭️']
pause_message_reactions = ['⏹️', '▶️', '⏮️', '⏭️']

class Song:
    def __init__(self, ctx, source):
        self.source = source
        self.ctx = ctx
        self.is_old = False
        self.message = None
    
    def get_embed(self):
        if self.source:
            title = self.source.title
            author = self.source.data['uploader']
            duration = self.convert_duration(self.source.data['duration'])
            url = self.source.data['webpage_url']
            thumbnail = self.source.data['thumbnails'][0]['url']
            embed = (discord.Embed(title='Now playing:',
                                description=title, color=discord.Color.blurple())
                                .add_field(name='Author', value=author)
                                .add_field(name='Duration', value=duration)
                                .add_field(name='URL', value=url)
                                .set_thumbnail(url=thumbnail))             
            return embed

    def convert_duration(self, duration):
        h = duration // 3600
        duration %= 3600
        m = duration // 60
        duration %= 60
        s = duration
        return f'{int(h)}:{int(m)}:{int(s)}'
    
    async def refresh(self, bot):
        self.source = await YTDLSource.from_url(self.source.title, loop=bot.loop)
        self.is_old = False

    async def update_message_reactions(self, reactions):
        await self.message.clear_reactions()
        for reaction in reactions:
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
    
    def remove(self, i):
        del self._queue[i]

class VoiceChannel:
    def __init__(self, bot: commands.Bot, ctx):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self.audio_player = self.bot.loop.create_task(self.audio_player_task())
        asyncio.gather(self.audio_player)
    
    def __del__(self):
        self.audio_player.cancel()
    
    async def audio_player_task(self):
        while True:
            self.next.clear()

            if self.current:
                await self.current.message.clear_reactions()
            self.current = await self.songs.get()
            self.current.source.volume = 0.5
            if self.current.is_old:
                await self.current.refresh(self.bot)
            self.voice.play(self.current.source, after=self.play_next_song)
            self.current.is_old = True
            self.current.message = await self.current.ctx.send(embed=self.current.get_embed())
            await self.current.update_message_reactions(default_message_reactions)
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

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channels = dict()
    
    def get_voice_channel(self, ctx): 
        server_id = ctx.guild.id
        state = self.voice_channels.get(server_id)
        if not state:
            state = VoiceChannel(self.bot, ctx)
            self.voice_channels[server_id] = state
        return state
    
    @commands.command(name='join')
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
    async def _leave(self, ctx: commands.Context):
        '''Leave Iosif alone'''
        await self.voice_channels[ctx.guild.id].leave()
    
    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        '''Skip a song'''
        try:
            async with ctx.typing():
                await self.voice_channels[ctx.guild.id].skip()
        except:
            pass
    
    @commands.command(name='back')
    async def _back(self, ctx: commands.Context):
        '''Go back'''
        try:
            async with ctx.typing():
                await self.voice_channels[ctx.guild.id].back()
        except:
            pass
    
    @commands.command(name='jump')
    async def _jump(self, ctx: commands.Context, i):
        '''Jump to song'''
        try:
            async with ctx.typing():
                await self.voice_channels[ctx.guild.id].jump(int(i) - 1)
        except:
            pass
    
    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, keyword):
        '''Hey, Iosif. Light up the dance floor!'''
        async with ctx.typing():
            source = await YTDLSource.from_url(keyword, loop=self.bot.loop)
            song = Song(ctx, source)
            server_id = ctx.guild.id
            await self.voice_channels[server_id].songs.put(song)
            self.voice_channels[server_id].songs.list_to_show.append(song)
            await ctx.send('Added to queue {}'.format(source.title))

    @commands.command(name='stop')
    async def _stop(self, ctx: commands.Context):
        '''Have a rest'''
        self.voice_channels[ctx.guild.id].songs.clear()
        await self.voice_channels[ctx.guild.id].current.message.clear_reactions()
        self.voice_channels[ctx.guild.id].voice.stop()
    
    @commands.command(name='pause')
    async def _pause(self, ctx: commands.Context):
        '''Wait please'''
        self.voice_channels[ctx.guild.id].voice.pause()
        await self.voice_channels[ctx.guild.id].current.update_message_reactions(
            pause_message_reactions)
    
    @commands.command(name='resume')
    async def _resume(self, ctx: commands.Context):
        '''Yeah, go on'''
        self.voice_channels[ctx.guild.id].voice.resume()
        await self.voice_channels[ctx.guild.id].current.update_message_reactions(
            default_message_reactions)
    
    @commands.command(name='list')
    async def _list(self, ctx: commands.Context):
        '''Show list of the next songs'''
        async with ctx.typing():
            res = ''
            for i, v in enumerate(self.voice_channels[ctx.guild.id].songs.list_to_show):
                res += f'{i + 1}. {v.source.title}\n'
            await ctx.send(res)


# default_message_reactions = ['⏹️', '⏸️', '⏮️', '⏭️']
# pause_message_reactions = ['▶️', '⏹️', '⏮️', '⏭️']
