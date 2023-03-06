import random
from discord import Colour
import discord
import asyncio

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
        players.append(p)
    players = sorted(players, key=lambda p: p['acs'], reverse=True) 
    scoreboard = []
    for p in players:
        gap = '                 '
        gap2 = '         '
        offset1 = len(p['name'])
        offset2 = len(p['kda'])
        offset3 = len(p['hs']) + 5
        scoreboard.append(f'{p["name"]}{gap[offset1:]}{p["kda"]}{gap2[offset2:]}HS: {p["hs"]}%{gap2[offset3:]}ACS: {p["acs"]}')
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