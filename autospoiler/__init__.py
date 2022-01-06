from .autospoiler import Autospoiler

def setup(bot):
    bot.add_cog(Autospoiler(bot))
