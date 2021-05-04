import discord
from discord.ext import commands
import asyncio
import aiohttp
from random import randint
import os


class Memes(commands.Cog):
    API_LINK = 'https://reddit-meme-api.herokuapp.com/memes/1'

    memes = dict()

    def __init__(self, bot):
        self.bot = bot
    
    async def translate(self, ctx: commands.Context, language):
        API_LINK_IMAGE = 'https://iosif-rest-api.herokuapp.com/api/v1/translate_image'
        API_LINK_TEXT = 'https://iosif-rest-api.herokuapp.com/api/v1/translate_text'
        async with aiohttp.ClientSession() as session:
            json = {'image_url': self.memes[ctx.message][0], 'language': language}
            async with session.get(API_LINK_IMAGE, json=json) as response:
                print(response.status)
                if response.status == 200:
                    meme_text = await response.json()
                    # print(meme_text)
            json = {'text': self.memes[ctx.message][1], 'language': language}
            async with session.get(API_LINK_TEXT, json=json) as response:
                if response.status == 200:
                    message_text = await response.json()
            # print(message_text + '\n' + meme_text)
            await ctx.message.edit(content=message_text + '\n' + meme_text)
        await ctx.message.clear_reactions()
        for reaction in ['🇷🇺', '🇩🇪', '🇪🇸', '🇬🇧']:
            await ctx.message.add_reaction(reaction)
    
    @commands.command()
    async def meme(self, ctx: commands.Context):
        '''Iosif, send funny meme'''
        async with ctx.typing(): 
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(self.API_LINK) as response:
                        json = await response.json()
                        title = json['title']
                        image_url = json['image_previews'][-1]
                    async with session.get(image_url) as response:
                        with open('meme.jpg', 'wb') as file:
                            file.write(await response.read())
                except Exception:
                    await ctx.send('There was an error 😞')
                else:
                    image = discord.File('meme.jpg')
                    message = await ctx.send(title, file=image)
                    self.memes[message] = (image_url, message.content)
                    await message.add_reaction('🇷🇺')
                    await message.add_reaction('🇩🇪')
                    await message.add_reaction('🇪🇸')
                    await message.add_reaction('🇬🇧')



