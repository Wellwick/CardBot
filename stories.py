from discord.ext import commands
import discord, sheets
from story import Story

class Stories(commands.Cog):
    def __init__(self):
        self.stories = {}

    async def load_story(self, user, story):
        pass

    async def do_step(self, ctx):
        story = self.stories[ctx.author.id]
        text = []
        while story.can_step():
            text += story.do_step()
        if len(text) == 0:
            text = [ "Could not progress the story. Please contact Wellwick, since this is probably a bug!" ]
        index = 0
        string = ""
        for i in text:
            if len(string) + len(i) < 1990:
                string += "\n" + i
            else:
                await ctx.send(string)
                string = ""
        await ctx.send(string)

    async def select(self, ctx, val):
        story = self.stories[ctx.author.id]
        if story.current_node.has_options():
            story.choose(val)
        self.do_step(ctx)


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
        elif args[:4] == "load":
            story = await sheets.get_story(args[4:].strip())
            self.stories[ctx.author.id] = story
            await self.do_step(ctx)
        else:
            try:
                # This is which index of the options to do
                val = int(args.strip()) - 1
            except:
                await ctx.send("Expected 'list', 'load' or a number")
                return
            await self.select(ctx, val)
