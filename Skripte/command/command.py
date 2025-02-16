import discord
from discord.ext import commands
import json

class CommandHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('Skripte/command/command.json', 'r') as f:
            self.strips = json.load(f)['strips']

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        for strip in self.strips:
            if strip['enabled'] and message.content.startswith(f"{self.bot.command_prefix}{strip['command']}"):
                await message.channel.send(strip['response'])
                return  # Stop after finding the first matching command

def setup(bot):
    bot.add_cog(CommandHandler(bot))
