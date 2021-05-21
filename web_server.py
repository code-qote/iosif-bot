import os
from aiohttp import web
import discord
from discord.ext import commands, tasks
from consts import MESSAGE_API_TOKEN


app = web.Application()
routes = web.RouteTableDef()


class WebServer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.web_server.start()

        async def send_to_everyone(message):
            embed = discord.Embed(title=message,
                                  color=discord.Color.red()).set_footer(text='From Iosif Team ❤️')
            for guild in bot.guilds:
                await guild.text_channels[0].send(embed=embed)
        
        def _block_command(command_name):
            music = self.bot.get_cog('Music')
            if command_name not in music.blocked_commands:
                music.blocked_commands.append(command_name)
        
        def _unblock_command(command_name):
            music = self.bot.get_cog('Music')
            if command_name in music.blocked_commands:
                music.blocked_commands.remove(command_name)

        @routes.get('/')
        async def index(request):
            return web.Response(status=200)

        @routes.post('/send_message')
        async def send(request):
            json = await request.json()
            token = json.get('token')
            if token == MESSAGE_API_TOKEN:
                if json.get('message'):
                    await send_to_everyone(json['message'])
                    return web.Response(status=200)
            return web.Response(status=401)
        
        @routes.get('/commands')
        async def get_commands(request):
            json = await request.json()
            token = json.get('token')
            if token == MESSAGE_API_TOKEN:
                commands = self.bot.commands
                blocked_commands = self.bot.get_cog('Music').blocked_commands
                return web.json_response({'commands': sorted([i.name for i in list(commands)]), 'blocked_commands': [i.strip('_') for i in blocked_commands]})
            return web.Response(status=401)
        
        @routes.post('/block_command')
        async def block(request):
            json = await request.json()
            token = json.get('token')
            if token == MESSAGE_API_TOKEN:
                if json.get('message'):
                    _block_command(json['message'])
                    return web.Response(status=200)
            return web.Response(status=401)
        
        @routes.post('/unblock_command')
        async def unblock(request):
            json = await request.json()
            token = json.get('token')
            if token == MESSAGE_API_TOKEN:
                if json.get('message'):
                    _unblock_command(json['message'])
                    return web.Response(status=200)
            return web.Response(status=401)

        self.webserver_port = os.environ.get('PORT', 5000)
        # self.webserver_port = os.environ.get('PORT', 8080)
        app.add_routes(routes)     

    @tasks.loop()
    async def web_server(self):
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host='0.0.0.0', port=self.webserver_port)
        await site.start()

    @web_server.before_loop
    async def web_server_before_loop(self):
        await self.bot.wait_until_ready()
