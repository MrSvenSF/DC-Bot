import discord
from discord.ext import commands

BOT_TOKEN = "MTMyNjk2MzY1NDM1NjM3MzU3OA.GxGaWx.ckWBMYwypKGKfyT_3g4m8abXUHFWdB1RbR27k4"  # Ändere dies zu deinem Bot-Token

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')

bot.run(BOT_TOKEN)
