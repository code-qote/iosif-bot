from discord.ext import commands
import discord


async def send_info(ctx, title, message):
    await ctx.send(embed=discord.Embed(title=title, description=message, color=discord.Color.greyple()))


async def send_error(ctx, message):
    await ctx.send(embed=discord.Embed(title=message, color=discord.Color.red()))


async def send_success(ctx, message):
    await ctx.send(embed=discord.Embed(title=message, color=discord.Color.green()))


class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):

        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound, )

        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.ArgumentParsingError):
            await send_error(ctx, 'You did not pass any arguments.')
        elif isinstance(error, commands.ChannelNotFound):
            await send_error(ctx, 'Join any voice channel.')
        elif isinstance(error, commands.MessageNotFound):
            pass
