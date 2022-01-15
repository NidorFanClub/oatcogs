from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from io import BytesIO
import asyncio
import discord.utils 
import discord.ext
import discord
import os

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
        # Grey (#2c3032)
        # Yellow (#917f2f)
        # Green (#42713e)
    # Clear Sans 32pt

    @commands.command()
    @commands.guild_only()
    async def wordle(self, ctx):
        f"Play a game of Wordle!"
        wordle_game = await self.draw_canvas(ctx, "guess", None)
        file = discord.File(wordle_game, filename = "world.png")
        await ctx.send(file = file)

    async def draw_canvas(self, ctx, target_word, guesses):
        canvas_width = 350
        canvas_height = 420
        canvas_padding = 10

        cell_bg = (0, 0, 0, 255)
        cell_border = (121, 112, 99, 0)
        cell_grey = (44, 48, 50, 0)
        cell_yellow = (145, 127, 47, 0)
        cell_green = (66, 113, 62, 0)

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

                frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_bg, cell_border, cell_border_width)

        file = BytesIO()
        frame.save(file, "PNG", quality = 100)
        file.seek(0)
        return file


