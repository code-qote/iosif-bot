TOKEN = 'Njc4NjM2NDg2NDQ2NTQ2OTc0.Xklreg.NpEp6lij-qTsNIFsr1d2VQj__-Y'
TOKEN_TEST = 'Nzc4NDYyODM0Mzg0MTc1MTA0.X7SWAg.mB4hoCak5IHWtZT5llYAApYqhRc'
API_URL_SERVER = 'http://127.0.0.1:5000/api/server?'
API_URL_SONG = 'http://127.0.0.1:5000/api/song?'

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
    'source_address': '0.0.0.0',
    'age_limit': 17
}


FFMPEG_OPTIONS = {
    'options': '-vn'
}

MESSAGE_API_TOKEN = 'QHKqKGksdXMNwH9NgKkLy2NcK9cHes'

languages = {'🇷🇺': 'ru', '🇩🇪': 'de', '🇪🇸': 'es', '🇬🇧': 'en'}
digits = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3, '5️⃣': 4,
          '6️⃣': 5, '7️⃣': 6, '8️⃣': 7, '9️⃣': 8, '🔟': 9}
