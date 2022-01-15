from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.data_manager import bundled_data_path
from io import BytesIO
import asyncio
import discord.utils 
import discord.ext
import discord
import random
import os
import re

try:
    from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps
    from PIL import features as pil_features
except Exception as e:
    raise RuntimeError(f"Can't load pillow: {e}\nDo '[p]pipinstall pillow'.")

AVATAR_FORMAT = "webp" if pil_features.check("webp_anim") else "jpg"

class Wordle(commands.Cog):
    """Wordle -- now in Discord!"""
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier = 8234834580, force_registration=True)
        #self.config.register_guild()

    # 350x420 canvas (10 px padding)
    # 62x62 cells
    # 5 pixel gaps between cells
    # 2 pixel border (#797063)
    # Colors for cell:
        # Default (#121213)
        # Grey (#2c3032)
        # Yellow (#917f2f)
        # Green (#42713e)
        # Discord Dark (#292b2f)
        # Discord Grey (#2f3136)
    # Clear Sans 32pt

    @commands.command()
    @commands.guild_only()
    async def wordle(self, ctx):
        f"Play a game of Wordle!"
        target_word = await self.get_word()

        re.sub(r'\W+', '', target_word)

        guesses = []

        await ctx.send("Welcome to Wordle! Try deciphering the random five letter word. Type `stop` at any time to cancel the game.")

        canvas = await self.draw_canvas(ctx, target_word, guesses)
        file = discord.File(canvas, filename = "wordle.png")
        await ctx.send(file = file)

        async def check(message: discord.Message):
            if message.author.id == ctx.author.id and message.channel.id == ctx.channel.id:
                return True
            elif message.content.lower() == "stop":
                await ctx.send("Stopping game. Goodbye!")
            elif (len(message.content) != 5):
                await ctx.send("Your guess must be exactly 5 characters.")
            elif message.content not in open(f"{bundled_data_path(self)}/words.txt").read():
                await ctx.send("Your guess must be a valid English word.")
            else:
                return False

        while len(guesses) < 6 or target_word not in guesses:
            try:
                guess = await ctx.bot.wait_for("message", check = check, timeout=120.0)
            except asyncio.TimeoutError:
                await ctx.send("Stopping game. Goodbye!")
                return
            else:
                guesses.append(guess.content.lower())
                canvas = await self.draw_canvas(ctx, target_word, guesses)
                file = discord.File(canvas, filename = "wordle.png")
                await ctx.send(file = file)

        await ctx.send("A winner is you!")
        return

    async def get_word(self):
        return random.choice(open(f"{bundled_data_path(self)}/words.txt").read().splitlines()).lower()

    async def draw_canvas(self, ctx, target_word, guesses):
        canvas_width = 350
        canvas_height = 420
        canvas_padding = 10

        cell_bg = (0, 0, 0, 0)
        cell_white = (255, 255, 255, 255)
        cell_border = (121, 112, 99, 255)
        cell_default = (18, 18, 19, 255)
        cell_grey = (44, 48, 50, 255)
        cell_yellow = (145, 127, 47, 255)
        cell_green = (66, 113, 62, 255)
        cell_discord_dark = (41, 43, 47, 255)
        cell_discord_grey = (47, 49, 54, 255)

        cell_border_width = 2
        cell_gap = 5
        cell_width = 62
        cell_height = 62
        cell_row_count = 6
        cell_column_count = 5

        canvas = Image.new("RGBA", (canvas_width, canvas_height), cell_bg)
        frame = ImageDraw.Draw(canvas)

        cell_rows = [list(target_word) for row in range(cell_row_count)]

        for y, cell_row in enumerate(cell_rows):
            for x, letter in enumerate(cell_row):
                start_x = canvas_padding + (cell_width * x) + (cell_gap * x)
                start_y = canvas_padding + (cell_height * y) + (cell_gap * y)
                end_x = start_x + cell_width
                end_y = start_y + cell_height

                if y < len(guesses):
                    if guesses[y][x] == letter:
                        frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_green)
                    elif guesses[y][x] in target_word:
                        frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_yellow)
                    else:
                        frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_grey)
                else:
                    frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_bg, cell_white, cell_border_width)

        file = BytesIO()
        canvas.save(file, "PNG", quality = 100)
        file.seek(0)
        return file


