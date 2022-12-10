import discord
import os
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from discord import Colour

import random

class Default(commands.Cog, name = 'default'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name='help',
        description='List all bot commands'
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def help(self, ctx):
        embed = discord.Embed(
            title='Help 💬',
            description='Available commands:',
            color=0xFFFFF
        )

        for i in self.bot.cogs:
            cmds = []
            for command in self.bot.get_cog(i.lower()).get_commands():
                description = command.description.partition('\n')[0]
                cmds.append(f'>{command.name}: {description}')
                cmd = "\n".join(cmds)
            embed.add_field(name=i.capitalize() + 'commands',
                            value=f'```{cmd}```', inline=False)

        await ctx.send(embed=embed)


    @commands.hybrid_command(
        name = 'info',
        description = 'Get some info about the server',
        aliases = ['serverinfo']
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def info(self, ctx):
        embed = discord.Embed(
            title=str(ctx.author),
            description=str(ctx.guild.name),
            colour=rand_colour()
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        embed.add_field(name='Server ID', value=ctx.guild.id)
        embed.add_field(name='Members', value=ctx.guild.member_count)
        embed.add_field(name='Channels', value=f'{len(ctx.guild.channels)}')
        embed.add_field(name='Roles', value=len(ctx.guild.roles))
        embed.set_footer(text=f'Server Made: {ctx.guild.created_at}')
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name='ping',
        description='Check bot delay',
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def ping(self, ctx):
        await ctx.send(f'🏓 Pong! Latency is `{round(self.bot.latency * 1000, 1)}ms`')

async def setup(bot):
    await bot.add_cog(Default(bot))

# Helpers
def rand_colour():
    return Colour.from_rgb(random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))