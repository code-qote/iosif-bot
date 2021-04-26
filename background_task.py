import datetime
from random import choice, randint
from time import sleep
import asyncio
import discord

import pymorphy2
import pytz
from requests import get

from commands.fortnite.fort_consts import *
from commands.fortnite.store_update import get_store
from data.__all_models import Holiday
from data.db_session import create_session


def check_update_task(bot):
    global holiday
    last = None
    while True:
        time = datetime.datetime.now()
        timezone = pytz.timezone('Etc/Greenwich')
        time = time.astimezone(timezone)
        headers = {'TRN-Api-Key': API_KEY}
        try:
            response = eval(
                get('https://api.fortnitetracker.com/v1/store', headers=headers).content)
        except Exception:
            pass
        if len(response):
            if response != last:
                last = response
                get_store(response)

                session = create_session()
                old_holiday = session.query(Holiday).limit(1).first()
                if old_holiday:
                    session.delete(old_holiday)
                holiday = Holiday(name=get_holiday())
                session.add(holiday)
                session.commit()
                session.close()
        if bot:
            update_presence = bot.loop.create_task(update_presence_task(bot))
            asyncio.gather(update_presence)
        sleep(60)

async def update_presence_task(bot):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'{len(bot.guilds)} servers!'))

def get_holiday():
    beginnings = ['День независимости', 'Христианский праздник',
                  'День защитника', 'Международный день', 'День народного']
    with open('nouns.txt', 'r', encoding='utf-8') as file:
        nouns = [i.strip('\r\n') for i in file.readlines()]
    beginning = choice(beginnings)
    morph = pymorphy2.MorphAnalyzer()
    noun = morph.parse(choice(nouns))[0].inflect({'gent'}).word
    return beginning + ' ' + noun
