import discord
from discord.ext import commands
import json

# Load configurations from config.json
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

config = load_config()

BOT_TOKEN = config['bot_token']
BOT_PREFIX = config['prefix']
SCRIPTS = config['scripts']

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Enable member intents for welcome messages

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

def load_scripts():
    for script in SCRIPTS:
        if script['enabled']:
            bot.load_extension(f"Skripte.{script['name']}")
        else:
            bot.unload_extension(f"Skripte.{script['name']}")

# Load or unload scripts based on config
load_scripts()

bot.run(BOT_TOKEN)
