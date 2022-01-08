from .verification import Verification

def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Verification(bot))
