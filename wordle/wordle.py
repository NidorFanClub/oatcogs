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

        await ctx.send("Welcome to Wordle! Type a five letter word to start. Type `stop` at any time to cancel the game.")

        played = await self.config.member(ctx.author).played() + 1
        total_wins = await self.config.member(ctx.author).total_wins()
        streak = await self.config.member(ctx.author).streak()
        max_streak = await self.config.member(ctx.author).max_streak()
        win_amount = await self.config.guild(ctx.guild).WIN_AMOUNT() * (1 + (0.25 * streak))

        await self.config.member(ctx.author).played.set(played)

        canvas = await self.draw_canvas(ctx, target_word, guesses)
        keyboard = await self.draw_keyboard(ctx, target_word, guesses)

        wordle_game = discord.File(canvas, filename = "wordle_game.png")
        wordle_keyboard = discord.File(keyboard, filename = "wordle_keyboard.png")
        await ctx.send(file = wordle_game)
        await ctx.send(file = wordle_keyboard)

        while len(guesses) < 6 and target_word not in guesses:
            try:
                guess = await self.bot.wait_for("message", check = MessagePredicate.same_context(ctx), timeout = 300.0)
            except asyncio.TimeoutError:
                await ctx.send(f"Stopping game. The word was ***{target_word}***. Goodbye!")
                return
            else:
                if guess.content.lower() == "stop":
                    await ctx.send(f"It was nice playing with you. The word was ***{target_word}***. Goodbye!")
                    return
                elif (len(guess.content) != 5):
                    await ctx.send("Your guess must be exactly 5 characters long.", delete_after = 5.0)
                elif guess.content.lower() not in open(f"{bundled_data_path(self)}/valid_guesses.txt").read() and guess.content.lower() not in open(f"{bundled_data_path(self)}/words.txt").read():
                    await ctx.send("That doesn't seem to be a valid word. Please guess again.", delete_after = 5.0)
                else:
                    guesses.append(guess.content.lower())
                    canvas = await self.draw_canvas(ctx, target_word, guesses)
                    keyboard = await self.draw_keyboard(ctx, target_word, guesses)

                    wordle_game = discord.File(canvas, filename = "wordle_game.png")
                    wordle_keyboard = discord.File(keyboard, filename = "wordle_keyboard.png")
                    await ctx.send(file = wordle_game)
                    await ctx.send(file = wordle_keyboard)

        if target_word in guesses:
            victory_string = f"A winner is you! You guessed the word ***{target_word}***, earning you {int(win_amount)} {await bank.get_currency_name(ctx.guild)}."

            if streak >= 1:
                victory_string = victory_string + f" Your streak is {str(streak + 1)} and your bonus is x{(1 + (0.25 * (streak + 1))):.2f}!"

            await ctx.send(victory_string)
            await self.config.member(ctx.author).total_wins.set(total_wins + 1)
            await self.config.member(ctx.author).streak.set(streak + 1)
            if streak + 1 > max_streak:
                await self.config.member(ctx.author).max_streak.set(streak + 1)
            try:
                await bank.deposit_credits(ctx.author, int(win_amount))
            except:
                pass
        else:
            await ctx.send(f"The word was ***{target_word}***. Better luck next time!")
            await self.config.member(ctx.author).streak.set(0)
        return

    async def get_word(self):
        return random.choice(open(f"{bundled_data_path(self)}/words.txt").read().splitlines()).lower()

    async def draw_canvas(self, ctx, target_word, guesses):
        canvas_width = 350
        canvas_height = 420
        canvas_padding = 10

        cell_border_width = 2
        cell_gap = 5
        cell_width = 62
        cell_height = 62
        cell_row_count = 6
        cell_column_count = 5

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

        canvas = Image.new("RGBA", (canvas_width, canvas_height), cell_bg)
        frame = ImageDraw.Draw(canvas)

        cell_rows = [list(target_word) for row in range(cell_row_count)]

        for y, cell_row in enumerate(cell_rows):
            answer = target_word

            for x, letter in enumerate(cell_row):
                start_x = canvas_padding + (cell_width * x) + (cell_gap * x)
                start_y = canvas_padding + (cell_height * y) + (cell_gap * y)
                end_x = start_x + cell_width
                end_y = start_y + cell_height

                font_x = start_x + (cell_width / 2)
                font_y = start_y + (cell_height / 2)

                frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_bg, cell_white, cell_border_width)

                if y < len(guesses):
                    frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_grey)
                    if guesses[y][x] == letter:
                        answer = ''.join(answer.split(letter, 1))
                        frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_green)
                    frame.text(xy = (font_x, font_y), text = guesses[y][x].upper(), fill = font_color, font = font, anchor = "mm")

            for x, letter in enumerate(cell_row):
                start_x = canvas_padding + (cell_width * x) + (cell_gap * x)
                start_y = canvas_padding + (cell_height * y) + (cell_gap * y)
                end_x = start_x + cell_width
                end_y = start_y + cell_height

                font_x = start_x + (cell_width / 2)
                font_y = start_y + (cell_height / 2)

                if y < len(guesses):
                    if guesses[y][x] in answer and guesses[y][x] != letter:
                        answer = ''.join(answer.split(guesses[y][x], 1))
                        frame.rectangle([(start_x, start_y), (end_x, end_y)], cell_yellow)
                    frame.text(xy = (font_x, font_y), text = guesses[y][x].upper(), fill = font_color, font = font, anchor = "mm")

        file = BytesIO()
        canvas.save(file, "PNG", quality = 100)
        file.seek(0)
        return file

    async def draw_keyboard(self, ctx, target_word, guesses):
        canvas_width = 500
        canvas_height = 200
        canvas_padding = 8

        key_gap = 6
        key_width = 43
        key_height = 58

        key_bg = (0, 0, 0, 0)
        key_default = (129, 131, 132, 255)
        key_grey = (58, 58, 60, 255)
        key_yellow = (181, 159, 59, 255)
        key_green = (83, 141, 78, 255)

        keys = "qwertyuiopasdfghijklzxcvbnm"

        font_file = f"{bundled_data_path(self)}/HelveticaNeue.ttf"
        font_color = (208, 204, 198, 255)
        font = ImageFont.truetype(font_file, 13.33333)

        for key_index, keyboard_letter in enumerate(keys):
            if key_index < 10:
                top = key_index
                start_x = canvas_padding + (key_width * top) + (key_gap * top)
                start_y = 0
            elif key_index >= 10 and key_index < 20:
                mid = key_index - 10
                start_x = canvas_padding + (key_width/2) + (key_width * mid) + (key_gap * mid)
                start_y = key_height + key_gap
            else:
                bot = key_index - 20
                start_x = canvas_padding + key_width + (key_width/2) + (key_width * bot) + (key_gap * bot)
                start_y = (key_height * 2) + (key_gap * 2)

            end_x = start_x + key_width
            end_y = start_y + key_height

            font_x = start_x + (key_width / 2)
            font_y = start_y + (key_height / 2)

            frame.rounded_rectangle([(start_x, start_y), (end_x, end_y)], radius = 4, fill = key_default)
            frame.text(xy = (font_x, font_y), text = guesses[y][x].upper(), fill = font_color, font = font, anchor = "mm")

            for guess in guesses:
                for i, letter in enumerate(guess):
                    if guess[i] not in target_word:
                        frame.rounded_rectangle([(start_x, start_y), (end_x, end_y)], radius = 4, fill = key_grey)

            for guess in guesses:
                for i, letter in enumerate(guess):
                    if guess[i] in target_word:
                        frame.rounded_rectangle([(start_x, start_y), (end_x, end_y)], radius = 4, fill = key_yellow)

            for guess in guesses:
                for i, letter in enumerate(guess):
                    if guess[i] == target_word[i]:
                        frame.rounded_rectangle([(start_x, start_y), (end_x, end_y)], radius = 4, fill = key_green)
