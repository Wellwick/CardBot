from discord.ext import commands
import discord, sheets
from story import Story

class Stories(commands.Cog):
    def __init__(self):
        self.stories = {}

    async def load_story(self, user, story):
        pass

    @commands.command()
    async def s(self, ctx, *, args):
        '''Play through an adventure story.
            %s list - Get a list of the available stories
            %s load Story Name - Load in a story
            %s ## - Choose a numbered option in the story
        '''
        if args[:4] == "list":
            stories = await sheets.get_stories()
            await ctx.send("Here is a list of the available stories:\n**" + "**, ".join(stories) + "**")

