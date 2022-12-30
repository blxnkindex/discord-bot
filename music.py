import asyncio
import os

import discord
import youtube_dl
import random
from default import rand_colour
from discord import app_commands

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''



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


# Reconnect options prevent corrupt 
# packets from force skipping a song
# Source: https://stackoverflow.com/questions/66070749/
ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

'''
Instances created for each requested song
Source: https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py
'''
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.33):
        super().__init__(source, volume)

        self.data = data
        # Song data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def source(cls, song, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(song['webpage_url'], download=False))

        # This should never be necessary
        if 'entries' in data:
            print('entries are in data which shouldn\'t be possible')
            data = data['entries'][0]

        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data=data)

'''
Main cog for music commands
'''
class Music(commands.Cog, name = 'music'):
    def __init__(self, bot):
        self.bot = bot
        self.current = None
        self.queue = []

    @commands.hybrid_command(name = 'join', description = 'Joins your voice channel')
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def join(self, ctx):
        if not ctx.message.author.voice:
            return await ctx.send('You are not connected to a voice channel.', delete_after=10)
        channel = ctx.message.author.voice.channel
        if not channel:
            return await ctx.send('You are not connected to a voice channel.', delete_after=10)
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()
        await self.delete_command_message(ctx)

    @commands.hybrid_command(name = 'play', description = 'Plays/searches youtube for a song', aliases = ['p'])
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def play(self, ctx, *, search):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return await ctx.send('You are not connected to a voice channel.', delete_after=10)

        response = await song_search(search, ctx.message.author, loop=self.bot.loop)
        song = response['songs'].pop(0)
        if not ctx.voice_client.is_playing():
            player = await YTDLSource.source(song, loop=self.bot.loop)
            async with ctx.typing():
                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
                await self.player_delay(ctx)
            self.current = song
            await ctx.send(embed = self.create_song_embed(song, '🎵  Now Playing:'))
        else:
            self.queue.append(song)
            await ctx.send(embed = self.create_song_embed(song, '⏳ Queued:'))
        if response['songs']:
            for i in response['songs']:
                self.queue.append(i)
            await ctx.send(f'Queued {len(response["songs"])} songs from {response["pl_name"]}')

        await self.delete_command_message(ctx)

    async def play_next(self, ctx):
        song = self.queue.pop(0)
        player = await YTDLSource.source(song, loop=self.bot.loop)
        self.current = song
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        await self.player_delay(ctx)
        await ctx.send(embed = self.create_song_embed(song, '🎵  Now Playing:'))


    @commands.hybrid_command(name = 'queue', description = 'Displays the next 10 songs in queue', aliases = ['q'])
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def queue(self, ctx):
        embed = discord.Embed(title='Queue 🎵', colour=rand_colour())
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            self.current = None
        if self.current:
            embed.add_field(name='Current Song', value=f'```{self.current["title"]}```', inline=False)
            embed.set_thumbnail(url=self.current["tn"])
            songs = []
            for i in range(min(len(self.queue), 10)):
                songs.append(str(self.queue[i]['title']))
            if len(songs) == 0:
                text = 'Empty. Add more songs with >play'
            else:
                text = '\n\n'.join(songs)
            embed.add_field(name='Queue', value=f'```{text}```')
            embed.set_footer(text=self.queue_duration())
        else:
            embed.add_field(name='Current Song', value=f'```Not playing anything. Add songs with >play```', inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name = 'skip', description = 'Skip the current song', aliases = ['s'])
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def skip(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send('I am not playing anything.', delete_after=10)
        skipped = self.current
        if len(self.queue) == 0:
            ctx.voice_client.stop()
            self.current = None
        else:
            ctx.voice_client.stop()
        if skipped:
            await ctx.send(embed = self.create_song_embed(skipped, '⌛ Skipped:'))
    
    @commands.hybrid_command(name = 'shuffle', description = 'Shuffle the queue')
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def shuffle(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send('I am not playing anything.', delete_after=10)
        if len(self.queue) == 0:
            await ctx.send('Queue is empty.', delete_after=10)
        else:
            random.shuffle(self.queue)
            await ctx.send('Shuffled queue')

    @commands.hybrid_command(name = 'pause', description = '(Un)pauses current music')
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def pause(self, ctx):
        if not ctx.voice_client:
            return await ctx.send('I am not currently playing anything.', delete_after=10)
        elif ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            return await ctx.send(f'`{ctx.author}` Resumed the song')
        elif not ctx.voice_client.is_paused():
            ctx.voice_client.pause()
            return await ctx.send(f'`{ctx.author}` paused the song')
        return await ctx.send('Error in pause: unhandled case')

    @commands.hybrid_command(name = 'volume', description = 'Change the global volume of music')
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def volume(self, ctx, volume=None):
        if not volume:
            await ctx.send(f'Current volume is {int(ctx.voice_client.source.volume * 100)}%')
            return
        if ctx.voice_client is None:
            return await ctx.send('I am not connected to a vc')
        ctx.voice_client.source.volume = int(volume) / 100
        await ctx.send(f'`{ctx.author}` changed volume to {volume}%')

    @commands.hybrid_command(name = 'leave', description = 'Leave, also clears queue', aliases = ['l', 'stop'])
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def leave(self, ctx):
        if ctx.voice_client:
            self.queue = []
            await ctx.send('Left the voice channel, queue is cleared', delete_after=10)
            await ctx.voice_client.disconnect()
        else:
            await ctx.send('Not in a vc', delete_after=3)

    @commands.hybrid_command(name = 'clear', description = 'Clear the queue')
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def clear(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            self.current = None
            self.queue = []
            await ctx.send('Queue is cleared.', delete_after=10)

    async def player_delay(self, ctx):
        ctx.voice_client.pause()
        await asyncio.sleep(1)
        ctx.voice_client.resume()
    
    async def delete_command_message(self, ctx):
        if ctx.message.content.startswith('>'):
            await asyncio.sleep(5)
            await ctx.message.delete()

    def create_song_embed(self, song, title):
        embed = discord.Embed(
            title=title,
            description=song['title']  + f'\n\nrequested by `{song["requester"]}`',
            colour=rand_colour()
        )
        embed.set_thumbnail(url=song['tn'])
        embed.set_footer(text=f'{int(song["duration"] / 60)} minutes {int(song["duration"] % 60)} seconds')
        return embed

    def queue_duration(self):
        duration = self.current['duration']
        for song in self.queue:
            duration += song['duration']
        return f'{int(duration / 60)} minutes {int(duration % 60)} seconds'


async def song_search(url, requester, *, loop=None):
    loop = loop or asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
    
    response = {}
    response['songs'] = []
    
    if 'entries' in data:
        for i in range(0, len(data['entries'])):
            info = data['entries'][i]
            response['songs'].append(get_song_data(info, requester))
            response['pl_name'] = info['playlist_title']
    else:
        response['songs'].append(get_song_data(data, requester))
    return response

def get_song_data(info, requester):
    song = {}
    song['title'] = info['title']
    song['webpage_url'] = info['webpage_url']
    song['tn'] = info['thumbnail']
    song['duration'] = info['duration']
    song['requester'] = requester
    return song
        
async def setup(bot):
    await bot.add_cog(Music(bot))