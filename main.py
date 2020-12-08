import discord
from discord.ext import commands
import asyncio
from discord import FFmpegPCMAudio
from consts import *
import os
from api import *
from data import db_session
from commands import music, playlist_music, queue_music


if __name__ == '__main__':
    db_session.global_init()
    
    bot = commands.Bot(command_prefix='!')

    bot.add_cog(music.Music(bot))
    bot.add_cog(queue_music.QueueMusic(bot))
    bot.add_cog(playlist_music.PlaylistMusic(bot))
    
    bot.run(TOKEN)

    @bot.event
    async def on_ready():
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')
        discord.opus.load_opus('libopus.so')
