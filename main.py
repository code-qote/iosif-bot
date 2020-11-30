import discord
from discord.ext import commands
import youtube_dl
import asyncio
from discord import FFmpegPCMAudio
from requests import get
from consts import *
import os
import time
from datetime import date
from threading import Thread

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

last_congratulation = None
last_day = None

async def check_birthdays():
    await bot.wait_until_ready()
    global last_congratulation, last_day
    while not bot.is_closed():
        day = date.today()
        if day != last_day:
            for birthday in birthdays:
                if birthday[0] == day.day and birthday[1] == day.month:
                    from random import choice
                    congratulation = choice(congratulations)
                    while congratulation == last_congratulation:
                        congratulation = choice(congratulations)
                    channel = bot.get_channel(birthday_channel_id)
                    await channel.send(congratulation.replace('date', birthday[3]).replace('name', birthday[2]))
                    last_congratulation = congratulation
                    last_day = day
                    break
        await asyncio.sleep(time_to_sleep)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

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
    async def join(self, ctx, ctx_channel: discord.VoiceChannel = None):
        global bot
        if ctx.channel.name == BOT_CHANNEL:
            try:
                channel = ctx.author.voice.channel
            except:
                channel = ctx_channel
            print(list(bot.get_all_channels()))
            print(bot.guilds)
            await channel.connect()

    @commands.command()
    async def play(self, ctx, *, keyword):
        if ctx.channel.name == BOT_CHANNEL:
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                ctx.voice_client.stop()
            async with ctx.typing():
                player = await YTDLSource.from_url(keyword, loop=self.bot.loop)
                ctx.voice_client.play(player, after=lambda e: print('Ошибка: %s' % e) if e else None)
            await ctx.send('Сейчас играет: {}'.format(player.title))
    
    @commands.command()
    async def stop(self, ctx):
        if ctx.channel.name == BOT_CHANNEL:
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                ctx.voice_client.stop()

    @commands.command()
    async def pause(self, ctx):
        if ctx.channel.name == BOT_CHANNEL:
            if ctx.voice_client.is_playing():
                ctx.voice_client.pause()
    
    @commands.command()
    async def resume(self, ctx):
        if ctx.channel.name == BOT_CHANNEL:
            if ctx.voice_client.is_paused():
                ctx.voice_client.resume()
    
    @commands.command()
    async def leave(self, ctx):
        if ctx.channel.name == BOT_CHANNEL:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            await ctx.voice_client.disconnect()


if __name__ == '__main__':
    bot = commands.Bot(command_prefix='!')
    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
    bot.add_cog(Music(bot))
    #bot.loop.create_task(check_birthdays())
    bot.run(TOKEN)

    @bot.event
    async def on_ready():
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')
        discord.opus.load_opus('libopus.so')
    
