import discord
import os
from discord import app_commands
from discord.ext import commands
import requests
from discord.ext.commands import Context
from discord import Colour


class Valorant(commands.Cog, name = 'valorant'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name = 'valrank', description = 'Gets valorant rank from id and server (default APAC server)')
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def valrank(self, ctx, riotid, region='ap'):
        name = riotid.split('#')[0]
        hsh = riotid.split('#')[1]
        if not '#' in riotid or region not in ['na', 'eu', 'ap', 'kr']:
            await ctx.send('Invalid account (name#id) or region (na, eu, ap, kr)', delete_after=15)

        response = requests.get(f'https://api.kyroskoh.xyz/valorant/v1/mmr/{region}/{name}/{hsh}')
        if response.status_code == 200:
            rank = response.text[:-1].split(' - ')[0]
            rr = response.text[:-1].split(' - ')[1]
            embed = discord.Embed(
                title=riotid,
                description=f'{rank}\n\n{rr}',
                color=self.rank_color(rank.replace(' ', ''))
            )
            file = discord.File(f'./assets/valranks/{rank.replace(" ", "")}.png', filename=f'{rank.replace(" ", "")}.png')
            embed.set_thumbnail(url=f'attachment://{rank.replace(" ", "")}.png')
            await ctx.send(file = file, embed=embed)
        else:
            await ctx.send('Couldn\'t find that account', delete_after = 10)

    def rank_color(self, rank):
        if 'Iron' in rank:
            return 0xcecfce
        elif 'Bronze' in rank:
            return 0x5d400b
        elif 'Silver' in rank:
            return 0xa4acac
        elif 'Gold' in rank:
            return 0xd1922e
        elif 'Platinum' in rank:
            return 0x3a92a0
        elif 'Diamond' in rank:
            return 0xce91e3
        elif 'Ascendant' in rank:
            return 0x269d60
        elif 'Immortal' in rank:
            return 0xad3670
        elif 'Radiant' in rank:
            return 0xffc76b


async def setup(bot):
    await bot.add_cog(Valorant(bot))
