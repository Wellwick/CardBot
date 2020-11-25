from discord.ext import commands
import discord, sheets
import random, datetime, asyncio

class FicWriter(commands.Cog):
    def __init__(self, cards):
        # Use the cards in the other 
        self.cards = cards
        self.writing = {}
        self.bunnies = []
        self.morphologische = {}
        self.cache = False

    async def check_cache(self):
        if not self.cache:
            self.cache = True
            await self.load_bunnies()
            await self.load_morphologische()

    async def load_bunnies(self):
        self.bunnies = await sheets.get_bunnies()

    async def load_morphologische(self):
        self.morphologische = await sheets.get_morphologische()

    async def player_present(self, user, player):
        for i in self.writing[user]["players"]:
            if i["player"] == player:
                return True
        return False

    async def setup(self, user, rounds, timeout, title, channel):
        self.writing["open"] = {
            "rounds": rounds,
            "timeout": timeout,
            "title": title,
            "channel": channel,
            "c_round": 0,
            "p_index": 0,
            "players": [ 
                { "player": user, "written": False, "bunny": "" }
            ],
            "messages": [],
        }
        await channel.send("Game setup! You are added, everyone else can `%f join` now! Type `%f start` to get going!")
    
    async def start(self):
        # We know that whatever is in "open" goes to ["players"][0]
        user = self.writing["open"]["players"][0]["player"]
        self.writing[user] = self.writing["open"]
        bunnies = self.bunnies.copy()
        for i in self.writing[user]["players"]:
            b_index = random.randrange(0,len(bunnies))
            i["bunny"] = bunnies[b_index]
            bunnies.pop(b_index)
            if len(bunnies) == 0:
                bunnies = self.bunnies.copy()
        del self.writing["open"]
        await self.next_round(user)

    async def complete(self, user):
        all_players = ""
        for i in self.writing[user]["players"]:
            all_players += i["player"].mention + " "
        messages = ["{}All rounds complete! Bonus cards have been sent out for each sentence you have written. Here's your fic: ".format(all_players)]
        if self.writing[user]["title"] != "":
            messages[0] += "**{}**".format(self.writing[user]["title"])
        messages[0] += "\n"
        index = 0
        m = self.writing[user]["messages"]
        bold = False
        for i in m:
            if len(messages[index] + i + " ") > 1800:
                messages += [""]
                index += 1
            if bold:
                messages[index] += "**{}** ".format(i)
            else:
                messages[index] += "{} ".format(i)
            bold = not bold
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
            write["players"][i]["written"] = False
            message += "{} - {}\n".format(i+1, write["players"][i]["player"].mention)

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
        who = write["players"][index]["player"]
        message = "It's your turn to add a sentence! Your plot point to try and get in is `{}`".format(write["players"][index]["bunny"])
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
            if write["players"][index]["written"] or write["c_round"] != c_round:
                return
            await who.send("You have {} minutes left to write".format(countdown/60))
        while countdown > 30:
            t = countdown - 30
            countdown -= t
            await asyncio.sleep(t)
            if write["players"][index]["written"] or write["c_round"] != c_round:
                return
            await who.send("You have {} seconds left to write".format(countdown))
        while countdown > 10:
            t = countdown - 10
            countdown -= t
            await asyncio.sleep(t)
            if write["players"][index]["written"] or write["c_round"] != c_round:
                return
            await who.send("You have {} seconds left to write".format(countdown))
        await asyncio.sleep(countdown)
        if write["players"][index]["written"] or write["c_round"] != c_round:
            return
        await who.send("You've run out of time to write! Moving on to the next person")
        await self.next_write(user)

    @commands.command()
    async def f(self, ctx, *, arguments):
        '''Fic writing minigame thing. See %help f for how to play.
            %f setup rounds=number timeout=seconds title="whatever" - Setup the start of a game. Default is one round, 2 minutes 30 second timeout and no title
            %f join - Join a game that's in it's setup phase
            %f leave - Leave a game in progress
            %f start - The person who setup the writing minigame can start a minigame
            %f <sentence> - Write your sentence when it's your turn (don't include those <>!)
            When the game begins, the bot will PM you when it's your turn
        '''
        await self.cards.check_cache(ctx)
        await self.check_cache()
        args = arguments.split(" ")
        while "" in args:
            args.remove("")
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
            timeout=150
            title=""
            tracking_title=False
            for i in args[1:]:
                if tracking_title:
                    title += i + " "
                    if i[-1] == '"':
                        title = title[:-2]
                        tracking_title = False
                else:
                    if i.startswith("rounds="):
                        rounds = int(i[7:])
                    elif i.startswith("timeout="):
                        timeout = int(i[8:])
                    elif i.startswith("title=\""):
                        tracking_title = True
                        title = i[7:] + " "
                    else:
                        await ctx.send("Unrecognised setup command, have a look at `%help f`")
            await self.setup(user, rounds, timeout, title, ctx.message.channel)
        elif command == "join":
            if "open" in self.writing and not await self.player_present("open", user):
                self.writing["open"]["players"] += [ {"player": user, "written": False, "bunny": ""} ]
                await ctx.send("You've been added")
            else:
                await ctx.send("There isn't a game currently accepting players. Maybe you could start one with `%f setup`")
        elif command == "leave":
            if "open" in self.writing and user in self.writing["open"]["players"][1:]:
                for i in self.writing["open"]["players"]:
                    if i["player"] == user:
                        self.writing["open"]["players"].remove(i)
                await ctx.send("You've been removed from the current minific game")
            else:
                for i in self.writing:
                    write = self.writing[i]
                    if await self.player_present(i, user):
                        for j in range(0, len(self.writing[i]["players"])):
                            if self.writing[i]["players"][j]["player"] == user:
                                index = j
                                break
                        go_next = index == write["p_index"]
                        if index <= write["p_index"]:
                            write["p_index"] -= 1
                        write["players"].remove(user)
                        await ctx.send("You've been removed from the a minific game")
                        if go_next:
                            # The current player has decided to leave!
                            await self.next_write(user)
                        return
                await ctx.send("Sorry, failed to remove you from any minific games")
        elif command == "start":
            if "open" in self.writing and user == self.writing["open"]["players"][0]["player"]:
                await self.start()
            else:
                await ctx.send("You haven't run `%f setup`!")
        elif command == "reset" and str(user.id) in resetters:
            self.writing = {}
            await ctx.send("All writing games have been reset!")
        elif command == "recache" and str(user.id) in resetters:
            await self.load_bunnies()
        else:
            s = arguments
            for i in self.writing:
                if i == "open":
                    continue
                write = self.writing[i]
                if await self.player_present(i, user) and write["players"][write["p_index"]]["player"] == user:
                    write["messages"] += [ s ]
                    write["players"][write["p_index"]]["written"] = True
                    await ctx.send("Thanks for posting!")
                    # Give them a bonus card per round
                    await self.cards.grant(str(user.id), 1)
                    await self.next_write(i)
                    return
            await ctx.send("Sorry, not expecting you to post a sentence right now!")

    def multiply_string(self, string, multiple):
        new_string = ""
        for i in range(0,multiple):
            new_string += string
            
        return new_string

    @commands.command()
    async def prompt(self, ctx, *args):
        '''Produce a prompt for your writing
            %prompt - Produce a random prompt
            %prompt 3 - Produce a table of 3 (or any number) of rows of prompt options
            %prompt recache - Reload things from the spreadsheet https://docs.google.com/spreadsheets/d/1MYxwMMXpNfx22gsbPmKLlkPh30NZNXeKSMBo96s7knc/edit#gid=993001934
        '''
        await self.check_cache()
        if len(args) == 1:
            if args[0].lower() == "recache":
                await self.load_morphologische()
                await ctx.send("Recache complete!")
                return
            try:
                rows = int(args[0])

                if len(self.morphologische["character"]) < rows:
                    random.shuffle(self.morphologische["character"])
                    pair1 = self.morphologische["character"]
                    random.shuffle(self.morphologische["character"])
                    pair2 = self.morphologische["character"]
                    for i in range(len(self.morphologische["character"]), rows):
                        pair1 += [""]
                        pair2 += [""]
                else:
                    pair1 = random.sample(self.morphologische["character"], rows)
                    pair2 = random.sample(self.morphologische["character"], rows)
                
                if len(self.morphologische["obstacle"]) < rows:
                    random.shuffle(self.morphologische["obstacle"])
                    obstacle = self.morphologische["obstacle"]
                    for i in range(len(self.morphologische["obstacle"]), rows):
                        obstacle += [""]
                else:
                    obstacle = random.sample(self.morphologische["obstacle"], rows)
                
                if len(self.morphologische["place"]) < rows:
                    random.shuffle(self.morphologische["place"])
                    place = self.morphologische["place"]
                    for i in range(len(self.morphologische["place"]), rows):
                        place += [""]
                else:
                    place = random.sample(self.morphologische["place"], rows)
                
                if len(self.morphologische["time"]) < rows:
                    random.shuffle(self.morphologische["time"])
                    time = self.morphologische["time"]
                    for i in range(len(self.morphologische["time"]), rows):
                        time += [""]
                else:
                    time = random.sample(self.morphologische["time"], rows)
                
                if len(self.morphologische["object"]) < rows:
                    random.shuffle(self.morphologische["object"])
                    objects = self.morphologische["object"]
                    for i in range(len(self.morphologische["object"]), rows):
                        objects += [""]
                else:
                    objects = random.sample(self.morphologische["object"], rows)

                max_pair1 = len(max(pair1 + ["Character 1"], key=len)) + 1
                max_pair2 = len(max(pair2 + ["Character 2"], key=len)) + 1
                max_obstacle = len(max(obstacle + ["Obstacle"], key=len)) + 1
                max_place = len(max(place + ["Place"], key=len)) + 1
                max_time = len(max(time + ["Time"], key=len)) + 1
                max_object = len(max(objects + ["Object"], key=len)) + 1
                row_length = max_pair1 + max_pair2 + max_obstacle + max_place + max_time + max_object + 11

                output = "``` Character 1"
                output += self.multiply_string(" ", max_pair1 - 11) + "| "
                output += "Character 2"
                output += self.multiply_string(" ", max_pair2 - 11) + "| "
                output += "Obstacle"
                output += self.multiply_string(" ", max_obstacle - 8) + "| "
                output += "Place"
                output += self.multiply_string(" ", max_place - 5) + "| "
                output += "Time"
                output += self.multiply_string(" ", max_time - 4) + "| "
                output += "Object"
                output += self.multiply_string(" ", max_object - 6) + "\n"
                output += self.multiply_string("-", row_length) + "\n "
                for i in range(0,rows):
                    # Check if the row is empty
                    if pair1[i] == pair2[i] == obstacle[i] == place[i] == time[i] == objects[i] == "":
                        break
                    if len(output) + row_length > 1996:
                        output += "```"
                        await ctx.send(output)
                        output = "``` "
                    output += pair1[i]
                    output += self.multiply_string(" ", max_pair1 - len(pair1[i])) + "| "
                    output += pair2[i]
                    output += self.multiply_string(" ", max_pair2 - len(pair2[i])) + "| "
                    output += obstacle[i]
                    output += self.multiply_string(" ", max_obstacle - len(obstacle[i])) + "| "
                    output += place[i]
                    output += self.multiply_string(" ", max_place - len(place[i])) + "| "
                    output += time[i]
                    output += self.multiply_string(" ", max_time - len(time[i])) + "| "
                    output += objects[i]
                    output += self.multiply_string(" ", max_object - len(objects[i])) + "\n "
                    
                output += "```"
                await ctx.send(output)
            except:
                await ctx.send("Failed to make this many table rows")
        else:
            pair1 = random.choice(self.morphologische["character"])
            pair2 = random.choice(self.morphologische["character"])
            obstacle = random.choice(self.morphologische["obstacle"])
            place = random.choice(self.morphologische["place"])
            time = random.choice(self.morphologische["time"])
            c_object = random.choice(self.morphologische["object"])
            output = f"> **Characters**: {pair1}, {pair2}\n"
            output += f"> **Obstacle**: {obstacle}\n"
            output += f"> **Place**: {place}\n"
            output += f"> **Time**: {time}\n"
            output += f"> **Object**: {c_object}\n"
            await ctx.send(output)

