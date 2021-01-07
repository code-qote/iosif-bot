from mega import Mega
import discord
from discord.ext import commands
import asyncio
from random import randint
import os

mega_email = 'iosif.bot@yandex.ru'
mega_password = 'for_bot123'

class Memes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def meme(self, ctx):
        '''send random meme'''
        mega = Mega()
        m = mega.login(mega_email, mega_password)
        files_count = len(m.get_files())
        file_number = randint(0, files_count - 1)
        file = m.find(f'memes/meme_file_{file_number}.jpg') 
        while file is None:
            file_number = randint(0, files_count - 1)
            file = m.find(f'memes/meme_file_{file_number}.jpg')
        try:
            m.download(file)
        except PermissionError:
            pass
        filename = f'meme_file_{file_number}.jpg'
        with open(filename, 'rb') as file:
            await ctx.send(file=discord.File(file))
        os.remove(filename)
            

