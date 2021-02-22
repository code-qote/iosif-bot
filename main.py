import discord
from discord.ext import commands
import asyncio
from discord import FFmpegPCMAudio
from consts import *
import os
from api import *
from data import db_session
from commands import music, memes
from commands.fortnite import fortnite


if __name__ == '__main__':
    db_session.global_init()
    bot = commands.Bot(command_prefix='!')

    music_cog = music.Music(bot)
    memes_cog = memes.Memes(bot)
    fortnite_cog = fortnite.Fortnite(bot)
    bot.add_cog(music_cog)
    bot.add_cog(memes_cog)
    bot.add_cog(fortnite_cog)
    # bot.add_cog(queue_music.QueueMusic(bot))
    # bot.add_cog(playlist_music.PlaylistMusic(bot))

    @bot.event
    async def on_reaction_add(reaction: discord.Reaction, user):
        server_id = reaction.message.guild.id
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
    
    bot.run(TOKEN_TEST)

