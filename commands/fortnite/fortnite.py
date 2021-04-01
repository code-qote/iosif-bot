from urllib import request
import discord
from discord.ext import commands
import asyncio
import itertools
from discord.ext.commands import bot
from discord.ext.commands.core import command
import aiohttp
import threading
from .store_update import check_update_task
from .fort_consts import API_KEY, DROPBOX_TOKEN
import dropbox
import os


class Fortnite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        checking_store_update = threading.Thread(target=check_update_task, daemon=True)
        checking_store_update.start()
    
    def get_embed(self, stats_type, nickname, picture, wins, kd, win_ratio,
                matches, kills, time_played, footer):
        embed = discord.Embed(title=stats_type,
                              description=nickname, color=0x01a706)
        if picture:
            embed.set_thumbnail(url=picture)
        embed.add_field(name="Wins", value=wins, inline=True)
        embed.add_field(name="KD", value=kd, inline=True)
        embed.add_field(name="Win %", value=win_ratio, inline=True)
        embed.add_field(name="Matches", value=matches, inline=True)
        embed.add_field(name="Kills", value=kills, inline=True)
        embed.add_field(name="Time played", value=time_played, inline=True)
        if footer:
            embed.set_footer(text=footer)
        return embed
    
    async def get_stats(self, platform, nickname):
        headers = {'TRN-Api-Key': API_KEY}
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.fortnitetracker.com/v1/profile/{platform}/{nickname}', headers=headers) as response:
                response = eval(await response.text())
        stats = response.get('stats', None)
        if not stats:
            return None
        k = 0
        to_embed = []
        used = set()
        for stat in stats.keys():
            if k < 3:
                if stat != 'ltm':
                    k += 1
                    if stat == 'p2':
                        stats_type = 'Solo stats'
                        picture = response['avatar']
                        footer = None
                    elif stat == 'p10':
                        stats_type = 'Duos stats'
                        picture = None
                        footer = None
                        nickname = ''
                    elif stat == 'p9':
                        stats_type = 'Squad stats'
                        footer = 'Made with ❤️'
                        picture = None
                        nickname = ''
                    wins = stats[stat]['top1']['displayValue']
                    kd = stats[stat]['kd']['displayValue']
                    win_ratio = stats[stat]['winRatio']['displayValue']
                    matches = stats[stat]['matches']['displayValue']
                    kills = stats[stat]['kills']['displayValue']
                    time_played = stats[stat]['minutesPlayed']['displayValue']
                if stats_type not in used:
                    to_embed.append(self.get_embed(stats_type, nickname, picture, wins, kd,
                                    win_ratio, matches, kills, time_played, footer))
                    used.add(stats_type)
        return to_embed
    
    @commands.command(name='stats')
    async def _stats(self, ctx: commands.Context, platform, *nickname):
        '''!stats {pc/xbl/psn} {epic-nickname}'''
        nickname = ' '.join(nickname)
        async with ctx.typing():
            stats = await self.get_stats(platform, nickname)
            if not stats:
                await ctx.send("The player wasn't found")
            else:
                for embed in stats:
                    await ctx.send(embed=embed)

    @commands.command(name='store')
    async def _store(self, ctx: commands.Context):
        '''Get Fortnite store'''
        async with ctx.typing():
            dbx = dropbox.Dropbox(DROPBOX_TOKEN)
            dbx.users_get_current_account()
            for i in dbx.files_list_folder('/stores').entries:
                metadata, file_to_download = dbx.files_download(
                    f'/stores/{i.name}')
                with open(i.name, 'wb') as file:
                    file.write(file_to_download.content)
                with open(i.name, 'rb') as file:
                    await ctx.send(file=discord.File(file))
                os.remove(i.name)
