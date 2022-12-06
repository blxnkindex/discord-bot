import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context



class Test(commands.Cog, name = 'test'):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name = 'test',
        with_app_command = True,
        description = 'TESTING'
    )
    # Syncs to test server
    @app_commands.guilds(discord.Object(id = 715252385269678241))
    @commands.has_permissions(administrator = True)
    async def test(self, ctx: Context):
        await ctx.send(embed = discord.Embed(
            title = 'test command', 
            description = 'Description', 
            color = 0x00E76D
        ))

async def setup(bot):
    await bot.add_cog(Test(bot))