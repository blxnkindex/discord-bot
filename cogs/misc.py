import discord
import asyncio
from utils import rand_colour, delete_command_message
from discord.ext import commands

import random

class Misc(commands.Cog, name = 'misc'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name = 'flip', description = 'Flip a coin', aliases = ['coinflip', 'flipcoin'])
    async def flip(self, ctx):
        result = random.choice(['Heads', 'Tails'])
        embed = discord.Embed(title=result, colour=rand_colour())
        file = discord.File(f'./assets/coinflip/{result}.png', filename=f'{result}.png')
        embed.set_image(url=f'attachment://{result}.png')
        await ctx.send(file=file, embed=embed)

    @commands.hybrid_command(name = 'rroulette', description = 'Shoot yourself', aliases = ['russian'])
    async def rroulette(self, ctx, *, bullets=None):
        if not bullets:
            bullets = 1
        elif bullets.isdigit():
            bullets = int(bullets)
        if type(bullets) != int:
            await ctx.send(f'Load a whole number of bullets numpty', delete_after=3)
            await delete_command_message(ctx)
        if bullets < 1:
            bullets = 1
        elif bullets > 6:
            bullets = 6
        num = random.randint(1, 6)
        await ctx.send(f'`{ctx.message.author}`:gun: is about to shoot themselves, gun loaded with {bullets} bullet(s)...')
        await asyncio.sleep(2)
        if num <= bullets:
            deathStrs = [' has been blasted. o7', ' exploded with a swift bang.', ' discovered kinetic energy.'
                         ' died. nothing more to it.', ' got hit by a stray.', ' hit the one in six.', ' took the easy way out.']
            await ctx.send(f':boom: `{ctx.message.author}`{random.choice(deathStrs)}')
        else:
            aliveStrs = [' managed to miss somehow.', ' narrowly avoided death.', ' has storm trooper aim.', ' would rather suffer alive.',
                         '\'s face is still intact.', ' is taking the hard way out.', ' has dodged their own bullet.. why\'d they even shoot?']
            await ctx.send(f':dash: `{ctx.message.author}`{random.choice(aliveStrs)}')      

    @commands.hybrid_command(name = 'clean', description = 'Deletes a given number of messages (up to 20 at a time)', aliases = ['purge'])
    async def clean(self, ctx, num=20):
        try:
            int(num)
        except:
            await ctx.send('Usage: >clean [int]', delete_after=10)
        else:
            await ctx.channel.purge(limit=min(num, 20))

    @commands.command(name = ':)', hidden=True)
    async def smile(self, ctx):
        embed = discord.Embed(title='>:)', colour=rand_colour())
        file = discord.File('./assets/smiles/stare.png', filename='stare.png')
        embed.set_image(url='attachment://stare.png')
        
        await ctx.send(file=file, embed=embed)
    
    @commands.command(name = ':(', hidden=True)
    async def frown(self, ctx):
        embed = discord.Embed(title='>:(', colour=rand_colour())
        file = discord.File('./assets/smiles/mad.png', filename='mad.png')
        embed.set_image(url='attachment://mad.png')
        await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))