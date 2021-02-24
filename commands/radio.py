import spotipy

class Artist:
    def __init__(self, info):
        self.id = info['id']
        self.uri = info['uri']
        self.name = info['name']
    
    def __str__(self):
        return str({'id': self.id, 'uri': self.uri, 'name': self.name})

class Album:
    def __init__(self, info):
        self.id = info['id']
        self.uri = info['uri']
        self.name = info['name']
        self.image_url = info['images'][0]['url']
        self.release_date = info['release_date']
        self.total_tracks = info['total_tracks']
    
    def __str__(self):
        return str({'id': self.id, 'uri': self.uri, 'name': self.name, 'image_url': self.image_url, 
                    'release_date': self.release_date, 'total_tracks': self.total_tracks})

class Track:
    def __init__(self, name, artist, sp: spotipy.Spotify):
        self.sp = sp
        self.id = None
        self.uri = None
        self.album = None
        self.artist = None
        self.popularity = None
        self._get_info(name, artist)
    
    def _get_info(self, name, artist):
        info = self.sp.search(q='artist:' + artist + ' track:' +
                         name, type='track', limit=1)
        track = info['tracks']['items'][0]
        album = Album(track['album'])
        artist = Artist(track['artists'][0])
        self.album = album
        self.artist = artist
        self.id = track['id']
        self.uri = track['uri']
        self.name = track['name']
        self.popularity = track['popularity']
    
    def __str__(self):
        return str({'id': self.id, 'uri': self.uri, 'name': self.name, 'popularity': self.popularity})

class RadioEngine:
    client_id = '44897430b3ff40e1b8e5cebbf31b7989'
    client_secret = '97873e4eca264471b40d1f15de216a82'
    username = 'Iosif Radio'
    scope = "playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative"
    redirect_uri = 'https://iosif.herokuapp.com/'

    tracks = dict()

    def __init__(self):
        client_credentials_manager = spotipy.SpotifyClientCredentials(client_id=self.client_id,
                                                                      client_secret=self.client_secret)

        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        token = spotipy.util.prompt_for_user_token(
            self.username, self.scope, self.client_id, self.client_secret, self.redirect_uri)

        self.sp = spotipy.Spotify(auth=token)

    def add(self, track, artist, server_id):
        self.tracks[server_id] = self.tracks.get(server_id, []) + [Track(track, artist, self.sp)]
    
    def get_recommendation(self, server_id):
        pass