import discord
from discord.ext import commands
import json
import os

# Load configurations from config.json
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config()

BOT_TOKEN = config['bot_token']
BOT_PREFIX = config['prefix']
SCRIPTS = config['scripts']

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Enable member intents for welcome messages
intents.messages = True  # Enable message intents for message delete/edit events

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

def load_scripts():
    for script in SCRIPTS:
        extension_name = f"Skripte.{script['directory']}.{script['name']}"
        if script['enabled']:
            if extension_name not in bot.extensions:
                bot.load_extension(extension_name)
        else:
            if extension_name in bot.extensions:
                bot.unload_extension(extension_name)

@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, script_name: str):
    script = next((s for s in SCRIPTS if s['name'] == script_name), None)
    if script:
        extension_name = f"Skripte.{script['directory']}.{script['name']}"
        if extension_name in bot.extensions:
            bot.unload_extension(extension_name)
        bot.load_extension(extension_name)
        await ctx.send(f"Script {script_name} reloaded successfully.")
    else:
        await ctx.send(f"Script {script_name} not found.")

@bot.command(name='commands', aliases=['?'])
async def commands_command(ctx):
    help_text = """
    **Available Commands:**
    - !commands or !? : Show this help message
    - !reload <script_name> : Reload a specific script (admin only)
    - !enable_logging <channel_id> : Enable logging for a specific channel (admin only)
    - !disable_logging <channel_id> : Disable logging for a specific channel (admin only)
    """
    await ctx.send(help_text)

# Load or unload scripts based on config
load_scripts()

bot.run(BOT_TOKEN)
