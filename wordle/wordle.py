from redbot.core import commands
from redbot.core import Config, bank
from redbot.core import checks
from redbot.core.utils.predicates import MessagePredicate
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

    default_guild_settings = {"WIN_AMOUNT": 2000}
    default_member_settings = {"played": 0, "total_wins": 0, "streak": 0, "max_streak": 0}

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier = 8234834580, force_registration=True)
        self.config.register_guild(**self.default_guild_settings)
        self.config.register_member(**self.default_member_settings)

    @commands.command()
    @commands.max_concurrency(1, per = commands.BucketType.user, wait = False)
    @commands.guild_only()
    async def wordle(self, ctx):
        f"Play a game of Wordle!"
        target_word = await self.get_word()

        re.sub(r'\W+', '', target_word)

        guesses = []

        await ctx.send("Welcome to Wordle! Try deciphering the random five letter word. Type `stop` at any time to cancel the game.")

        played = await self.config.member(ctx.author).played() + 1
        total_wins = await self.config.member(ctx.author).total_wins()
        streak = await self.config.member(ctx.author).streak()
        max_streak = await self.config.member(ctx.author).max_streak()

        await self.config.member(ctx.author).played.set(played)

        canvas = await self.draw_canvas(ctx, target_word, guesses)
        file = discord.File(canvas, filename = "wordle.png")
        wordle_game = await ctx.send(file = file)

        while len(guesses) < 6 and target_word not in guesses:
            try:
                guess = await self.bot.wait_for("message", check = MessagePredicate.same_context(ctx), timeout=150.0)
            except asyncio.TimeoutError:
                await ctx.send("Stopping game. Goodbye!")
                return
            else:
                if guess.content.lower() == "stop":
                    await ctx.send("It was nice playing with you. Goodbye!")
                elif (len(guess.content) != 5):
                    await ctx.send("Your guess must be 5 characters long.", delete_after = 5)
                elif guess.content.lower() not in open(f"{bundled_data_path(self)}/valid_guesses.txt").read():
                    await ctx.send("Please guess another word, that one isn't valid.", delete_after = 5)
                else:
                    guesses.append(guess.content.lower())
                    canvas = await self.draw_canvas(ctx, target_word, guesses)
                    file = discord.File(canvas, filename = "wordle.png")
                    await wordle_game.edit(file = file)

        if target_word in guesses:
            await ctx.send(f"A winner is you! You've been awarded {await self.config.guild(ctx.guild).WIN_AMOUNT()} {await bank.get_currency_name(ctx.guild)}!")
            await self.config.member(ctx.author).total_wins.set(total_wins + 1)
            await self.config.member(ctx.author).streak.set(streak + 1)
            if streak + 1 > max_streak:
                await self.config.member(ctx.author).max_streak.set(streak + 1)
            try:
                await bank.deposit_credits(author, await self.config.guild(guild).WIN_AMOUNT())
            except:
                pass
        else:
            await ctx.send(f"The word was {target_word}. Better luck next time!")
            await self.config.member(ctx.author).streak.set(0)
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

        font_file = f"{bundled_data_path(self)}/HelveticaNeue.ttf"
        font_color = (208, 204, 198, 255)
        font = ImageFont.truetype(font_file, 32)

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
                font_x = start_x + (cell_width / 2)
                font_y = start_y + (cell_height / 2)
                end_x = start_x + cell_width
                end_y = start_y + cell_height

                if y < len(guesses):
                    if guesses[y][x] == letter:
                        frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_green)
                    elif guesses[y][x] in target_word and (len(re.findall(guesses[y][x], guesses[y])) < len(re.findall(guesses[y][x], target_word))):
                        frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_yellow)
                    else:
                        frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_grey)
                    frame.text(xy = (font_x, font_y), text = guesses[y][x].upper(), fill = font_color, font = font, anchor = "mm")

                else:
                    frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_bg, cell_white, cell_border_width)

        file = BytesIO()
        canvas.save(file, "PNG", quality = 100)
        file.seek(0)
        return file


