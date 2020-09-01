from PIL import Image, ImageDraw
import random

from discord.ext import commands
import discord, sheets

class BingoSheet:
    def __init__(self, size, cards, owner):
        assert len(cards) == size * size
        self.cards = cards
        self.sheet = {}
        for i in cards:
            if i == "Free Space":
                self.sheet[i] = True
            else:
                self.sheet[i] = False
        self.size = size
        self.cleared = []
        self.owner = owner

    def complete(self) -> bool:
        for i in self.sheet:
            if not self.sheet[i]:
                return False
        return True

    def fill_in(self, card) -> bool:
        # Return true if something gets filled in
        if card in self.sheet and not self.sheet[card]:
            self.sheet[card] = True
            return True
        return False

    def output_file(self, location):
        try:
            img = Image.open("BingoSheet.png")
            # Space to work in is 16,20 to 239,235
            # This is 223,215 pixel to work within
            draw = ImageDraw.Draw(img)
            # We are going to draw (size-1)*2 lines
            width = 223/self.size
            height = 215/self.size
            for i in range(1, self.size):
                currentX = 16 + (width*i)
                currentY = 20 + (height*i)
                draw.line((currentX, 20, currentX, 235), fill=155, width = 1)
                draw.line((16, currentY, 239, currentY), fill=155, width = 1)

            currentPos = 0
            for i in self.cards:
                currentX = 16 + (currentPos % self.size) * width
                currentY = 20 + int(currentPos / self.size) * height
                length = draw.textsize(i)
                if length[0] < width:
                    xOffset = (width - length[0]) / 2
                    yOffset = (height - length[1]) / 2
                    draw.text((currentX + xOffset, currentY + yOffset), i, fill=155)
                else:
                    # Multiline it!
                    # We know that the text is height 11
                    words = i.split(" ")
                    drawTexts = [""]
                    index = 0
                    wordCount = 0
                    drawTexts[index] = words[wordCount]
                    wordCount += 1
                    while wordCount < len(words):
                        if draw.textsize(drawTexts[index]+ " " + words[wordCount])[0] < width:
                            drawTexts[index] += " " + words[wordCount]
                        else:
                            drawTexts += [ words[wordCount] ]
                            index += 1
                        wordCount += 1

                    index = 0
                    startY = currentY + (height/2) - (11*(len(drawTexts)-1))
                    for line in drawTexts:
                        length = draw.textsize(line)[0]
                        xOffset = (width - length) / 2
                        draw.text((currentX+xOffset, startY+(index*11)), line, fill=155)
                        index += 1
                if self.sheet[i]:
                    draw.line((currentX, currentY, currentX+width, currentY+height), fill=10)
                    draw.line((currentX, currentY+height, currentX+width, currentY), fill=10)
                currentPos += 1

            img.save(location)
        except Exception as err:
            print("We failed to make the image!")
            print(err)

class Bingo(commands.Cog):
    def __init__(self):
        self.bingoSheets = {}
        self.all_cards = []
        self.cache = False

    async def check_cache(self):
        if not self.cache:
            self.cache = True
            await self.load_bingo_cards()

    async def load_bingo_cards(self):
        self.all_cards = await sheets.get_bingo_cards()

    async def make_sheet(self, size, user, free_space=True):
        await self.check_cache()
        if free_space and "Free Space" in self.all_cards:
            bingo_set = random.sample(self.all_cards, size*size-1)
            midpoint = int(size*size/2)
            bingo_set = bingo_set[:midpoint] + ["Free Space"] + bingo_set[midpoint:]
        else:
            bingo_set = random.sample(self.all_cards, size*size)
        self.bingoSheets[user] = BingoSheet(size, bingo_set, user)

    @commands.command()
    async def make_bingo_sheet(self, ctx, *args):
        """
        A test command to see if making a bingo sheet works!
        """
        user_id = str(ctx.author.id)
        await self.make_sheet(3, user_id)
        self.bingoSheets[user_id].output_file("testfile.png")
        await ctx.send(file=discord.File("testfile.png"))
