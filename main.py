import discord
from discord.ext import commands
import youtube_dl
import asyncio
from discord import FFmpegPCMAudio
from requests import get
from consts import TOKEN, BOT_CHANNEL, ytdl_format_options, FFMPEG_OPTIONS, VIDEO_URL, YOUTUBE_API_URL, API_TOKEN


youtube_dl.utils.bug_reports_message = lambda: ''

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

def get_url(keyword):
    request = f'{YOUTUBE_API_URL}q={keyword}&regionCode=US&key={API_TOKEN}'
    json_response = get(request).json()
    return VIDEO_URL + json_response['items'][0]['id']['videoId']


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
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)
    

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, ctx_channel: discord.VoiceChannel = None):
        if ctx.channel.name == BOT_CHANNEL:
            try:
                channel = ctx.author.voice.channel
            except:
                channel = ctx_channel
            await channel.connect()

    @commands.command()
    async def play(self, ctx, *, keyword):
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
        async with ctx.typing():
            player = await YTDLSource.from_url(get_url(keyword), loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Ошибка: %s' % e) if e else None)

        await ctx.send('Сейчас играет: {}'.format(player.title))
    
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
         if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
    
    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()


if __name__ == '__main__':
    bot = commands.Bot(command_prefix='!')
    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
    bot.add_cog(Music(bot))
    bot.run(TOKEN)

    @bot.event
    async def on_ready():
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')
        discord.opus.load_opus('libopus.so')
    
