import discord
import os
from default import rand_colour
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

import random

class Misc(commands.Cog, name = 'misc'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name = 'pug',
        description = 'Creates two teams randomly',
        aliases = ['maketeam', 'teams']
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def pug(self, ctx, *, players):
        players = players.split()
        if len(players) % 2 != 0:
            await ctx.send('Need even number of players for balanced teams')
            return
        embed = discord.Embed(
            title='Teams', 
            description=f'Players: {" ".join(players)}', 
            colour=0xFFFFFF
        )
        random.shuffle(players)
        teamSize = int(len(players)/2)
        embed.add_field(name='Team 1', value=f'```{" ".join(players[:teamSize])}```', inline=False)
        embed.add_field(name='Team 2', value=f'```{" ".join(players[teamSize:])}```', inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name = 'flip',
        description = 'Flip a coin',
        aliases = ['coinflip', 'flipcoin']
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def flip(self, ctx: Context):
        result = random.choice(['Heads!', 'Tails!'])
        embed = discord.Embed(
            title=result,
            colour=rand_colour()
        )
        if result == 'Heads!':
            embed.set_image(url='https://cdn.discordapp.com/attachments/1050680252453625886/1050707443677675570/heads.png')
        else:
            embed.set_image(url='https://cdn.discordapp.com/attachments/1050680252453625886/1050707443283415060/tails.png')
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))
