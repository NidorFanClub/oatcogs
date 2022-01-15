from .wordle import Wordle

def setup(bot):
    bot.add_cog(Wordle(bot))
