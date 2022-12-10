import asyncio
import os

import discord
import youtube_dl
from default import rand_colour
from discord import app_commands

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def search(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data=data)

class Music(commands.Cog, name = 'music'):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    @commands.hybrid_command(
        name = 'join',
        description = 'Joins your voice channel',
        aliases = ['j']
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def join(self, ctx):        
        channel = ctx.message.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.hybrid_command(
        name = 'play',
        description = 'Plays a URL, or searches youtube for a song',
        aliases = ['p']
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def play(self, ctx, *, search):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")

        player = await YTDLSource.search(search, loop=self.bot.loop)
        if not ctx.voice_client.is_playing():
            async with ctx.typing():
                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
                await self.player_delay(ctx)
            await ctx.send(f'Now playing: {player.title}')
        else:
            self.queue.append(player)
            await ctx.send(f'Queued: {player.title}')

    async def play_next(self, ctx):
        player = self.queue.pop(0)
        await asyncio.sleep(1)
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        await self.player_delay(ctx)
        await ctx.send(f'Now playing: {player.title}')

    @commands.hybrid_command(
        name = 'queue',
        description = 'Displays the queue',
        aliases = ['q']
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def queue(self, ctx):
        songs = []
        for song in self.queue:
            songs.append(str(song.title))
        text = '\n\n'.join(songs)
        if len(songs) == 0:
            text = 'Empty! Add songs with >play'
        embed = discord.Embed(
            title='Queue', 
            description=f'```{text}```', 
            colour=rand_colour()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name = 'skip',
        description = 'Skip the current song'
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def skip(self, ctx):
        if len(self.queue) == 0:
            ctx.voice_client.stop()
            await ctx.send('Last song in queue, stopping...', delete_after=10)
        else:
            ctx.voice_client.stop()
            player = self.queue.pop(0)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            await self.player_delay(ctx)
            await ctx.send(f'Now playing: {player.title}')

    @commands.hybrid_command(
        name = 'pause',
        description = 'Pauses current music'
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def pause(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send('I am not currently playing anything!', delete_after=10)
        elif ctx.voice_client.is_paused():
            return

        ctx.voice_client.pause()
        await ctx.send(f'`{ctx.author}` paused the song!')

    @commands.hybrid_command(
        name = 'resume',
        description = 'Resumes paused music'
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def resume(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send('I am not currently playing anything!', delete_after=10)
        elif not ctx.voice_client.is_paused():
            return

        ctx.voice_client.resume()
        await ctx.send(f'`{ctx.author}` Resumed the song!')

    @commands.hybrid_command(
        name = 'volume',
        description = 'Change the global volume of music'
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def volume(self, ctx, volume=None):
        if not volume:
            print(ctx.voice_client.source.volume)
            await ctx.send(f'Current volume is {int(ctx.voice_client.source.volume * 100)}%')
            return
        if ctx.voice_client is None:
            return await ctx.send("I am not connected to a vc")
        ctx.voice_client.source.volume = int(volume) / 100
        await ctx.send(f'`{ctx.author}` changed volume to {volume}%')

    @commands.hybrid_command(
        name = 'leave',
        description = 'Leaves the channel (also clears the queue)',
        aliases = ['l', 'stop']
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def leave(self, ctx):
        await ctx.send('Left the voice channel, queue is cleared', delete_after=10)
        await ctx.voice_client.disconnect()

    @commands.hybrid_command(
        name = 'clear',
        description = 'Clear the queue but doesn\'t leave voice',
        aliases = ['clearqueue']
    )
    @app_commands.guilds(discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    async def clear(self, ctx):
        ctx.voice_client.stop()        
        self.queue = []
        await ctx.send('Queue is cleared.', delete_after=10)

    async def player_delay(self, ctx):
        ctx.voice_client.pause()
        await asyncio.sleep(1)
        ctx.voice_client.resume()

async def setup(bot):
    await bot.add_cog(Music(bot))