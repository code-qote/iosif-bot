TOKEN = 'Njc4NjM2NDg2NDQ2NTQ2OTc0.XklvYw.W1Fume1JRGVDG6AV3DXpKQuCgvQ'
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
