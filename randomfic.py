from discord.ext import commands
import discord
import random
from ff.fiction import Story, Chapter, User


class RandomFic(commands.Cog):
    def __init__(self):
        with open("HPFFIds.txt", "r") as f:
            ids = f.readlines()
        # Since these are all numbers, and we can store numbers easier than
        # strings, let's save some space!
        self.ids = []
        for i in ids:
            self.ids += [ int(i) ]

    @commands.command()
    async def quote(self, ctx, linecount=3):
        '''Pulls a random quote from a HP story somewhere on fanfiction.net!
        - Change linecount to decide how long you want the quote to be
        '''
        if linecount != 3:
            try:
                linecount = int(linecount)
            except:
                linecount = 3
        
        story = Story(id=random.choice(self.ids))
        story.download_data()

        chapter_val = random.randrange(story.chapter_count) + 1

        chapter = Chapter(story_id=story.id, chapter=chapter_val)

        author = User(id=story.author_id)
        author.download_data()

        info = f"> **{story.title}** by *{author.username}*\n"
        info += f"> Link: *<{story.url}>*\n"
        info += f"> Chapter {chapter_val}"

        lines = chapter.text.split("\n")

        guess_lines = []
        current_line = ""
        for line in lines:
            if len(line.strip()) == 0:
                guess_lines += [ current_line ]
                current_line = ""
                continue
            if line.strip()[-1] not in [".", "!", "?", '"', "'", ")", "]"]:
                current_line += line.strip() + " "
            elif current_line != "":
                current_line += line.strip()
                guess_lines += [ current_line ]
                current_line = ""
            else:
                guess_lines += [ line ]

        if linecount >= len(guess_lines):
            print_lines = guess_lines
        else:
            lineIndex = random.randrange(len(guess_lines)-linecount)
            print_lines = guess_lines[lineIndex:lineIndex+linecount]

        current_string = ""
        index = 0
        for line in print_lines:
            new_line = f"{current_line}\n\n{line}"
            if len(new_line) < 2000:
                current_line = new_line
            else:
                await ctx.send(current_line)
                current_line = f"> {line}"
        
        new_line = f"{current_line}\n\n{info}"
        if len(new_line) < 2000:
            await ctx.send(new_line)
        else:
            await ctx.send(current_line)
            await ctx.send(info)

