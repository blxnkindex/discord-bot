import discord
from discord.ext import commands

from utils import rand_colour

class Default(commands.Cog, name = 'default'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='help', description='List all bot commands')
    async def help(self, ctx):
        hidden = [':)', ':(']
        embed = discord.Embed(title='Help 💬', description='**Available commands:**', color=0xFFFFF)
        for i in self.bot.cogs:
            cmds = []
            if not (i.lower() == 'owner'):
                for command in self.bot.get_cog(i.lower()).get_commands():
                    if command.name not in hidden:
                        description = command.description.partition('\n')[0]
                        cmds.append(f'>{command.name} -  {description}')
                        cmd = "\n".join(cmds)
                embed.add_field(name=i.capitalize() + ' commands', value=f'```{cmd}```', inline=False)

        await ctx.send(embed=embed)


    @commands.hybrid_command(name = 'info', description = 'Get some info about the server', aliases = ['serverinfo'])
    async def info(self, ctx):
        embed = discord.Embed(title='Server Info 💬', description=str(ctx.guild.name), colour=rand_colour())
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        embed.add_field(name='Server ID', value=ctx.guild.id)
        embed.add_field(name='Members', value=ctx.guild.member_count)
        embed.add_field(name='Channels', value=f'{len(ctx.guild.channels)}')
        embed.add_field(name='Roles', value=len(ctx.guild.roles))
        embed.set_footer(text=f'Server Made: {ctx.guild.created_at}')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='ping', description='Check bot delay',)
    async def ping(self, ctx):
        await ctx.send(f'🏓 Pong! Latency is `{round(self.bot.latency * 1000, 1)}ms`')

async def setup(bot):
    await bot.add_cog(Default(bot))
