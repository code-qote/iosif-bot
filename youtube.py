import youtube_dl
from consts import *
from discord import FFmpegPCMAudio, PCMVolumeTransformer
import asyncio
import os

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(PCMVolumeTransformer):
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
        except Exception:
            return False
        if 'entries' in data:
            try:
                data = data['entries'][0]
            except IndexError:
                return

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as E:
            print(E)
        return cls(FFmpegPCMAudio(filename, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", **FFMPEG_OPTIONS), data=data)
