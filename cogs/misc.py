import discord
import os
from utils import rand_colour
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

import random

class Misc(commands.Cog, name = 'misc'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name = 'flip', description = 'Flip a coin', aliases = ['coinflip', 'flipcoin'])
    async def flip(self, ctx: Context):
        result = random.choice(['Heads', 'Tails'])
        embed = discord.Embed(title=result, colour=rand_colour())
        file = discord.File(f'./assets/coinflip/{result}.png', filename=f'{result}.png')
        embed.set_image(url=f'attachment://{result}.png')
        await ctx.send(file=file, embed=embed)

    @commands.command(name = ':)', hidden=True)
    async def smile(self, ctx: Context):
        embed = discord.Embed(title='>:)', colour=rand_colour())
        file = discord.File('./assets/smiles/stare.png', filename='stare.png')
        embed.set_image(url='attachment://stare.png')
        
        await ctx.send(file=file, embed=embed)
    
    @commands.command(name = ':(', hidden=True)
    async def frown(self, ctx: Context):
        embed = discord.Embed(title='>:(', colour=rand_colour())
        file = discord.File('./assets/smiles/mad.png', filename='mad.png')
        embed.set_image(url='attachment://mad.png')
        await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))