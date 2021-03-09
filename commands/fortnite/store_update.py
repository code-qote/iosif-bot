import asyncio
import datetime
from math import ceil, sqrt
from time import sleep, time
from mega import Mega

import pytz
from PIL import Image, ImageDraw, ImageFont
from requests import get
import os

from .fort_consts import *


def check_update_task():
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
        sleep(60)

def get_size(images_count):
    s = default_size // ceil(images_count ** 0.5)
    return s, s

def get_gradient(innerColor, outerColor, imgsize):
    image = Image.new('RGBA', imgsize)
    for y in range(imgsize[1]):
        for x in range(imgsize[0]):
            distanceToCenter = sqrt(
                (x - imgsize[0]/2) ** 2 + (y - imgsize[1]/2) ** 2)
            distanceToCenter = float(distanceToCenter) / \
                (sqrt(2) * imgsize[0]/2)
            r = outerColor[0] * distanceToCenter + \
                innerColor[0] * (1 - distanceToCenter)
            g = outerColor[1] * distanceToCenter + \
                innerColor[1] * (1 - distanceToCenter)
            b = outerColor[2] * distanceToCenter + \
                innerColor[2] * (1 - distanceToCenter)
            image.putpixel((x, y), (int(r), int(g), int(b)))
    return image

def get_store(response):
    print('Getting store...')
    image_size = get_size(len(response))
    images = []
    k = 0
    for image_info in response:
        url = image_info['imageUrl']
        with open('commands/fortnite/image.png', 'wb') as file:
            file.write(get(url).content)
        try:
            image = Image.open('commands/fortnite/image.png').convert('RGBA')
        except Exception:
            continue
        image = image.resize(image_size)

        result = get_gradient(*rarity_colors.get(image_info['rarity'], ([31, 31, 31], [
                              31, 31, 31])), (image_size[0] + 40, image_size[1] + 140))
        result.paste(image, (20, 20), image)
        result_size = result.size

        name = image_info['name']
        s = 0
        for i in name:
            s += symbols_to_pixels.get(i, 25)
        s += len(name) - 1
        font_size = 64
        while result_size[0] - s <= 0:
            s = round(s / 1.33)
            font_size = round(font_size / 1.33)
        offset = ((result_size[0] - s) // 2, image_size[0] + 10)
        draw = ImageDraw.Draw(result)
        font = ImageFont.truetype('commands/fortnite/font.ttf', font_size)
        draw.text(offset, name, (255, 255, 255), font=font)

        vbucks = Image.open('commands/fortnite/vbucks.png').convert('RGBA')
        vbucks_size = vbucks.size[0] // 4, vbucks.size[1] // 4
        vbucks = vbucks.resize(vbucks_size)
        price = str(image_info['vBucks'])
        if price == '0':
            price = '???'
        s = 0 
        for i in price:
            s += symbols_to_pixels.get(i, 25)
        s += len(price) - 1
        offset = ((result_size[0] - s - vbucks.size[0] // 4) // 2, offset[1] + 90)
        result.paste(vbucks, offset, vbucks)

        offset = (offset[0] + 40, offset[1] - 20)
        font = ImageFont.truetype('commands/fortnite/font.ttf', 48)
        draw.text(offset, price, (255, 255, 255), font=font)
        k += 1
        images.append(result)    
    result_size = (ceil((default_size - 7 * 30) / 6), ceil((default_size - 7 * 30) / 6))
    ans = get_gradient([37, 184, 229, 255], [
                       22, 136, 171, 255], (default_size - result_size[0], default_size - result_size[1]))
    i = 30
    k = 0
    ans_size = ans.size
    while k < len(images) and i + result_size[0] + 30 <= ans_size[0]:
        j = 30
        while k < len(images) and j + result_size[1] + 30 <= ans_size[1]:
            image = images[k].resize(result_size)
            ans.paste(image, (j, i))
            k += 1
            j += result_size[1] + 30
        i += result_size[0] + 30
    draw = ImageDraw.Draw(ans)
    font = ImageFont.truetype('commands/fortnite/font.ttf', 24)
    draw.text((10, ans_size[1] - 30), '@Iosif', (255, 255, 255), font=font)
    filename = 'commands/fortnite/store.png'
    ans.save(filename)
    mega = Mega()
    m = mega.login(mega_email, mega_password)
    old_file = m.find('store.png')
    m.delete(old_file[0])
    m.upload(filename)
    os.remove(filename)
    print('Store is done!')
