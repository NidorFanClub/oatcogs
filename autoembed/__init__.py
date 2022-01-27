from .autoembed import Autoembed

def setup(bot):
    bot.add_cog(Autoembed(bot))
