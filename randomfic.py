from discord.ext import commands
import discord
import random
from ff.fiction import Story, Chapter, User
import AO3

class RandomFic(commands.Cog):
    def __init__(self):
        with open("HPFFIds.txt", "r") as f:
            ids = f.readlines()
        # Since these are all numbers, and we can store numbers easier than
        # strings, let's save some space!
        self.ffids = []
        for i in ids:
            self.ffids += [ int(i) ]

        with open("HPAO3Ids.txt", "r") as f:
            ids = f.readlines()

        self.ao3ids = []
        for i in ids:
            self.ao3ids += [ int(i) ]

    def ffPickChapter(self, story):
        return random.randrange(story.chapter_count) + 1

    def ffInfo(self, story, chapter):
        author = User(id=story.author_id)
        author.download_data()

        info = f"> **{story.title}** by *{author.username}*\n"
        info += f"> Link: *<{story.url}>*\n"
        info += f"> Chapter {chapter}"
        return info

    def ffChapterLines(self, story, chapter):
        chapter = Chapter(story_id=story.id, chapter=chapter)
        return chapter.text.split("\n")

    def ao3PickChapter(self, work):
        return random.randrange(len(work.chapter_names)) + 1

    def ao3Info(self, work, chapter):
        authors = work.authors[0].username
        for i in work.authors[1:]:
            authors += f", {i.username}"

        info = f"> **{work.title}** by *{authors}*\n"
        info += f"> Link: *<{work.url}>*\n"
        info += f"> Chapter {chapter}"
        return info

    def ao3ChapterLines(self, work, chapter):
        return work.get_chapter_text(chapter).split("\n")

    @commands.command()
    async def quote(self, ctx, website="any", linecount=3):
        '''Pulls a random quote from a HP story somewhere on fanfiction.net!
        - Change linecount to decide how long you want the quote to be
        - Change website to ao3 or ff to only get things from ao3 or fanfiction.net
        '''
        if linecount != 3:
            try:
                linecount = int(linecount)
            except:
                linecount = 3

        if website.lower() == "any":
            counter = random.randrange(len(self.ffids) + len(self.ao3ids))
            if counter >= len(self.ffids):
                counter -= len(self.ffids)
                work = AO3.Work(self.ao3ids[counter])
                chapter = self.ao3PickChapter(work)
                info = self.ao3Info(work, chapter)
                lines = self.ao3ChapterLines(work, chapter)
            else:
                story = Story(id=self.ffids[counter])
                story.download_data()
                chapter = self.ffPickChapter(story)
                info = self.ffInfo(story, chapter)
                lines = self.ffChapterLines(story, chapter)

        elif website.lower() == "ff":
            story = Story(id=random.choice(self.ffids))
            story.download_data()
            chapter = self.ffPickChapter(story)
            info = self.ffInfo(story, chapter)
            lines = self.ffChapterLines(story, chapter)
        elif website.lower() == "ao3":
            work = AO3.Work(random.choice(self.ao3ids))
            chapter = self.ao3PickChapter(work)
            info = self.ao3Info(work, chapter)
            lines = self.ao3ChapterLines(work, chapter)
        else:
            await ctx.send("Don't recognise name for website!")
            return

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
                current_line = f"{line}"
        
        new_line = f"{current_line}\n\n{info}"
        if len(new_line) < 2000:
            await ctx.send(new_line)
        else:
            await ctx.send(current_line)
            await ctx.send(info)

