TOKEN = 'Nzc4NDYyODM0Mzg0MTc1MTA0.X7SWAg.mB4hoCak5IHWtZT5llYAApYqhRc'
BOT_CHANNEL = 'forbot'

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'options': '-vn'
}

birthdays = [(13, 4, 'Никита', '13 апреля'), (30, 7, 'Кирилл', '30 июля'), (7, 9, 'Вова', '7 сентября'), (30, 12, 'Макс', '30 декабря'), (3, 11, 'Костя', '3 ноября'), (9, 1, 'Коля', '9 января')]
congratulations = ['''Сегодня, date, в городе Самаре родился Человек с большой буквы — name!
Его появление на свет является важным событием в жизни нашей великой страны! Желаем тебе дожить до ста лет, пусть мотор в твоей груди работает без перебоев и без ремонтов, пусть жизнь твоя будет широкой и ровной трассой без ухабов и рытвин.
Желаем также, чтоб не заносило тебя на крутых поворотах, чтобы ты всегда крепко держал руль своей жизни в твердых руках.
Удачной и счастливой тебе дороги! Любви! Львиного здоровья! А главное, чувствовать себя счастливым каждый день своей жизни!''']
birthday_channel_id = 675248925489364994
time_to_sleep = 60
