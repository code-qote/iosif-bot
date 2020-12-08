import discord
from discord.ext import commands
import asyncio
from api import *
from consts import *
from youtube import YTDLSource


playlists = dict()


class PlaylistMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def pnew(self, ctx, *, keyword):
        '''[playlist name] - create new playlist'''
        user_id = ctx.message.author.id
        add_user(user_id)
        if add_playlist(user_id, keyword)['success']:
            await ctx.send(f'Playlist {keyword} created!')
        else:
            await ctx.send('Error!')
    
    @commands.command()
    async def playlists(self, ctx):
        '''show all your playlists'''
        user_id = ctx.message.author.id
        add_user(user_id)
        playlists = playlist_list(user_id)
        if playlists['exist']:
            text = '\n'.join([f"{i + 1}. {playlist}" for i, playlist in enumerate(playlists['playlists'])])
        else:
            text = 'There are not any playlists'
        await ctx.send(text)
    
    @commands.command()
    async def popen(self, ctx, *, keyword):
        '''open playlist'''
        user_id = ctx.message.author.id
        server_id = ctx.message.guild.id
        playlist = get_playlist_by_user_id_and_name(user_id, keyword)
        if playlist['exist']:
            playlists[server_id] = {'id': playlist['id'], 'position': 1}
            await self.plist(ctx)
        else:
            ctx.send('There are not such playlists')
    
    @commands.command()
    async def plist(self, ctx):
        '''show all songs in playlist'''
        playlist_id = playlists.get(ctx.message.guild.id, False)
        if playlist_id:
            songs = songs_list_from_playlist(playlist_id['id'])
            if songs:
                text = '\n'.join([f"{song['position']}. {song['request']}" for i, song in enumerate(sorted(songs, key=lambda x: x['position']))])
            else:
                text = 'Playlist is empty'
            await ctx.send(text)
        else:
            await ctx.send('There are not opened playlists')
    
    @commands.command()
    async def padd(self, ctx, *, keyword):
        '''[song name] - add song'''
        playlist_id = playlists.get(ctx.message.guild.id, False)
        if playlist_id:
            add_song(keyword)
            add_song_to_playlist(keyword, playlist_id['id'])
            await self.plist(ctx)
        else:
            await ctx.send('There are not opened playlists')
    
    @commands.command()
    async def pdel(self, ctx, *, keyword):
        '''[song position] - remove song in position'''
        playlist_id = playlists.get(ctx.message.guild.id, False)
        if playlist_id:
            try:
                if not remove_song_from_playlist(playlist_id['id'], int(keyword))['success']:
                    await ctx.send('Error')
                else:
                    await self.plist(ctx)
            except ValueError:
                await ctx.send('Argument must be integer')
        else:
            await ctx.send('There are not opened playlists') 

    @commands.command()
    async def pclear(self, ctx):
        '''clear queue'''
        playlist_id = playlists.get(ctx.message.guild.id, False)
        if playlist_id:
            clear_playlist(playlist_id['id'])
            await self.plist(ctx)
        else:
            await ctx.send('There are not opened playlists')
    
    @commands.command()
    async def pnext(self, ctx):
        '''next song'''
        playlist_id = playlists.get(ctx.message.guild.id, False)
        if playlist_id:
            await self.play_next(ctx)
        else:
            await ctx.send('There are not opened playlists')
    
    @commands.command()
    async def pprev(self, ctx):
        '''previous song'''
        playlist_id = playlists.get(ctx.message.guild.id, False)
        if playlist_id:
            await self.play_previous(ctx)
        else:
            await ctx.send('There are not opened playlists')
    
    @commands.command()
    async def pjump(self, ctx, *, keyword):
        '''[song position] - jump to position in playlist'''
        server_id = ctx.message.guild.id
        playlist_id = playlists.get(server_id, False)
        if playlist_id:
            try:
                position = int(keyword)
                last_pos = playlists[server_id]['position']
                playlists[server_id]['position'] = position
                request = get_song_from_playlist(playlists[server_id])
                if request:
                    await self.pplay(ctx)
                else:
                    playlists[server_id]['position'] = last_pos
                    await ctx.send('Error')
            except ValueError:
                await ctx.send('Argument must be integer')
        else:
            await ctx.send('There are not opened playlists')

    async def play_previous(self, ctx):
        server_id = ctx.message.guild.id
        playlists[server_id]['position'] -= 1
        if playlists[server_id]['position'] == 0:
            playlists[server_id]['position'] = 1
            await ctx.send('This is the first song')
        else:
            request = get_song_from_playlist(playlists[server_id])
            if request:
                await self.pplay(ctx)
            else:
                await ctx.send('Error')

    async def play_next(self, ctx):
        server_id = ctx.message.guild.id
        print(playlists[server_id])
        playlists[server_id]['position'] += 1
        request = get_song_from_playlist(playlists[server_id])
        if request:
            await self.pplay(ctx)
        elif not request and playlists[server_id]['position'] == 1:
            await ctx.send('Playlist is clear')
        else:
            playlists[server_id]['position'] = 0
            await self.play_next(ctx)
    
    @commands.command()
    async def pplay(self, ctx):
        '''play playlist'''
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
        async with ctx.typing():
            server_id = ctx.message.guild.id
            playlist_id = playlists.get(ctx.message.guild.id, False)
            if playlist_id:
                request = get_song_from_playlist(playlists[server_id])
                if not request:
                    await ctx.send('Playlist is clear')
                else:
                    player = await YTDLSource.from_url(request, loop=self.bot.loop)
                    if player:
                        ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
                await ctx.send('Now playing: {}'.format(player.title))
            else:
                await ctx.send('There are not opened playlists')
