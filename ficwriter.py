from discord.ext import commands
import discord, sheets
import random, datetime, asyncio

class FicWriter(commands.Cog):
    def __init__(self, cards):
        # Use the cards in the other 
        self.cards = cards
        self.writing = {}
        self.plot_points = []
        self.cache = False

    async def check_cache(self):
        if not self.cache:
            self.cache = True
            await self.load_plot_points()

    async def load_plot_points(self):
        pass # Don't have these yet!

    async def setup(self, user, rounds, timeout, title, channel):
        self.writing["open"] = {
            "rounds": rounds,
            "timeout": timeout,
            "title": title,
            "channel": channel,
            "c_round": 0,
            "p_index": 0,
            "players": [ user ],
            "messages": [],
            "written": []
        }
        await channel.send("Game setup! You are added, everyone else can `%f join` now! Type `%f start` to get going!")
    
    async def start(self):
        # We know that whatever is in "open" goes to ["players"][0]
        user = self.writing["open"]["players"][0]
        self.writing[user] = self.writing["open"]
        for i in self.writing[user]["players"]:
            self.writing[user]["written"] += [ False ]
        del self.writing["open"]
        await self.next_round(user)

    async def complete(self, user):
        messages = ["All rounds complete! Here's your fic:\n"]
        index = 0
        m = self.writing[user]["messages"]
        for i in m:
            if len(messages[index] + i + " ") > 1800:
                messages += [""]
                index += 1
            messages[index] += i + " "
        for i in messages:
            await self.writing[user]["channel"].send(i)
        del self.writing[user]

    async def next_round(self, user):
        write = self.writing[user]
        write["c_round"] += 1
        if write["c_round"] > write["rounds"]:
            await self.complete(user)
            return
        
        message = "We're now on round {}/{}. Here's the order for this round!\n".format(write["c_round"],write["rounds"])
        # Shuffle the players! Can't have the last player from last round be the first in this
        last = write["players"][-1]
        random.shuffle(write["players"])
        if last == write["players"][0]:
            write["players"].remove(last)
            write["players"] += [ last ]
        for i in range(0, len(write["players"])):
            write["written"][i] = False
            message += "{} - {}\n".format(i+1, write["players"][i].mention)

        await write["channel"].send(message)

        write["p_index"] = -1
        await self.next_write(user)

    async def next_write(self, user):
        write = self.writing[user]
        if write["p_index"] == len(write["players"])-1:
            return await self.next_round(user)
        write["p_index"] += 1
        index = write["p_index"]
        c_round = write["c_round"]
        who = write["players"][index]
        message = "It's your turn to add a sentence! "
        if len(write["messages"]) > 0:
            message += "Here is the previous sentence: \n**{}**\n".format(write["messages"][-1])
        else:
            message += "It's the very first one, so start it however you like!\n"
        message += "Make your sentence by doing `%f This is your sentence.` "
        timeout = write["timeout"]
        message += "You have {} seconds to write your sentence or things will time out!".format(timeout)
        await who.send(message)
        # Let's give them a warning at each minute, 30 seconds and 10 seconds
        countdown = timeout
        while countdown > 60:
            t = countdown % 60
            if t == 0:
                t = 60
            countdown -= t
            await asyncio.sleep(t)
            if write["written"][index] or write["c_round"] != c_round:
                return
            await who.send("You have {} minutes left to write".format(countdown/60))
        while countdown > 30:
            t = countdown - 30
            countdown -= t
            await asyncio.sleep(t)
            if write["written"][index] or write["c_round"] != c_round:
                return
            await who.send("You have {} seconds left to write".format(countdown))
        while countdown > 10:
            t = countdown - 10
            countdown -= t
            await asyncio.sleep(t)
            if write["written"][index] or write["c_round"] != c_round:
                return
            await who.send("You have {} seconds left to write".format(countdown))
        await asyncio.sleep(countdown)
        if write["written"][index] or write["c_round"] != c_round:
            return
        await who.send("You've run out of time to write! Moving on to the next person")
        await self.next_write(user)




    @commands.command()
    async def f(self, ctx, *args):
        '''Fic writing minigame thing. See %help f for how to play.
            %f setup rounds=number timeout=seconds title="whatever" - Setup the start of a game. Default is one round, 60 second timeout and no title
            %f join - Join a game that's in it's setup phase
            %f leave - Leave a game in progress
            %f start - The person who setup the writing minigame can start a minigame
            %f <sentence> - Write your sentence when it's your turn (don't include those <>!)
            When the game begins, the bot will PM you when it's your turn
        '''
        await self.cards.check_cache(ctx)
        await self.check_cache()
        if len(args) == 0:
            await ctx.send("Have a look at `%help f`")
            return
        # Wellwick, Kim, sequoia
        resetters = ["227834498019098624","347524359830634496","472241913467240449"]
        user = ctx.author
        command = args[0]
        if command == "setup":
            if user in self.writing:
                await ctx.send("You're already running a minific writing game!")
                return
            if "open" in self.writing:
                await ctx.send("Another minific writing game is already in the setup phase! You can `%f join` it now")
                return
            rounds=1
            timeout=60
            title=""
            tracking_title=False
            for i in args[1:]:
                if tracking_title:
                    title += i
                    if i[-1] == '"':
                        title = title[:-1]
                        tracking_title = False
                else:
                    if i.startswith("rounds="):
                        rounds = int(i[7:])
                    elif i.startswith("timeout="):
                        timeout = int(i[8:])
                    elif i.startswith("title=\""):
                        tracking_title = True
                        title = i[7:]
                    else:
                        await ctx.send("Unrecognised setup command, have a look at `%help f`")
            await self.setup(user, rounds, timeout, title, ctx.message.channel)
        elif command == "join":
            if "open" in self.writing:
                self.writing["open"]["players"] += [ user ]
                await ctx.send("You've been added ")
            else:
                await ctx.send("There isn't a game currently accepting players. Maybe you could start one with `%f setup`")
        elif command == "leave":
            if "open" in self.writing and user in self.writing["open"]["players"][1:]:
                self.writing["open"]["players"].remove(user)
                await ctx.send("You've been removed from the current minific game")
            else:
                for i in self.writing:
                    write = self.writing[i]
                    if user in write["players"]:
                        index = write["players"].index(user)
                        go_next = index == write["p_index"]
                        if index <= write["p_index"]:
                            write["p_index"] -= 1
                        write["players"].remove(user)
                        write["written"].pop(index)
                        await ctx.send("You've been removed from the a minific game")
                        if go_next:
                            # The current player has decided to leave!
                            await self.next_write(user)
                        return
                await ctx.send("Sorry, failed to remove you from any minific games")
        elif command == "start":
            if "open" in self.writing and user == self.writing["open"]["players"][0]:
                await self.start()
            else:
                await ctx.send("You haven't run `%f setup`!")
        elif command == "reset" and str(user.id) in resetters:
            self.writing = {}
            await ctx.send("All writing games have been reset!")
        else:
            s = ""
            for i in args:
                s += i + " "
            s = s[:-1]
            for i in self.writing:
                if i == "open":
                    continue
                write = self.writing[i]
                if user in write["players"] and write["p_index"] == write["players"].index(user):
                    write["messages"] += [ s ]
                    write["written"][write["players"].index(user)] = True
                    await ctx.send("Thanks for posting!")
                    await self.next_write(i)
                    return
            await ctx.send("Sorry, not expecting you to post a sentence right now!")

