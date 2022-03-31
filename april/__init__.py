from .greetings import Greetings

def setup(bot):
    bot.add_cog(Greetings(bot))
