import threading

import discord
from discord.ext import commands

from commands import memes, music
# from commands.fortnite import fortnite
from consts import *
from data import db_session
from web_server import WebServer
from background_task import check_update_task
from errors_handler import CommandErrorHandler

if __name__ == '__main__':
    bot = commands.Bot(command_prefix='!')
    # db_session.global_init('data/db.db')
    db_session.global_init()

    music_cog = music.Music(bot)
    error_cog = CommandErrorHandler(bot)
    # memes_cog = memes.Memes(bot)
    # fortnite_cog = fortnite.Fortnite(bot)
    web_server_cog = WebServer(bot)
    bot.add_cog(music_cog)
    # bot.add_cog(error_cog)
    # bot.add_cog(memes_cog)
    # bot.add_cog(fortnite_cog)
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
                await music_cog.dislike_song(await bot.get_context(reaction.message))
            elif reaction.emoji == '❌':
                await music_cog._leave(await bot.get_context(reaction.message))
            elif reaction.emoji == '⬅️':
                await music_cog._previous_playlist_page(await bot.get_context(reaction.message), reaction.message)
            elif reaction.emoji == '➡️':
                await music_cog._next_playlist_page(await bot.get_context(reaction.message), reaction.message)
            # elif reaction.emoji in languages:
            # await memes_cog.translate(await
            # bot.get_context(reaction.message), languages[reaction.emoji])
            elif reaction.emoji in digits:
                await music_cog._play_playlist(await bot.get_context(reaction.message), digits[reaction.emoji])
            elif reaction.emoji == '📻':
                await music_cog._radio_from_playlist(await bot.get_context(reaction.message))

    @bot.event
    async def on_ready():
        background_update = threading.Thread(
            target=check_update_task, daemon=True, args=[bot])
        background_update.start()

    # bot.run(TOKEN_TEST)
    bot.run(TOKEN)
