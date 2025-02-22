import discord
from discord.ext import commands
import json
import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'Welcome.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.welcome_channel_id = int(self.config['welcome_channel'])
        self.welcome_message = self.config['welcome_message']
        self.welcome_image_url = self.config.get('welcome_image_url', '')
        self.text_position = self.config.get('text_position', {'x': 325, 'y': 125})
        self.font_size = self.config.get('font_size', 30)
        self.image_size = self.config.get('image_size', {'width': 650, 'height': 245})

    def generate_welcome_image(self, member_name):
        response = requests.get(self.welcome_image_url)
        img = Image.open(BytesIO(response.content))
        img = img.resize((self.image_size['width'], self.image_size['height']))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", self.font_size)
        except OSError:
            font = ImageFont.load_default()
        text = self.welcome_message.format(member=member_name)
        text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
        text_x = self.text_position['x'] - text_width / 2
        text_y = self.text_position['y'] - text_height / 2
        draw.text((text_x, text_y), text, font=font, fill="white")
        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)
        return output

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.welcome_channel_id)
        if channel:
            welcome_image = self.generate_welcome_image(member.display_name)
            await channel.send(file=discord.File(welcome_image, "welcome.png"))

def setup(bot):
    bot.add_cog(Welcome(bot))
