from .verification import Verification

def setup(bot):
    bot.add_cog(Verification(bot))
