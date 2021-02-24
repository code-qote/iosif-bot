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
from .fort_consts import API_KEY, mega_email, mega_password, mega_token
from mega import Mega


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
        return self.get_embed(stats_type, nickname, picture, wins, kd,
                            win_ratio, matches, kills, time_played, footer)
    
    @commands.command(name='stats')
    async def _stats(self, ctx: commands.Context, platform, *nickname):
        '''!stats {pc/xbl/psn} {epic-nickname}'''
        nickname = ' '.join(nickname)
        async with ctx.typing():
            stats = self.get_stats(platform, nickname)
            if not stats:
                await ctx.send("The player wasn't found")
            else:
                await ctx.send(embed=stats)

    @commands.command(name='store')
    async def _store(self, ctx: commands.Context):
        async with ctx.typing():
            mega = Mega()
            m = mega.login(mega_email, mega_password)
            file = m.find('store.png')
            m.download(file)
            with open('store.png', 'rb') as file:
                await ctx.send(file=discord.File(file))
