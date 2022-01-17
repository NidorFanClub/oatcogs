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

    default_guild_settings = {"WIN_AMOUNT": 500, "MULTIPLIER": True, "STREAKS": True, "TURN_MULTIPLIER": True}
    default_member_settings = {"played": 0, "total_wins": 0, "total_earnings": 0, "streak": 0, "max_streak": 0, "guess_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}}

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

        await self.config.member(ctx.author).played.set(await self.config.member(ctx.author).played() + 1)

        wordle_image = await self.draw_wordle(ctx, await self.draw_canvas(ctx, target_word, guesses), await self.draw_keyboard(ctx, target_word, guesses))
        wordle_file = discord.File(wordle_image, filename = "wordle.png")

        await ctx.send("Welcome to Wordle! Type a five letter word to start. Type `stop` at any time to cancel the game.", file = wordle_file)

        while len(guesses) < 6 and target_word not in guesses:
            try:
                guess = await self.bot.wait_for("message", check = MessagePredicate.same_context(ctx), timeout = 300.0)
            except asyncio.TimeoutError:
                await ctx.send(f"Stopping game. The word was ***{target_word}***. Goodbye!")
                break
            else:
                if guess.content.lower() == "stop":
                    break
                elif (len(guess.content) != 5):
                    await ctx.send("Your guess must be exactly 5 characters long.", delete_after = 4.0)
                elif guess.content.lower() not in open(f"{bundled_data_path(self)}/valid_guesses.txt").read() and guess.content.lower() not in open(f"{bundled_data_path(self)}/words.txt").read():
                    await ctx.send("That doesn't seem to be a valid word. Please guess again.", delete_after = 4.0)
                else:
                    guesses.append(guess.content.lower())

                    wordle_image = await self.draw_wordle(ctx, await self.draw_canvas(ctx, target_word, guesses), await self.draw_keyboard(ctx, target_word, guesses))
                    wordle_file = discord.File(wordle_image, filename = "wordle.png")

                    await ctx.send(file = wordle_file)

        if target_word in guesses:
            base_amount = await self.config.guild(ctx.guild).WIN_AMOUNT()
            streak = await self.config.member(ctx.author).streak() + 1
            total_wins = await self.config.member(ctx.author).total_wins() + 1
            total_earnings = await self.config.member(ctx.author).total_earnings()
            max_streak = await self.config.member(ctx.author).max_streak()

            await self.config.member(ctx.author).total_wins.set(total_wins)
            await self.config.member(ctx.author).streak.set(streak)

            async with self.config.member(ctx.author).guess_distribution() as guess_distribution:
                guess_distribution[str(len(guesses))] += 1

            if streak > max_streak:
                await self.config.member(ctx.author).max_streak.set(streak)

            if await self.config.guild(ctx.guild).MULTIPLIER():
                multiplier = 0
                if await self.config.guild(ctx.guild).STREAKS():
                    await self.config.member(ctx.author).streak.set(streak)
                    multiplier += (0.5 * (streak))
                if await self.config.guild(ctx.guild).TURN_MULTIPLIER():
                    multiplier += (1 / (len(guesses) / 6))
            else:
                multiplier = 1

            win_amount = base_amount * multiplier

            victory_string = f"A winner is you! You guessed the word ***{target_word}***, earning you {int(win_amount)} {await bank.get_currency_name(ctx.guild)}."

            if streak > 1 and await self.config.guild(ctx.guild).STREAKS():
                victory_string += f" Your streak is {str(streak)} and your bonus multiplier is **x{multiplier:.2f}**!"

            await ctx.send(victory_string)

            try:
                await bank.deposit_credits(ctx.author, int(win_amount))
                await self.config.member(ctx.author).total_earnings.set(win_amount)
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

        text_color = (208, 204, 198, 255)

        HelveticaNeueBold = f"{bundled_data_path(self)}/HelveticaNeueBold.ttf"
        bold = ImageFont.truetype(HelveticaNeueBold, 32)

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
                    frame.text(xy = (font_x, font_y), text = guesses[y][x].upper(), fill = text_color, font = bold, anchor = "mm")

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
                    frame.text(xy = (font_x, font_y), text = guesses[y][x].upper(), fill = text_color, font = bold, anchor = "mm")

        return canvas

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

        text_color = (208, 204, 198, 255)

        letters = "qwertyuiopasdfghjklzxcvbnm"

        HelveticaNeueBold = f"{bundled_data_path(self)}/HelveticaNeueBold.ttf"
        bold = ImageFont.truetype(HelveticaNeueBold, 14)

        canvas = Image.new("RGBA", (canvas_width, canvas_height), key_bg)
        frame = ImageDraw.Draw(canvas)
        
        for key_index, letter in enumerate(letters):
            if key_index < 10:
                start_x = canvas_padding + (key_width * key_index) + (key_gap * key_index)
                start_y = 0
            elif key_index >= 10 and key_index < 19:
                start_x = canvas_padding + (key_width / 2) + (key_width * (key_index - 10)) + (key_gap * (key_index - 10))
                start_y = key_height + key_gap
            else:
                start_x = canvas_padding + (key_width / 2) + (key_gap / 2) + (key_width * (key_index - 18)) + (key_gap * (key_index - 18))
                start_y = (key_height * 2) + (key_gap * 2)

            end_x = start_x + key_width
            end_y = start_y + key_height

            font_x = start_x + (key_width / 2)
            font_y = start_y + (key_height / 2)

            frame.rounded_rectangle([(start_x, start_y), (end_x, end_y)], radius = 4, fill = key_default)

            for guess in guesses:
                for i, guess_letter in enumerate(guess):
                    if letter == guess_letter and guess[i] not in target_word:
                        frame.rounded_rectangle([(start_x, start_y), (end_x, end_y)], radius = 4, fill = key_grey)

            for guess in guesses:
                for i, guess_letter in enumerate(guess):
                    if letter == guess_letter and guess[i] in target_word:
                        frame.rounded_rectangle([(start_x, start_y), (end_x, end_y)], radius = 4, fill = key_yellow)

            for guess in guesses:
                for i, guess_letter in enumerate(guess):
                    if letter == guess_letter and guess[i] == target_word[i]:
                        frame.rounded_rectangle([(start_x, start_y), (end_x, end_y)], radius = 4, fill = key_green)

            frame.text(xy = (font_x, font_y), text = letter.upper(), fill = text_color, font = bold, anchor = "mm")
                        
        return canvas

    async def draw_postgame(self, target_word = None, guesses = None, earned = None, member: discord.Member):
        canvas_width = 500
        canvas_height = 444
        canvas_padding = 16

        statistics_width = 349
        statistics_height = 66
        statistics_padding = 10

        statistic_label_width = 87
        statistic_label_height = 14
        statistic_value_height = 42

        graph_width = 373
        graph_height = 154
        graph_padding = 4

        graph_label_width = 8
        graph_label_height = 20
        graph_bar_width = 365
        graph_bar_min = 25

        economy_width = 466
        economy_height = 81
        economy_padding = 10

        economy_label_width = 221

        heading_height = 38

        blank_bg = (0, 0, 0, 0)
        frame_bg = (18, 18, 19, 255)
        frame_border = (26, 26, 27, 255)

        green_bar = (83, 141, 78, 255)
        grey_bar = (58, 58, 60, 255)

        text_color = (215, 218, 220, 255)

        HelveticaNeueBold = f"{bundled_data_path(self)}/HelveticaNeueBold.ttf"
        HelveticaNeue = f"{bundled_data_path(self)}/HelveticaNeue.ttf"

        header = ImageFont.truetype(HelveticaNeueBold, 17)
        statistic_value = ImageFont.truetype(HelveticaNeue, 36)
        statistic_label = ImageFont.truetype(HelveticaNeue, 12)
        graph_label = ImageFont.truetype(HelveticaNeue, 14)
        graph_bar_label = ImageFont.truetype(HelveticaNeueBold, 14)

        played = await self.config.member(member).played()
        total_wins = await self.config.member(member).total_wins()
        streak = await self.config.member(member).played()
        max_streak = await self.config.member(member).max_streak()

        canvas = Image.new("RGBA", (canvas_width, canvas_height), blank_bg)
        frame = ImageDraw.Draw(canvas)

        frame.rounded_rectangle([(0, 0), (canvas_width, canvas_height)], radius = 11, fill = frame_bg, width = 1, outline = frame_border)

        frame.text(xy = ((canvas_width / 2), (2 * canvas_padding + heading_height / 2)), text = "STATISTICS", fill = text_color, font = header, anchor = "mm")

        frame.text(xy = ((canvas_width / 2 - 3 * statistic_label_width / 2), (2 * canvas_padding + heading_height + statistic_value_height / 2)), text = f"{humanize_int(played)}", fill = text_color, font = statistic_value, anchor = "mm")
        frame.text(xy = ((canvas_width / 2 - statistic_label_width / 2), (2 * canvas_padding + heading_height + statistic_value_height / 2)), text = f"{100 * (total_wins / played):.0f}", fill = text_color, font = statistic_value, anchor = "mm")
        frame.text(xy = ((canvas_width / 2 + statistic_label_width / 2), (2 * canvas_padding + heading_height + statistic_value_height / 2)), text = f"{streak}", fill = text_color, font = statistic_value, anchor = "mm")
        frame.text(xy = ((canvas_width / 2 + 3 * statistic_label_width / 2), (2 * canvas_padding + heading_height + statistic_value_height / 2)), text = f"{max_streak}", fill = text_color, font = statistic_value, anchor = "mm")

        frame.text(xy = ((canvas_width / 2 - 3 * statistic_label_width / 2), (2 * canvas_padding + heading_height + statistic_value_height + statistic_label_height / 2)), text = "Played", fill = text_color, font = statistic_label, anchor = "mm")
        frame.text(xy = ((canvas_width / 2 - statistic_label_width / 2), (2 * canvas_padding + heading_height + statistic_value_height + statistic_label_height / 2)), text = "Win %", fill = text_color, font = statistic_label, anchor = "mm")
        frame.text(xy = ((canvas_width / 2 + statistic_label_width / 2), (2 * canvas_padding + heading_height + statistic_value_height + statistic_label_height / 2)), text = "Current Streak", fill = text_color, font = statistic_label, anchor = "mm")
        frame.text(xy = ((canvas_width / 2 + 3 * statistic_label_width / 2), (2 * canvas_padding + heading_height + statistic_value_height + statistic_label_height / 2)), text = "Max Streak", fill = text_color, font = statistic_label, anchor = "mm")

        frame.text(xy = ((canvas_width / 2), (2 * canvas_padding + heading_height + statistics_height + heading_height / 2)), text = "GUESS DISTRIBUTION", fill = text_color, font = header, anchor = "mm")

        async with self.config.member(member).guess_distribution() as guess_distribution:
            guess_amounts = list(guess_distribution.values())
            max_guess_amount = max(guess_amounts)

        for i, guess_amount in enumerate(guess_amounts):
            percent_of_max = guess_amount / max_guess_amount

            graph_label_x = canvas_width / 2 - graph_width / 2
            graph_label_y = 2 * canvas_padding + 2 * heading_height + statistics_height + statistics_padding / 2 + i * graph_padding + i * graph_label_height
            graph_bar_start_x = graph_label_x + graph_padding + graph_label_width
            graph_bar_start_y = graph_label_y
            graph_bar_end_x = max(graph_bar_start_x + graph_bar_min, graph_bar_start_x + percent_of_max * graph_bar_width)
            graph_bar_end_y = graph_bar_start_y + graph_label_height - 2
            graph_bar_label_x = graph_bar_end_x - graph_padding * 3

            frame.text(xy = (graph_label_x, graph_label_y), text = str(i + 1), fill = text_color, font = graph_label)

            if percent_of_max == 1:
                frame.rectangle([(graph_bar_start_x, graph_bar_start_y), (graph_bar_end_x, graph_bar_end_y)], green_bar)
            else:
                frame.rectangle([(graph_bar_start_x, graph_bar_start_y), (graph_bar_end_x, graph_bar_end_y)], grey_bar)

            frame.text(xy = (graph_bar_label_x, graph_label_y), text = str(guess_amount), fill = text_color, font = graph_bar_label, anchor = "ma")

        frame.line(xy = ([(canvas_padding + economy_width / 2, 2 * canvas_padding + 2 * heading_height + statistics_height + graph_height), (canvas_padding + economy_width / 2, 2 * canvas_padding + 2 * heading_height + statistics_height + graph_height + economy_height)]), fill = text_color, width = 1)

        frame.text(xy = (canvas_padding + economy_label_width / 2, 2 * canvas_padding + 2 * heading_height + statistics_height + graph_height + heading_height / 2), text = f"EARNED {str(await bank.get_currency_name(member.guild)).upper()}", fill = text_color, font = header, anchor = "mm")

        frame.text(xy = (canvas_padding + economy_label_width / 2, 2 * canvas_padding + 3 * heading_height + statistics_height + graph_height + statistic_value_height / 2), text = f"{earned}", fill = text_color, font = statistic_value, anchor = "mm")

        return canvas

    async def draw_wordle(self, ctx, canvas, keyboard):
        keyboard.thumbnail(canvas.size)

        bg = (0, 0, 0, 0)

        img = Image.new("RGBA", (min(canvas.width, keyboard.width), canvas.height + keyboard.height), bg)
        img.paste(canvas, (0, 0))
        img.paste(keyboard, (0, canvas.height))

        return await self.save_image(img)

    async def save_image(self, img):
        file = BytesIO()
        img.save(file, "PNG", quality = 100)
        file.seek(0)
        return file

    async def humanize_int(num):
        num = float(f"{num:.3g}")
        magnitude = 0

        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0

        return f"{"{num:f}".rstrip('0').rstrip('.')}{['', 'K', 'M', 'B', 'T'][magnitude]}"

    @commands.command()
    @commands.guild_only()
    async def wordleprofile(self, ctx):
        img = await self.save_image(await self.draw_postgame(None, None, ctx.author))

        img_file = discord.File(img, filename = "profile.png")

        await ctx.send(file = img_file)
