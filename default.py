import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from discord import Colour

import random



class Test(commands.Cog, name = 'test'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name = 'test',
        description = 'TESTING'
    )
    @app_commands.guilds(discord.Object(id = 715252385269678241))
    @commands.has_permissions(administrator = True)
    async def test(self, ctx: Context):
        await ctx.send(embed = discord.Embed(
            title='test command', 
            description='Description', 
            colour=rand_colour()
        ))

    @commands.hybrid_command(
        name = 'info',
        description = 'Get some info about the server',
        aliases = ['serverinfo']
    )
    @app_commands.guilds(discord.Object(id = 715252385269678241))
    async def info(self, ctx: Context):
        embed = discord.Embed(
            title=str(ctx.guild.name),
            description=str(ctx.guild),
            colour=rand_colour()
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        embed.add_field(
            name='Server ID',
            value=ctx.guild.id
        )
        embed.add_field(
            name='Members',
            value=ctx.guild.member_count
        )
        embed.add_field(
            name='Channels',
            value=f'{len(ctx.guild.channels)}'
        )
        embed.add_field(
            name='Roles',
            value=len(ctx.guild.roles)
        )
        embed.set_footer(
            text=f'Server Made: {ctx.guild.created_at}'
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name='ping',
        description='Check bot delay',
    )
    @app_commands.guilds(discord.Object(id = 715252385269678241))
    async def ping(self, ctx: Context):
        await ctx.send(embed = discord.Embed(
            title='Ping Received!',
            description=f'Bot delay is {round(self.bot.latency * 1000, 1)}ms.',
            colour=0x00E76D
        ))
    
    @commands.hybrid_command(
        name = 'flip',
        description = 'Flip a coin',
        aliases = ['coinflip']
    )
    @app_commands.guilds(discord.Object(id = 715252385269678241))
    async def flip(self, ctx: Context):
        result = random.choice(['Heads!', 'Tails!'])
        embed = discord.Embed(
            title=result,
            colour=rand_colour()
        )
        if result == 'Heads!':
            embed.set_image(url='https://static.ayana.io/commands/flipcoin/heads.png')
        else:
            embed.set_image(url='https://static.ayana.io/commands/flipcoin/tails.png')
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Test(bot))


# Helpers

def rand_colour():
    return Colour.from_rgb(random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))