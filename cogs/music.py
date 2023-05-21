import asyncio

import discord
import youtube_dl
import random
import DiscordUtils
from discord.ext import commands, tasks

from utils import ytdl_format_options, ffmpeg_options
from utils import player_delay, delete_command_message, get_song_data, create_song_embed, rand_colour


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''
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
        self.loop = False
        self.toLoop = []

    @commands.hybrid_command(name = 'join', description = 'Joins your voice channel')
    async def join(self, ctx):
        if not ctx.message.author.voice:
            return await ctx.send('You are not connected to a voice channel.', delete_after=10)
        channel = ctx.message.author.voice.channel
        if not channel:
            return await ctx.send('You are not connected to a voice channel.', delete_after=10)
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        self.detect_idle.start(ctx)
        await channel.connect()
        await delete_command_message(ctx)

    @commands.hybrid_command(name = 'play', description = 'Plays/searches youtube for a song', aliases = ['p'])
    async def play(self, ctx, *, search):
        # check loop
        if not self.loop:
            self.toLoop = []
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                self.detect_idle.start(ctx)
            else:
                return await ctx.send(':x: You are not connected to a voice channel.', delete_after=10)
        try:
            async with ctx.typing():
                response = await song_search(search, ctx.message.author, loop=self.bot.loop)
            song = response['songs'].pop(0)
            if not ctx.voice_client.is_playing():
                player = await YTDLSource.source(song, loop=self.bot.loop)
                async with ctx.typing():
                    ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
                    await player_delay(ctx)
                self.current = song
                await ctx.send(embed = create_song_embed(song, '🎵  Now Playing:'))
            else:
                self.queue.append(song)
                if self.loop:
                    self.toLoop.append(song)
                await ctx.send(embed = create_song_embed(song, '⏳ Queued:'))
            if response['songs']:
                for i in response['songs']:
                    self.queue.append(i)
                await ctx.send(f'Queued {len(response["songs"])} songs from {response["pl_name"]}')
        except Exception as e:
            await ctx.send(f'Try again. Error occured {e}', delete_after=10)

        await delete_command_message(ctx)

    async def play_next(self, ctx):
        if self.loop and len(self.queue) == 0:
            self.queue = self.toLoop.copy()
        song = self.queue.pop(0)
        player = await YTDLSource.source(song, loop=self.bot.loop)
        self.current = song
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
        await player_delay(ctx)
        if not self.loop:
            await ctx.send(embed = create_song_embed(song, '🎵  Now Playing:'))

    @commands.hybrid_command(name = 'loop', description = 'Requeues a song whenever its done playing')
    async def loop(self, ctx, loop=None):
        if not loop:
            if self.loop:
                return await ctx.send('Currently looping')
            else:
                return await ctx.send('Currently not looping')
        if loop == 'on':
            self.loop = True
            self.toLoop = self.queue.copy()
            self.toLoop.append(self.current)
            return await ctx.send('Now looping. All existing songs will be looped. Music output is suppressed.')

        elif loop == 'off':
            self.loop = False
            self.toLoop = []
            return await ctx.send('Stopped looping.')
        else:
            return await ctx.send('Usage >loop on or >loop off.', delete_after=10)


    @commands.hybrid_command(name = 'queue', description = 'Displays the next 10 songs in queue', aliases = ['q'])
    async def queue(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            self.current = None
        if self.current:
            embeds = []
            if len(self.queue) != 0:
                for i in range(0, len(self.queue), 10):
                    embeds.append(self.get_queue_embeds(i))
                if len(embeds) == 1:
                    return await ctx.send(embed=embeds.pop(0))
                else:
                    paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx)
                    paginator.add_reaction('⏪', "back")
                    paginator.add_reaction('⏩', "next")
                    
                    await paginator.run(embeds)
            else:
                embed = discord.Embed(title='Queue 🎵', colour=rand_colour())
                embed.add_field(name='Current Song', value=f'```{self.current["title"]}```', inline=False)
                embed.set_thumbnail(url=self.current["tn"])
                return await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title='Queue 🎵', colour=rand_colour())
            embed.add_field(name='Current Song', value=f'```Not playing anything. Add songs with >play```', inline=False)
            return await ctx.send(embed=embed)

    def get_queue_embeds(self, i):
        embed = discord.Embed(title='Queue 🎵', colour=rand_colour())
        embed.add_field(name='Current Song', value=f'```{self.current["title"]}```', inline=False)
        embed.set_thumbnail(url=self.current["tn"])
        songs = []
        cap = min(len(self.queue), i + 10)
        for j in range(i, cap):
            songs.append(str(self.queue[j]['title']))
        if len(songs) == 0:
            text = 'Empty. Add more songs with >play'
        else:
            text = '\n\n'.join(songs)
        embed.add_field(name=f'{i + 1} to {cap + 1} of {len(self.queue) + 1} songs', value=f'```{text}```')
        embed.set_footer(text=f'Queue Duration: {self.queue_duration()}')
        return embed

    @commands.hybrid_command(name = 'skip', description = 'Skip the current song', aliases = ['s'])
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
            await ctx.send(embed = create_song_embed(skipped, '⏩ Skipped:'))
    
    @commands.hybrid_command(name = 'shuffle', description = 'Shuffle the queue')
    async def shuffle(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send('I am not playing anything.', delete_after=10)
        if len(self.queue) == 0:
            await ctx.send('Queue is empty.', delete_after=10)
        else:
            random.shuffle(self.queue)
            await ctx.send('Shuffled queue')

    @commands.hybrid_command(name = 'pause', description = '(Un)pauses current music')
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
    async def volume(self, ctx, volume=None):
        if not volume:
            await ctx.send(f'Current volume is {int(ctx.voice_client.source.volume * 100)}%')
            return
        if ctx.voice_client is None:
            return await ctx.send('I am not connected to a vc')
        ctx.voice_client.source.volume = int(volume) / 100
        await ctx.send(f'`{ctx.author}` changed volume to {volume}%')

    @commands.hybrid_command(name = 'leave', description = 'Leave, also clears queue', aliases = ['l', 'stop'])
    async def leave(self, ctx):
        if ctx.voice_client:
            self.queue = []
            await ctx.send('Left the voice channel, queue is cleared', delete_after=10)
            self.detect_idle.cancel()
            self.loop = False
            await ctx.voice_client.disconnect()
        else:
            await ctx.send('Not in a vc', delete_after=3)

    @commands.hybrid_command(name = 'clear', description = 'Clear the queue')
    async def clear(self, ctx):
        if ctx.voice_client:
            self.loop = False
            self.queue = []
            await ctx.send('Queue is cleared.', delete_after=10)

    def queue_duration(self):
        duration = self.current['duration']
        for song in self.queue:
            duration += song['duration']
        return f'{int(duration / 60)} minutes {int(duration % 60)} seconds'

    @tasks.loop(minutes=1)
    async def detect_idle(self, ctx):
        voice = ctx.voice_client
        if voice and not voice.is_playing() and len(self.queue) == 0:
            idle_time = 0
            while True:
                await asyncio.sleep(1)
                idle_time = idle_time + 1
                if idle_time == 300:
                    await ctx.send("Leaving voice due to inactivity")
                    await voice.disconnect()
                    self.detect_idle.cancel()
                    break
                if voice.is_playing() or voice.is_paused():
                    break


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

async def setup(bot):
    await bot.add_cog(Music(bot))