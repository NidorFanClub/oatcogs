import asyncio
import discord
import discord.utils
import discord.ext
import random

from redbot.core import commands, Config, bank, checks
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.menus import start_adding_reactions
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as e:
    raise RuntimeError(f"Can't load pillow: {e}\nDo '[p]pipinstall pillow'.")


class _2048(commands.Cog):
    """Play 2048 in Discord!"""

    default_guild_settings = {"ECONOMY": True,
                              "MULTIPLIER": 5}

    default_member_settings = {"played": 0,
                               "total_wins": 0,
                               "total_earnings": 0,
                               "best_score": 0,
                               "total_score": 0}

    LEFT = "\u2B05"
    RIGHT = "\u27A1"
    UP = "\u2B06"
    DOWN = "\u2B07"
    CANCEL = "\u274C"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=82348345234, force_registration=True)
        self.config.register_guild(**self.default_guild_settings)
        self.config.register_member(**self.default_member_settings)

    @checks.bot_has_permissions(add_reactions=True)
    @commands.command(name="2048")
    @commands.max_concurrency(1, per=commands.BucketType.member, wait=False)
    @commands.guild_only()
    async def _2048(self, ctx):
        "Start a new game of 2048!"

        conf = self.config
        member = conf.member(ctx.author)
        guild = conf.guild(ctx.guild)

        await member.played.set(await member.played() + 1)

        victory = False
        score = 0

        board = self.new_board()
        board_image = await self.canvas(board, score)
        file = discord.File(board_image, filename="2048.png")
        link_message = await ctx.send(file=file)
        message = await ctx.send(link_message.attachments[0].url)
        try:
            await link_message.delete()
        except Exception:
            pass

        def check(reaction, user):
            return ((user.id == ctx.author.id) and (str(reaction.emoji) in [self.LEFT, self.RIGHT, self.UP, self.DOWN, self.CANCEL]) and (reaction.message.id == message.id))

        while True:
            try:
                start_adding_reactions(message, [self.LEFT, self.UP, self.DOWN, self.RIGHT, self.CANCEL])
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)  # thanks NeuroAssassin <3
            except asyncio.TimeoutError:
                try:
                    await message.clear_reactions()
                except Exception:
                    pass
                break
            else:
                old_board = board

                emoji = str(reaction.emoji)

                # future me: please fucking fix this sometime. lmao
                if emoji == self.UP:
                    board = self.transpose(self.compress(self.merge(self.compress(self.transpose(old_board)))[0]))
                    score += self.merge(self.compress(self.transpose(old_board)))[1]
                elif emoji == self.DOWN:
                    board = self.transpose(self.reverse(self.compress(self.merge(self.compress(self.reverse(self.transpose(old_board))))[0])))
                    score += self.merge(self.compress(self.reverse(self.transpose(old_board))))[1]
                elif emoji == self.LEFT:
                    board = self.compress(self.merge(self.compress(old_board))[0])
                    score += self.merge(self.compress(old_board))[1]
                elif emoji == self.RIGHT:
                    board = self.reverse(self.compress(self.merge(self.compress(self.reverse(old_board)))[0]))
                    score += self.merge(self.compress(self.reverse(old_board)))[1]
                elif emoji == self.CANCEL:
                    await message.clear_reactions()
                    break

                if board != old_board:
                    if 2048 in (cell for row in board for cell in row):
                        victory = True
                    else:
                        board = self.generate_random(board)
                        can_continue = self.check(board)

                    if victory or not can_continue:
                        break
                    else:
                        board_image = await self.canvas(board, score)
                        file = discord.File(board_image, filename="2048.png")
                        link_message = await ctx.send(file=file)

                        try:
                            await message.edit(link_message.attachments[0].url)
                        except Exception:
                            pass

                        try:
                            await link_message.delete()
                        except Exception:
                            pass

        if victory:
            total_wins = await member.total_wins() + 1
            await member.total_wins.set(total_wins)
            win_amount = score * await guild.MULTIPLIER()
        else:
            win_amount = score

        try:
            await bank.deposit_credits(ctx.author, win_amount)
        except Exception:
            pass
        else:
            await member.total_earnings.set(await member.total_earnings() + win_amount)

        #summary_image = await self.summary(board, victory)
        #summary_file = discord.File(summary_image, filename="summary.png")

        #return await ctx.send(file=summary_file)

    @commands.group(name="2048set")
    @commands.guild_only()
    @checks.admin()
    async def _2048set(self, ctx):
        """Commands for changing 2048 behavior."""
        pass

    @_2048set.command(name="multiplier")
    async def _2048set_multiplier(self, ctx: commands.Context, value: int):
        """Balance earned = score * multiplier.

        Set to 5 by default."""
        await self.config.guild(ctx.guild).MULTIPLIER.set(value)
        await ctx.send(f"The 2048 multiplier has been set to {str(value)}.")

    @_2048set.command(name="economy")
    async def _2048set_economy(self, ctx: commands.Context, toggle: bool):
        """Receive economy balance for playing.

        Enabled by default."""
        await self.config.guild(ctx.guild).STREAKS.set(toggle)
        await ctx.send(f"2048 economy integration been turned {'on' if toggle else 'off'}.")

    @_2048set.command(name="list")
    async def _2048set_list(self, ctx):
        """View current 2048 settings for the guild."""
        e = discord.Embed(title="", colour=ctx.author.color)
        e.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        e.add_field(name="Economy", value=str(await self.config.guild(ctx.guild).ECONOMY()), inline=False)
        e.add_field(name="Multiplier", value=str(await self.config.guild(ctx.guild).MULTIPLIER()), inline=False)

        await ctx.send(embed=e)

    # image generation methods

    async def canvas(self, board, score):
        canvas_width = 500
        canvas_height = 500
        canvas_padding = 15
        canvas_border_radius = 10

        cell_gap = 15
        cell_width = 106
        cell_height = 106
        cell_row_count = 4
        cell_border_radius = 4

        canvas_bg = (0, 0, 0, 0)
        summary_bg = (238, 228, 218, 186)
        cell_bg = (187, 173, 160, 255)
        cell_0 = (205, 193, 180, 255)
        cell_2 = (238, 228, 218, 255)
        cell_4 = (237, 224, 200, 255)
        cell_8 = (242, 177, 121, 255)
        cell_16 = (245, 149, 99, 255)
        cell_32 = (246, 124, 96, 255)
        cell_64 = (246, 94, 59, 255)
        cell_128 = (237, 207, 115, 255)
        cell_256 = (237, 204, 98, 255)
        cell_512 = (237, 200, 80, 255)
        cell_1024 = (237, 197, 63, 255)
        cell_2048 = (237, 194, 45, 255)
        text_dark = (119, 110, 101, 255)
        text_light = (249, 246, 242, 255)

        ClearSansBold = f"{bundled_data_path(self)}/ClearSansBold.ttf"
        bold = ImageFont.truetype(ClearSansBold, 55)
        summary = ImageFont.truetype(ClearSansBold, 60)

        canvas = Image.new("RGBA", (canvas_width, canvas_height), canvas_bg)
        frame = ImageDraw.Draw(canvas)

        frame.rounded_rectangle(xy=[(0, 0), (canvas_width, canvas_height)], radius=canvas_border_radius, fill=cell_bg)

        for y, cell_row in enumerate(board):
            for x, number in enumerate(cell_row):
                start_x = canvas_padding + (cell_width * x) + (cell_gap * x)
                start_y = canvas_padding + (cell_height * y) + (cell_gap * y)
                end_x = start_x + cell_width
                end_y = start_y + cell_height

                font_x = start_x + (cell_width / 2)
                font_y = start_y + (cell_height / 2)

                if number == 0:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_0)
                elif number == 2:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_2)
                elif number == 4:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_4)
                elif number == 8:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_8)
                elif number == 16:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_16)
                elif number == 32:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_32)
                elif number == 64:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_64)
                elif number == 128:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_128)
                elif number == 256:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_256)
                elif number == 512:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_512)
                elif number == 1024:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_1024)
                elif number == 2048:
                    frame.rounded_rectangle(xy=[(start_x, start_y), (end_x, end_y)], radius=cell_border_radius, fill=cell_2048)

                if number == 2 or number == 4:
                    frame.text(xy=(font_x, font_y), text=str(number), fill=text_dark, font=bold, anchor="mm")
                elif number != 0:
                    frame.text(xy=(font_x, font_y), text=str(number), fill=text_light, font=bold, anchor="mm")

        if not self.check(board) and 2048 in (cell for row in board for cell in row):
            frame.rounded_rectangle(xy=[(0, 0), (canvas_width, canvas_height)], radius=canvas_border_radius, fill=summary_bg)
            frame.text(xy=(font_x, font_y + cell_gap * 2), text="Game Over!", fill=text_dark, font=summary, anchor="mm")
        elif 2048 in (cell for row in board for cell in row):
            frame.rounded_rectangle(xy=[(0, 0), (canvas_width, canvas_height)], radius=canvas_border_radius, fill=summary_bg)
            frame.text(xy=(font_x, font_y + cell_gap * 2), text="You win!", fill=text_dark, font=summary, anchor="mm")

        return await self.save_image(canvas)

    # game methods

    def new_board(self):
        board = [[0 for x in range(4)] for y in range(4)]
        board = self.generate_random(board)
        board = self.generate_random(board)
        return board

    def generate_random(self, board):
        val = random.randint(0, 10)
        while True:
            row = random.randint(0, 3)
            col = random.randint(0, 3)
            if board[row][col] == 0:
                board[row][col] = 2 if val <= 8 else 4
                return board

    def check(self, board):
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return True
        # FORGIVE ME GOD, FOR I HAVE SINNED.
        if board == self.transpose(self.compress(self.merge(self.compress(self.transpose(board)))[0])) and board == self.transpose(self.reverse(self.compress(self.merge(self.compress(self.reverse(self.transpose(board))))[0]))) and board == self.compress(self.merge(self.compress(board))[0]) and board == self.reverse(self.compress(self.merge(self.compress(self.reverse(board)))[0])):
            return False
        return True

    def reverse(self, board):
        new_board = []
        for i in range(4):
            new_board.append([])
            for j in range(4):
                new_board[i].append(board[i][3-j])
        return new_board

    def transpose(self, board):
        new_board = [[0 for i in range(4)] for i in range(4)]
        for i in range(4):
            for j in range(4):
                new_board[i][j] = board[j][i]
        return new_board

    def merge(self, board):
        score = 0
        for i in range(4):
            for j in range(3):
                if board[i][j] == board[i][j+1] and board[i][j] != 0:
                    board[i][j] += board[i][j]
                    board[i][j+1] = 0
                    score = board[i][j] * 2
        return board, score

    def compress(self, board):
        new_board = [[0 for i in range(4)] for i in range(4)]
        for i in range(4):
            k = 0
            for j in range(4):
                if board[i][j] != 0:
                    new_board[i][k] = board[i][j]
                    k += 1
        return new_board

    # util methods

    async def save_image(self, img):
        file = BytesIO()
        img.save(file, "PNG", quality=100)
        file.seek(0)
        return file
