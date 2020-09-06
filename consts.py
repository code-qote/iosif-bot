TOKEN = 'Njc4NjM2NDg2NDQ2NTQ2OTc0.Xklreg.NpEp6lij-qTsNIFsr1d2VQj__-Y'
BOT_CHANNEL = 'forbot'
VIDEO_URL = 'https://www.youtube.com/watch?v='
YOUTUBE_API_URL = 'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&'
API_TOKEN = 'AIzaSyCtCZl9l1Vu1ookv-79MQ5-oqfertcWMBc'

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

birthdays = [(13, 4, 'Никита', '13 апреля'), (30, 7, 'Кирилл', '30 июля'), (7, 9, 'Вова', '7 сентября'), (30, 12, 'Макс', '30 декабря'), (3, 10, 'Костя', '3 ноября'), (9, 1, 'Коля', '9 января')]
congratulations = ['''Сегодня, date, в городе Самаре родился Человек с большой буквы — name!
Его появление на свет является важным событием в жизни нашей великой страны! Желаем тебе дожить до ста лет, пусть мотор в твоей груди работает без перебоев и без ремонтов, пусть жизнь твоя будет широкой и ровной трассой без ухабов и рытвин.
Желаем также, чтоб не заносило тебя на крутых поворотах, чтобы ты всегда крепко держал руль своей жизни в твердых руках.
Удачной и счастливой тебе дороги! Любви! Львиного здоровья! А главное, чувствовать себя счастливым каждый день своей жизни!''']
birthday_channel_id = 675248925489364994
