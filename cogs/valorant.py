import discord
import os
from discord import app_commands
from discord.ext import commands
import requests
import json
import DiscordUtils
import random
from discord.ext.commands import Context

from utils import rank_color, create_scoreboard_embed, get_character, get_map_image, process_team, make_leaderboard_embed

class Valorant(commands.Cog, name = 'valorant'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name = 'pug', description = 'Creates two teams randomly', aliases = ['teams'])
    async def pug(self, ctx, *, players):
        players = players.split()
        if len(players) % 2 != 0:
            await ctx.send('Need even number of players for balanced teams')
            return
        mapname = random.choice(["Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox", "Pearl", "Split", "Lotus"])
        embed = discord.Embed(
            title='Teams', 
            description=f'Map: {mapname}',
            colour=0xFFFFFF
        )
        embed.set_thumbnail(url=get_map_image(mapname))
        random.shuffle(players)
        teamSize = int(len(players)/2)
        embed.add_field(name='Team 1', value=f'```{" ".join(players[:teamSize])}```', inline=False)
        embed.add_field(name='Team 2', value=f'```{" ".join(players[teamSize:])}```', inline=False)
        await ctx.send(embed=embed)


    @commands.hybrid_command(name = 'valrank', description = 'Gets valorant rank from id and server (default APAC server)')
    async def valrank(self, ctx, riotid, region='ap'):
        if not '#' in riotid or region not in ['na', 'eu', 'ap', 'kr']:
            return await ctx.send('Invalid account (name#id, surround with "" if you have spaces in name) or region (na, eu, ap, kr)', delete_after=15)
        name = riotid.split('#')[0]
        tag = riotid.split('#')[1]
        async with ctx.typing():
            response = requests.get(f'https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{name}/{tag}')
        if response.status_code == 200:
            data = json.loads(json.dumps(response.json(), indent=4))['data']
            rank = data['currenttierpatched']
            rr = data['ranking_in_tier']
            elo = data['elo']
            last_game = data['mmr_change_to_last_game']
            if last_game >= 0:
                last_game = '+' + str(last_game)
            rawid = data['name'] + '#' + data['tag']
            embed = discord.Embed(
                title=rawid,
                description=f'{rank}\n{rr}\n\nLast Win/Loss: {last_game}\nMMR/Elo: {elo}',
                color=rank_color(rank.replace(' ', ''))
            )
            file = discord.File(f'./assets/valranks/{rank.replace(" ", "")}.png', filename=f'{rank.replace(" ", "")}.png')
            embed.set_thumbnail(url=f'attachment://{rank.replace(" ", "")}.png')
            await ctx.send(file = file, embed=embed)
        else:
            await ctx.send(f'Couldn\'t find that account return code {response.status_code}', delete_after = 10)

    @commands.hybrid_command(name = 'valhistory', description = 'Gets scoreboard from last 5 most recent games')
    async def valhistory(self, ctx, riotid, region='ap'):
        if not '#' in riotid or region not in ['na', 'eu', 'ap', 'kr']:
            return await ctx.send('Invalid account (name#id, surround with "" if you have spaces in name) or region (na, eu, ap, kr)', delete_after=15)
        name = riotid.split('#')[0]
        tag = riotid.split('#')[1]
        try:
            async with ctx.typing():
                response = requests.get(f'https://api.henrikdev.xyz/valorant/v3/matches/{region}/{name}/{tag}?filter=competitive')
            if response.status_code == 200:
                info = json.loads(json.dumps(response.json(), indent=4))
                if not info['data']:
                    return await ctx.send(f'API returned no games...')
                paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx)
                paginator.add_reaction('⏪', "back")
                paginator.add_reaction('⏩', "next")
                embeds = []
                game_number = 1
                for game in info['data']:
                    embeds.append(create_scoreboard_embed(game, name, tag, game_number))
                    game_number += 1
                await paginator.run(embeds)
            else:
                return await ctx.send(f'API call failed with return code {response.status_code}')
            if response.status_code == 429:
                return await ctx.send(f'Rate limit for API exceeded, wait a few minutes')
        except Exception as e:
            return await ctx.send(f'Error occured: {e}')


    @commands.hybrid_command(name = 'valtop', description = 'Gets server (default APAC) top 10 radiant leaderboard')
    async def valtop(self, ctx, region='ap'):
        if region not in ['na', 'eu', 'ap', 'kr']:
            return await ctx.send('Invalid region (na, eu, ap, kr)', delete_after=15)
        async with ctx.typing():
            response = requests.get(f'https://api.henrikdev.xyz/valorant/v1/leaderboard/{region}')
        if response.status_code == 200:
            info = json.loads(json.dumps(response.json(), indent=4))
            embeds = []
            for i in range(0,500,10):
                embeds.append(make_leaderboard_embed(info, i))
                paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx)
            paginator.add_reaction('⏮️', "first")
            paginator.add_reaction('⏪', "back")
            paginator.add_reaction('⏩', "next")
            paginator.add_reaction('⏭️', "last")
            await paginator.run(embeds)
        else:
            return await ctx.send('Failed to find leaderboard. :(', delete_after=15)

async def setup(bot):
    await bot.add_cog(Valorant(bot))
