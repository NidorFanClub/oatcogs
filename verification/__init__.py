from .verification import Verification
from discord_components import DiscordComponents

def setup(bot):
    DiscordComponents(bot)
    bot.add_cog(Verification(bot))
