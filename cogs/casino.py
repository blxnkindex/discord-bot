import discord
import asyncio
import numpy
from discord import Colour
from utils import rand_colour, delete_command_message
from discord.ext import commands
from discord.ext.commands import Context

import random

class Casino(commands.Cog, name = 'casino'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name = 'roulette', description = 'Play roulette')
    async def roulette(self, ctx, bet=None, amount=None):
        if not bet or not amount:
            return await ctx.send('Usage: >roulette red/black/green/high/low/[0-15]] betAmount')
        if amount.isdigit():
            amount = int(amount)
            print(amount)
        if bet.isdigit():
            bet = int(bet)
            print(bet)
        if type(amount) != int:
            return await ctx.send('Bet amount needs to be a whole number')
        if type(bet) == str :
            if bet not in ['red', 'black', 'green', 'high', 'low']:
                return await ctx.send('Bet type can be red, black, green, high (8-14), low (1-7) or a specific number 0-14')
        elif bet.isdigit() and bet < 0 or bet > 15:
            return await ctx.send('Bet type can be red, black, green, high (8-14), low (1-7) or a specific number 0-14')

        r = ':red_square:'
        b = ':black_large_square:'
        g = ':green_square:'
        w = ':white_large_square:'
        table = [g,b,r,b,r,b,r,b,r,b,r,b,r,b,r,]
        table = numpy.roll(table, random.randint(0, 14))

        msg = await ctx.send(f'Rolling...')
        rollTime = 0
        maxRollTime = random.uniform(3.5, 5)
        increment = 0.5
        while rollTime < maxRollTime:
            table = numpy.roll(table, 1)
            await msg.edit(content=f'Rolling... {int(maxRollTime - rollTime)}\r\n{w}{w}{w}{w}{w}:arrow_down_small:{w}{w}{w}{w}{w}\
                        \r\n{w}{table[0]}{table[1]}{table[2]}{table[3]}{table[4]}{table[5]}{table[6]}{table[7]}{table[8]}{w}\
                        \r\n{w}{w}{w}{w}{w}:arrow_up_small:{w}{w}{w}{w}{w}')
            await asyncio.sleep(increment)
            print(f'rollTime: {rollTime}')
            rollTime += increment
            if rollTime > 1 and rollTime < 2:
                increment = 0.65
            elif rollTime > 2:
                increment = 0.85
        await asyncio.sleep(random.uniform(0.5, 1))
        table = numpy.roll(table, 1)
        await msg.edit(content=f'Finished!\r\n{w}{w}{w}{w}{w}:arrow_down_small:{w}{w}{w}{w}{w}\
                        \r\n{w}{table[0]}{table[1]}{table[2]}{table[3]}{table[4]}{table[5]}{table[6]}{table[7]}{table[8]}{w}\
                        \r\n{w}{w}{w}{w}{w}:arrow_up_small:{w}{w}{w}{w}{w}')
        color = 'none'
        if table[4] == g:
            num = 0
            color = 'green'
            embedColor = Colour.from_rgb(0,255,0)
        elif table[4] == r:
            num = random.randint(1,7) * 2
            color = 'red'
            embedColor = Colour.from_rgb(255,0,0)
        elif table[4] == b:
            num = random.randint(1,7) * 2 - 1
            color = 'black'
            embedColor = Colour.from_rgb(0,0,0)
        

        if type(bet) == str:
            if bet == 'green' and bet == color:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 14}`'
            elif (bet == 'red' or bet == 'black') and bet == color:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 2}`'
            elif bet == 'high' and num >= 8:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 2}`'
            elif bet == 'low' and num >= 8:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 2}`'
            else:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` and lost `{amount}`'
        elif type(bet) == int:
            if num == bet:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` with `{amount}` and wins `{amount * 14}`'
            else:
                resultStr = f'`{ctx.message.author}` bet on `{bet}` and lost `{amount}`'
        
        embed = discord.Embed(
            title=f'{table[4]}: {num}',
            description=resultStr,
            colour=embedColor
        )
        embed.set_footer(text=f'Your remaining coins: Database not implemented, will add unique user balance soon(tm)')
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Casino(bot))