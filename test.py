import discord
from discord.ext import commands
from discord.ext.commands import Context



class Test(commands.Cog, name = 'test'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name = 'help',
        description = 'help command description'
    )
    async def help(self, context: Context):
        await context.send(embed = discord.Embed(
            title = 'Help Command', 
            description = 'Description', 
            color = 0xFF076D
        ))

async def setup(bot):
    await bot.add_cog(Test(bot))