import asyncio
import os

import discord
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks

from api import *
from commands import memes, music
from commands.fortnite import fortnite
from consts import *
from data import db_session
from web_server import WebServer


if __name__ == '__main__':
    bot = commands.Bot(command_prefix='!')
    # db_session.global_init('data/db.db')
    db_session.global_init()

    music_cog = music.Music(bot)
    memes_cog = memes.Memes(bot)
    fortnite_cog = fortnite.Fortnite(bot)
    web_server_cog = WebServer(bot)
    bot.add_cog(music_cog)
    bot.add_cog(memes_cog)
    bot.add_cog(fortnite_cog)
    bot.add_cog(web_server_cog)

    @bot.event
    async def on_reaction_add(reaction: discord.Reaction, user):
        if user != bot.user:
            if reaction.emoji == '⏹️':
                await music_cog._stop(await bot.get_context(reaction.message))
            elif reaction.emoji == '⏸️':
                await music_cog._pause(await bot.get_context(reaction.message))
            elif reaction.emoji == '⏮️':
                await music_cog._back(await bot.get_context(reaction.message))
            elif reaction.emoji == '⏭️':
                await music_cog._skip(await bot.get_context(reaction.message))
            elif reaction.emoji == '▶️':
                await music_cog._resume(await bot.get_context(reaction.message))
            elif reaction.emoji == '👍':
                await music_cog.like_song(await bot.get_context(reaction.message))
            elif reaction.emoji == '👎':
                await music_cog.unlike_song(await bot.get_context(reaction.message))
            elif reaction.emoji in languages:
                await memes_cog.translate(await bot.get_context(reaction.message), languages[reaction.emoji])
    
    # bot.run(TOKEN_TEST)
    bot.run(TOKEN)
