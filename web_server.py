import os
from aiohttp import web
import discord
from discord.ext import commands, tasks
from consts import MESSAGE_API_TOKEN


app = web.Application()
routes = web.RouteTableDef()


class WebServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.web_server.start()

        async def send_to_everyone(message):
            embed = discord.Embed(title=message,
                                  color=discord.Color.red()).set_footer(text='From Iosif Team ❤️')
            for guild in bot.guilds:
                await guild.text_channels[0].send(embed=embed)

        @routes.post('/send_message')
        async def respond(request):
            json = await request.json()
            token = json.get('token')
            if token == MESSAGE_API_TOKEN:
                if json.get('message'):
                    await send_to_everyone(json['message'])
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
