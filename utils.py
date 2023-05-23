import random
from discord import Colour
import discord
import asyncio
import requests
import json
import datetime
import numpy
import os

'''
Generates a random Colour
'''
def rand_colour():
    return Colour.from_rgb(random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))



'''
Music Helpers
'''
# YTDL download options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'playliststart': 1,
    'playlistend': 21,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

# Options for ffmpeg processes

# Reconnect options prevent corrupt 
# packets from force skipping a song
# Source: https://stackoverflow.com/questions/66070749/ 
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

async def player_delay(ctx):
    ctx.voice_client.pause()
    await asyncio.sleep(1)
    ctx.voice_client.resume()

async def delete_command_message(ctx):
    if ctx.message.content.startswith('>'):
        await asyncio.sleep(5)
        await ctx.message.delete()

def get_song_data(info, requester):
    song = {}
    song['title'] = info['title']
    song['webpage_url'] = info['webpage_url']
    song['tn'] = info['thumbnail']
    song['duration'] = info['duration']
    song['requester'] = requester
    return song

def create_song_embed(song, title):
    embed = discord.Embed(
        title=title,
        description=song['title']  + f'\n\nrequested by `{song["requester"]}`',
        colour=rand_colour()
    )
    embed.set_thumbnail(url=song['tn'])
    embed.set_footer(text=f'{int(song["duration"] / 60)} minutes {int(song["duration"] % 60)} seconds')
    return embed

'''
Valorant Cog Helper Functions
'''
def rank_color(rank):
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

def create_scoreboard_embed(game, name, tag, game_number):
    mapname = game['metadata']['map']
    if game['teams']['red']['has_won']:
        win_team = 'red'
        lose_team = 'blue'
        win_rounds = game['teams']['red']['rounds_won']
        lose_rounds = game['teams']['blue']['rounds_won']
    else:
        win_team = 'blue'
        lose_team = 'red'
        win_rounds = game['teams']['blue']['rounds_won']
        lose_rounds = game['teams']['red']['rounds_won']
    embed = discord.Embed(
        title=f'Game {game_number}',
        description=f'Character Played: {get_character(game["players"]["all_players"], name, tag)}',
        color=rand_colour()
    )
    embed.set_thumbnail(url=get_map_image(mapname))
    winners = '\n'.join(process_team(game['players'][win_team], game['metadata']['rounds_played']))
    losers = '\n'.join(process_team(game['players'][lose_team], game['metadata']['rounds_played']))
    embed.add_field(name=mapname, 
        value=f'```>>> Winning Team <<<  - {win_rounds}\n{winners}\n>>> Losing Team <<<   - {lose_rounds}\n{losers}\n```', inline=False)
    return embed

def makeQuickHistoryEmbed(info, start):
    color = rank_color(info["data"][start]["currenttierpatched"].replace(" ", ""))
    embed = discord.Embed(title=f'{info["name"]}#{info["tag"]}', color=color)
    for i in range(start, min(start + 5, len(info['data']))):
        game = info['data'][i]
        timePlayed = datetime.datetime.fromtimestamp(game['date_raw'])

        rankString = str(game['currenttierpatched']) + ' ' + str(int(game['ranking_in_tier']) - int(game['mmr_change_to_last_game']))+'rr' + ' --> ' + str(game['ranking_in_tier']) + 'rr' + ' Net elo: ' + str(game['mmr_change_to_last_game'])
        embed.add_field(name=timePlayed.strftime("%A, %B %d, %H:%M"), value=f'```{rankString}```', inline=False)
        
    return embed

def get_character(players, name, tag):
    for p in players:
        if (name.lower().replace(' ', '') == p['name'].lower().replace(' ', '')) and (tag.lower() == p['tag'].lower()):
            return p['character']
    return 'Character not found'

def get_map_image(mapname):
    if mapname == 'Ascent':
        return 'https://static.wikia.nocookie.net/valorant/images/e/e7/Loading_Screen_Ascent.png/revision/latest?cb=20200607180020'
    elif mapname == 'Bind':
        return 'https://static.wikia.nocookie.net/valorant/images/2/23/Loading_Screen_Bind.png/revision/latest?cb=20200620202316'
    elif mapname == 'Breeze':
        return 'https://static.wikia.nocookie.net/valorant/images/1/10/Loading_Screen_Breeze.png/revision/latest?cb=20210427160616'
    elif mapname == 'Fracture':
        return 'https://static.wikia.nocookie.net/valorant/images/f/fc/Loading_Screen_Fracture.png/revision/latest?cb=20210908143656'
    elif mapname == 'Haven':
        return 'https://static.wikia.nocookie.net/valorant/images/7/70/Loading_Screen_Haven.png/revision/latest?cb=20200620202335'
    elif mapname == 'Icebox':
        return 'https://static.wikia.nocookie.net/valorant/images/1/13/Loading_Screen_Icebox.png/revision/latest?cb=20201015084446'
    elif mapname == 'Pearl':
        return 'https://static.wikia.nocookie.net/valorant/images/a/af/Loading_Screen_Pearl.png/revision/latest?cb=20220622132842'
    elif mapname == 'Split':
        return 'https://static.wikia.nocookie.net/valorant/images/d/d6/Loading_Screen_Split.png/revision/latest?cb=20200620202349'
    elif mapname == 'Lotus':
        return 'https://static.wikia.nocookie.net/valorant/images/d/d0/Loading_Screen_Lotus.png/revision/latest?cb=20230106163526'

def process_team(team, rounds):
    players = []
    for player in team:
        kda = f'{player["stats"]["kills"]}/{player["stats"]["deaths"]}/{player["stats"]["assists"]}'
        if (player["stats"]["headshots"] + player["stats"]["bodyshots"] + player["stats"]["legshots"]) > 0:
            hs = player["stats"]["headshots"]/(player["stats"]["headshots"] + player["stats"]["bodyshots"] + player["stats"]["legshots"])
        else:
            hs = 0
        p = {}
        p['name'] = player['name']
        p['kda'] = kda
        p['hs'] = str(round(hs*100))
        p['acs'] = round(player['stats']['score'] / rounds)
        if player['currenttier_patched'][0] == 'U':
            p['currenttier_patched'] = 'None'
        elif player['currenttier_patched'][0] == 'R':
            p['currenttier_patched'] = player['currenttier_patched'][0] + player['currenttier_patched'][1] + player['currenttier_patched'][2]
        else:
            p['currenttier_patched'] = player['currenttier_patched'][0] + player['currenttier_patched'][1] + player['currenttier_patched'][2] + ' ' + player['currenttier_patched'][-1]

        players.append(p)
    players = sorted(players, key=lambda p: p['acs'], reverse=True) 
    scoreboard = []
    for p in players:
        gap = '                 '
        gap2 = '        '
        gap3 = '   ' if (len(p['hs']) == 1) else '  '
        gap4 = '   '
        offset1 = 0
        for c in range(0,len(p['name'])):
            offset1 += 1 if p['name'][c].isascii() else 2
        offset1 = min(offset1, 16)
        offset2 = len(p['kda'])
        offset3 = len(str(p['acs']))
        scoreboard.append(f'{p["name"]}{gap[offset1:]}{p["kda"]}{gap2[offset2:]} {p["hs"]}%{gap3}{p["acs"]}{gap4[offset3:]}  {p["currenttier_patched"]}')
    return scoreboard

def make_leaderboard_embed(info, index):
    players = []
    for index in range(index, index + 10):
        p = info[index]
        if not  p['IsAnonymized']:
            name = f'{p["leaderboardRank"]}: ' + p['gameName'] + '#' + p['tagLine']
        else:
            name = f'{p["leaderboardRank"]}: ' + '*Hidden Name*'
        rr = f' RR: {p["rankedRating"]}'
        wins = f'Wins: {p["numberOfWins"]}'
        gap = '                          '[len(name):] 
        gap2 = '          '[len(rr):]
        players.append(f'{name}{gap}{rr}{gap2}{wins}')
    embed = discord.Embed(
        title='Top 500 Radiant',
        color=rand_colour()
    )
    players = '\n'.join(players)
    embed.add_field(name=f'Rank {index - 8} to {index + 1}',value=f'```{players}```', inline=False)
    return embed

def calcVariance(region, name, tag):
    response = requests.get(f'https://api.henrikdev.xyz/valorant/v1/mmr-history/{region}/{name}/{tag}')
    if response.status_code == 200:
        info = json.loads(json.dumps(response.json(), indent=4))
        wins = []
        losses = []
        for game in info['data']:
            if game['mmr_change_to_last_game'] > 0:
                wins.append(game['mmr_change_to_last_game'])
            elif game['mmr_change_to_last_game'] < 0:
                losses.append(game['mmr_change_to_last_game'])
        if len(wins) == 0 and len(losses) == 0:
            return 0
        avgWin = 0 if (len(wins) == 0) else sum(wins)/len(wins)
        avgLoss = 1 if (len(losses) == 0) else sum(losses)/len(losses)
        return round((avgWin + avgLoss),2)

def createMmrEmbed(hiddenElo, rawElo, variance, name):
    eloGap = hiddenElo - rawElo
    if eloGap > -50 and eloGap < 50:
        desc1 = f'Your average game mmr is close to your actual elo, difference of `{eloGap}`. \n\n(Actual elo `{rawElo}`, Avg Game MMR: `{hiddenElo}`).'
    elif eloGap < 0:
        desc1 = f'Your average game mmr is `{eloGap}`' + f' compared to your actual elo \n\n(Actual elo `{rawElo}`, Avg Game MMR: `{hiddenElo}`).'
    elif eloGap > 0:
        desc1 = f'Your average game mmr is `{eloGap}`' + f' above your actual elo \n\n(Actual elo `{rawElo}`, Avg Game MMR: `{hiddenElo}`)'
    color = getMmrEmbedDetails(variance)[1]
    desc2 = getMmrEmbedDetails(variance)[0]
    if eloGap > 100 and variance > 1:
        color = Colour.from_rgb(0,255,255)


    embed = discord.Embed(title=f'MMR Report for {name}', description=desc1 +'\n\n' + desc2, color=color)
    embed.set_footer(text=f'Use command \'>valmmrhelp\' for more info.')
    return embed

def getMmrEmbedDetails(variance):
    if variance > 10:
        color = Colour.from_rgb(0,255,255)
        desc2 =  f'Your hidden mmr is very good, with a variance of `{variance}`. \nYou are likely the highest rank on your teams/games and either not at your old rank or at a recent peak.'
    elif variance > 5 and variance <= 10:
        color = Colour.from_rgb(0,255,0)
        desc2 =  f'You have strong variance of `{variance}`, maintaining this mmr will result in positive climb. \nYou have good mmr and likely expected (by the game) to win most your games.'
    elif variance > 1 and variance <= 5:
        color = Colour.from_rgb(0,255,0)
        desc2 = f'You are getting above average gains and losses (Variance of `{variance}`)'
    elif variance > -1 and variance <= 1:
        color = Colour.from_rgb(255,255,0)
        desc2 = f'You are getting similar gains and losses (Variance of `{variance}`)'
    elif variance <= -1:
        color = Colour.from_rgb(255,0,0)
        desc2 = f'You are getting below average gains and losses (Variance of `{variance}`)'
    return (desc2, color)

def parseElo(rank):
        variance = random.randint(-49,49)
        if 'Iron' in rank:
            elo = 50
            elo += (int(rank.split(' ')[1]) - 1) * 100
        elif 'Bronze' in rank:
            elo = 350
            elo += (int(rank.split(' ')[1]) - 1) * 100
        elif 'Silver' in rank:
            elo = 650
            elo += (int(rank.split(' ')[1]) - 1) * 100
        elif 'Gold' in rank:
            elo = 950
            elo += (int(rank.split(' ')[1]) - 1) * 100
        elif 'Platinum' in rank:
            elo = 1250
            elo += (int(rank.split(' ')[1]) - 1) * 100
        elif 'Diamond' in rank:
            elo = 1550
            elo += (int(rank.split(' ')[1]) - 1) * 100
        elif 'Ascendant' in rank:
            elo = 1850
            elo += (int(rank.split(' ')[1]) - 1) * 100
        elif 'Immortal 1' in rank:
            elo = 2140
        elif 'Immortal 2' in rank:
            elo = 2240
        elif 'Immortal 3' in rank:
            elo = 2450
            variance = random.randint(-40,80)
        elif 'Radiant' in rank:
            elo = 2750
            variance = random.randint(-100,200)
        else:
            return -1
        return elo + variance
    
'''
Casino Utils
'''

def resetDeck():
    return ['2_clu', '2_dia', '2_hea', '2_spa', '3_clu', '3_dia', '3_hea', '3_spa', '4_clu', '4_dia', '4_hea', '4_spa', '5_clu', '5_dia', '5_hea', '5_spa', '6_clu', '6_dia', '6_hea', '6_spa', '7_clu', '7_dia', '7_hea', '7_spa', '8_clu', '8_dia', '8_hea', '8_spa', '9_clu', '9_dia', '9_hea', '9_spa', '10_clu', '10_dia', '10_hea', '10_spa','J_clu', 'J_dia', 'J_hea', 'J_spa', 'Q_clu', 'Q_dia', 'Q_hea', 'Q_spa', 'K_clu', 'K_dia', 'K_hea', 'K_spa','A_clu', 'A_dia', 'A_hea', 'A_spa']

def parseCards(card):
    if card == 'hidden':
        return 'Hidden Card'
    num = card.split('_')[0]
    suit = card.split('_')[1]
    s = ''
    if num == 'A':
        s += 'Ace'
    elif num == 'K':
        s += 'King'
    elif num == 'Q':
        s += 'Queen'
    elif num == 'J':
        s += 'Jack'
    else:
        s += num
    s += ' of '
    if suit == 'clu':
        s += 'Clubs'
    elif suit == 'dia':
        s += 'Diamonds'
    elif suit == 'hea':
        s += 'Hearts'
    elif suit == 'spa':
        s += 'Spades'
    return s

def getPlayerBalance(uid):
    with open(os.getenv('PLAYER_BAL'), "r") as f:
        balances =  json.load(f)
    if uid == 'casino':
        return balances['casino']
    if str(uid) in balances and balances[str(uid)] >= 0:
        return balances[str(uid)]
    elif str(uid) in balances and balances[str(uid)] <= 0:
        return -1
    elif not str(uid) in balances:
        return -21
    return False

def updatePlayerBalance(uid, newBal):
    with open(os.getenv('PLAYER_BAL'), "r") as f:
        balances =  json.load(f)
    balances[str(uid)] = newBal 
    with open(os.getenv('PLAYER_BAL'), "w") as f:
        json.dump(balances, f)
    print(f'updated {uid} to {newBal}')

async def ensureAmount(ctx, amount):
    balance = getPlayerBalance(ctx.message.author.id)
    print(balance)
    if balance == 0:
        await ctx.send(f'You have no dollars left brokie')
        return False
    if balance == -21:
        await ctx.send(f'`{ctx.message.author}` is new to the casino, they are given 5000 dollars starting balance.')
        balance = 5000
        updatePlayerBalance(ctx.message.author.id, 5000)
    if (balance - amount) < 0:
        await ctx.send(f'You have {balance}, not enough to use {amount}')
        return False
    return balance

async def ensureRouletteInput(ctx, bet, amount):
    if not bet or not amount:
        await ctx.send('Usage: >roulette red/black/green/high/low/[0-15] betAmount')
        return False
    if amount.isdigit():
        amount = int(amount)
    if bet.isdigit():
        bet = int(bet)
    if type(amount) != int:
        await ctx.send('Bet amount needs to be a whole number')
        return False
    if type(bet) == str :
        if bet not in ['red', 'black', 'green', 'high', 'low']:
            await ctx.send('Bet type can be red, black, green, high (8-14), low (1-7) or a specific number 0-14')
            return False
    elif type(bet) == int and bet < 0 or bet > 14:
        await ctx.send('Bet type can be red, black, green, high (8-14), low (1-7) or a specific number 0-14')
        return False
    return True

async def rollRoulette(ctx):
    r = ':red_square:'
    b = ':black_large_square:'
    g = ':green_square:'
    w = ':white_large_square:'
    table = [g,b,r,b,r,b,r,b,r,b,r,b,r,b,r]
    table = numpy.roll(table, random.randint(0, 14))

    msg = await ctx.send(f'Rolling...')
    rollTime = 0
    maxRollTime = random.uniform(2.5, 4.5)
    increment = 0.5
    while rollTime < maxRollTime:
        table = numpy.roll(table, 1)
        await msg.edit(content=f'Rolling... {int(maxRollTime - rollTime)}\r\n{w}{w}{w}{w}{w}:arrow_down_small:{w}{w}{w}{w}{w}\
                    \r\n{w}{table[0]}{table[1]}{table[2]}{table[3]}{table[4]}{table[5]}{table[6]}{table[7]}{table[8]}{w}\
                    \r\n{w}{w}{w}{w}{w}:arrow_up_small:{w}{w}{w}{w}{w}')
        await asyncio.sleep(increment)
        rollTime += increment
        if rollTime > 1 and rollTime < 2:
            increment = 0.65
        elif rollTime > 2:
            increment = 0.85
    await asyncio.sleep(random.uniform(0.2, 0.6))
    table = numpy.roll(table, 1)
    await msg.edit(content=f'Finished!\r\n{w}{w}{w}{w}{w}:arrow_down_small:{w}{w}{w}{w}{w}\
                    \r\n{w}{table[0]}{table[1]}{table[2]}{table[3]}{table[4]}{table[5]}{table[6]}{table[7]}{table[8]}{w}\
                    \r\n{w}{w}{w}{w}{w}:arrow_up_small:{w}{w}{w}{w}{w}')
    return table