from discord.ext import commands
import discord, sheets
import random, datetime, difflib

class Card:
    def __init__(
        self,
        name,
        role,
        house,
        rarity,
        ctype,
        era,
        tagline,
        relevant,
        submitter
    ):
        self.name = name.strip()
        self.role = role.strip()
        self.house = house.strip()
        self.rarity = rarity.strip()
        self.type = ctype.strip()
        self.era = era.strip()
        self.tagline = tagline.strip()
        self.submitter = submitter.strip()
        if relevant == "None":
            self.relevant = ""
        else:
            self.relevant = relevant.strip()

class Cards(commands.Cog):

    def __init__(self):
        self.cardlist = []
        self.trading = {}
        self.claims = {}
        self.bonus_claim = {}
        self.trades = {}
        self.cached = False
        self.pause = False

    async def set_local_cache(self):
        await self.load_cards()
        await self.load_owners()
        self.cached = True

    async def load_cards(self):
        cards = (await sheets.trading_cards())
        for card in cards:
            new_card = Card(*card)
            self.cardlist += [ new_card ]

    async def load_owners(self):
        card_owns = (await sheets.owned_cards())
        for card in card_owns:
            if not card[0] in self.trading:
                self.trading[card[0]] = []
            self.trading[card[0]] += [self.cardlist[int(card[1])]]

    async def random_claim(self, ctx, claimer_id):
        # Check if this person has already claimed today
        day = datetime.datetime.now().day
        if not day in self.claims:
            self.claims = {day: []}

        if claimer_id in self.claims[day] and claimer_id not in self.bonus_claim:
            if datetime.datetime.now().hour == 23:
                timeleft = "{} minutes".format(60-datetime.datetime.now().minute)
            else:
                timeleft = "{} hours".format(24-datetime.datetime.now().hour)
            await ctx.send("You have already made your daily claim! Next claim available in {}".format(timeleft))
            return

        amount = 0
        if claimer_id in self.bonus_claim:
            await ctx.send("Claiming {} bonus cards".format(self.bonus_claim[claimer_id]))
            amount += self.bonus_claim[claimer_id]
        if not claimer_id in self.claims[day]:
            amount += 1

        total = 0
        for i in self.cardlist:
            if i.rarity == "Common":
                total += 27
            elif i.rarity == "Uncommon":
                total += 9
            elif i.rarity == "Rare":
                total += 3
            elif i.rarity == "Legendary":
                total += 1
        selectedValues = []
        for i in range(0, amount):
            selectedValues += [ random.randrange(0,total) ]
        collected = ""
        for selectedValue in selectedValues:
            counting = 0
            card = None
            for i in self.cardlist:
                if i.rarity == "Common":
                    val_to_add = 27
                elif i.rarity == "Uncommon":
                    val_to_add = 9
                elif i.rarity == "Rare":
                    val_to_add = 3
                elif i.rarity == "Legendary":
                    val_to_add = 1
                if selectedValue >= counting and selectedValue < counting + val_to_add:
                    card = i
                    break
                else:
                    counting += val_to_add
            # If we didn't find a card, make it the last one!
            if card == None:
                card = self.cardlist[-1]
            if not claimer_id in self.trading:
                self.trading[claimer_id] = []
            await sheets.gain_card(claimer_id, self.cardlist.index(card))
            self.trading[claimer_id] += [card]
            collected += card.name + ", "
        await ctx.send("You gained the card for {}".format(collected[:-2]))
        if not claimer_id in self.claims[day]:
            self.claims[day] += [ claimer_id ]
        if claimer_id in self.bonus_claim:
            del self.bonus_claim[claimer_id]

    async def view_card(self, ctx, card):
        message =   "**{}**\n".format(card.name)
        message +=  "> ***{}***\n".format(card.tagline)
        message +=  "> Rarity: **{}**\n".format(card.rarity)
        if card.role != "None":
            message += "> Role: {}\n".format(card.role)
        if card.house != "None":
            message += "> House: {}\n".format(card.house)
        message +=  "> Type: {}\n".format(card.type)
        message +=  "> Era: **{}**\n".format(card.era)
        if card.relevant != "":
            message += "> Relevant Fic: {}".format(card.relevant)
        await ctx.send(message)

    async def messagify_ownership(self, user, c_list, c_filter = ""):
        if c_filter != "":
            c_filter = " **{}** ".format(c_filter)
        owned_cards = 0
        owned = {}
        if user in self.trading:
            for i in self.trading[user]:
                if i in c_list:
                    owned_cards += 1
                    if not i.name in owned:
                        owned[i.name] = 0
                    owned[i.name] += 1
        initial = "You own {}{} cards\n".format(owned_cards,c_filter[:-1])
        m_index = 0
        messages = ["> "]
        for i in owned:
            messages[m_index] += i
            if owned[i] > 1:
                messages[m_index] += "x{}".format(owned[i])
            messages[m_index] += ", "
            if len(messages[m_index]) > 1800: # Don't let it get too long
                messages[m_index] = messages[m_index][:-1]
                m_index += 1
                messages += ["> "]
        messages[m_index] = messages[m_index][:-2]
        
        messages[0] = "{}{}Cards collected {}/{}\n{}".format(initial, c_filter,len(owned),len(c_list),messages[0])
        return messages

    async def view(self, ctx, owner, *args):
        if not owner in self.trading:
            await ctx.send("You own no cards")
            return
        if len(args) == 0:
            # Let's display all cards
            messages = (await self.messagify_ownership(owner, self.cardlist))
            for i in messages:
                await ctx.send(i)
        else:
            name = ""
            for i in args:
                name += "{} ".format(i)
            name = name[:-1]
            cards_owned = []
            for i in self.trading[owner]:
                if i.name.lower() == name.lower():
                    return await self.view_card(ctx, i)
                if not i.name in cards_owned:
                    cards_owned += [ i.name ]
            
            closestCards = difflib.get_close_matches(name, cards_owned)
            if len(closestCards) > 1:
                await ctx.send("That card could not be found, did you mean one of: " + closestCards)
            elif len(closestCards) == 1:
                await ctx.send("That card could not be found, did you mean " + closestCards[0])
            else:
                await ctx.send("You don't own that that card!")

    async def get_card(self, name):
        for i in self.cardlist:
            if i.name.lower() == name.lower():
                return i

    async def at_to_id(self, at):
        at = at.replace("<", "")
        at = at.replace("@", "")
        at = at.replace("!", "")
        at = at.replace(">", "")
        return at.strip()

    async def has_cards(self, user, cards):
        # Cards comes in as an array of strings
        if len(cards) == 0:
            # You always have some of nothing!
            return True
        if user not in self.trading:
            # Can't have the required cards if they have nothing
            return False
        card_dict = {}
        for i in self.trading[user]:
            if not i.name in card_dict:
                card_dict[i.name] = 0
            card_dict[i.name] += 1
        for i in cards:
            if i in card_dict and card_dict[i] > 0:
                card_dict[i] -= 1
            else:
                return False

        return True
        

    async def trade(self, ctx, user, subaction, *args):
        if len(args) > 0 and (await self.at_to_id(args[0])) == user:
            await ctx.send("Trading with yourself just don't make sense...")
            return
        if subaction ==  "help":
            message = "**Trading commands:**\n```"
            message += "%tc trade offer @username [Card you have, Another card you have] [Card they have, another card they have] - Make an offer to someone\n"
            message += "%tc trade view - View all open trades you have\n"
            message += "%tc trade view @username - View an offer someone has made/you have made to them\n"
            message += "%tc trade cancel @username - Cancel a trade you have with someone\n"
            message += "%tc trade reject @username - Reject a trade someone has made to you\n"
            message += "%tc trade accept @username - Accept an open trade you have with someone\n"
            message += "```"
            await ctx.send(message)
        elif subaction == "offer":
            if args[0] == "help":
                message = "Specify who you want to trade with, your offer in parenthesis, then what you want back\n"
                message += "`    %tc trade offer @someperson [My Card, My Other Card] [Their Card, Another of their cards, a third card of theirs]`"
                await ctx.send(message)
                return 

            # First arg will be a person
            request_to_id = (await self.at_to_id(args[0]))
            # Make sure an existing offer with them doesn't already exist
            if (user in self.trades and request_to_id in self.trades[user]) or (request_to_id in self.trades and user in self.trades[request_to_id]):
                await ctx.send("Already have a trade proposed with them! Will have to cancel or reject trade to start a new one.")
                await self.trade(ctx, user, "view", *args[0:1])
                return
            offers = ""
            for i in args[1:]:
                offers += i + " "
            
            offer, desire, nil = offers.split("]")
            nil, offer = offer.split("[")
            offer = offer.split(",")
            nil, desire = desire.split("[")
            desire = desire.split(",")

            if len(offer) == 1 and offer[0] == "":
                offer = []
            if len(desire) == 1 and desire[0] == "":
                desire = []
            if len(offer) == 0 and len(desire) == 0:
                await ctx.send("You can't trade nothing for nothing, that's just silly")
                return

            for i in range(0, len(offer)):
                offer[i] = offer[i].strip()

            for i in range(0, len(desire)):
                desire[i] = desire[i].strip()
            
            # Check whether they even both have the required cards
            if not (await self.has_cards(user, offer)):
                await ctx.send("You do not have the cards required to trade!")
            elif not (await self.has_cards(request_to_id, desire)):
                await ctx.send("They don't have the cards you want!")
            else:
                if not user in self.trades:
                    self.trades[user] = {}
                self.trades[user][request_to_id] = [offer, desire]
                await ctx.send("Offer made")
        elif subaction == "view":
            if len(args) == 0:
                open_offers = ""
                for i in self.trades:
                    if user == i:
                        for j in self.trades[i]:
                            open_offers += "<@!{}>, ".format(j)
                    elif user in self.trades[i]:
                        open_offers += "<@!{}>, ".format(i)
                if open_offers == "":
                    await ctx.send("Don't have any open trades")
                else:
                    await ctx.send("Have open trades with {}".format(open_offers[:-2]))
            request_to_id = (await self.at_to_id(args[0]))
            if user in self.trades and request_to_id in self.trades[user]:
                offer = self.trades[user][request_to_id][0]
                o = "["
                for i in offer:
                    o += i + ", "
                o = o[:-2] + "]"
                if len(offer) == 0:
                    o = "nothing"
                
                desire = self.trades[user][request_to_id][1]
                d = "["
                for i in desire:
                    d += i + ", "
                d = d[:-2] + "]"
                if len(desire) == 0:
                    d = "nothing"

                message = "You offered to trade {} for their {}\nYou can cancel this trade with `%tc trade cancel @username`".format(o, d)
                await ctx.send(message)
            elif request_to_id in self.trades and user in self.trades[request_to_id]:
                offer = self.trades[request_to_id][user][0]
                o = "["
                for i in offer:
                    o += i + ", "
                o = o[:-2] + "]"
                if len(offer) == 0:
                    o = "nothing"

                desire = self.trades[request_to_id][user][1]
                d = "["
                for i in desire:
                    d += i + ", "
                d = d[:-2] + "]"
                if len(desire) == 0:
                    d = "nothing"

                message = "They offered to trade {} for your {}\nYou can reject this trade with `%tc trade reject @username`".format(o, d)
                await ctx.send(message)
            else:
                await ctx.send("Found no trade offer between the two of you")
        elif subaction == "accept":
            request_to_id = (await self.at_to_id(args[0]))
            if request_to_id in self.trades and user in self.trades[request_to_id]:
                offer = self.trades[request_to_id][user][0]
                desire = self.trades[request_to_id][user][1]
                if not (await self.has_cards(request_to_id, offer)):
                    await ctx.send("They no longer have the required cards! Trade cancelled")
                    del self.trades[request_to_id][user]
                elif not (await self.has_cards(user, desire)):
                    await ctx.send("You no longer have the required cards! Trade cancelled")
                    del self.trades[request_to_id][user]
                else:
                    offer_indexes = []
                    for i in offer:
                        card = await self.get_card(i)
                        self.trading[request_to_id].remove(card)
                        self.trading[user] += [card]
                        offer_indexes += [ self.cardlist.index(card) ]
                    
                    await sheets.move_card_owner(request_to_id, user, offer_indexes)

                    desire_indexes = []
                    for i in desire:
                        card = await self.get_card(i)
                        self.trading[user].remove(card)
                        self.trading[request_to_id] += [card]
                        desire_indexes += [ self.cardlist.index(card) ]
                    
                    await sheets.move_card_owner(user, request_to_id, desire_indexes)

                    await ctx.send("Trade made!")
                    del self.trades[request_to_id][user]
                    return
            else:
                await ctx.send("They haven't sent you a trade")
        elif subaction == "reject" or subaction == "cancel":
            request_to_id = (await self.at_to_id(args[0]))
            if user in self.trades and request_to_id in self.trades[user]:
                del self.trades[user][request_to_id]
                await ctx.send("Trade cancelled")
            elif request_to_id in self.trades and user in self.trades[request_to_id]:
                del self.trades[request_to_id][user]
                await ctx.send("Trade rejected")
            else:
                await ctx.send("Found no trade offer between the two of you")

    async def filter(self, ctx, user, *args):
        s = ""
        for i in args:
            s += i + " "
        s = s[:-1]
        houses = [ "gryffindor", "ravenclaw", "hufflepuff", "slytherin" ]
        eras = ["marauders", "founders", "classic", "next generation", "timeless"]
        relevant = []
        if s.lower() in ["common", "uncommon", "rare", "legendary"]:
            for i in self.cardlist:
                if i.rarity.lower() == s.lower():
                    relevant += [i]
            messages = (await self.messagify_ownership(user, relevant, "{} Rarity".format(s.capitalize())))
            
        elif s.lower() in houses:
            for i in self.cardlist:
                if s.lower() in i.house.lower():
                    relevant += [i]
            messages = (await self.messagify_ownership(user, relevant, "{} Member".format(s)))
        elif s.lower() in ["character", "trope", "item"]:
            for i in self.cardlist:
                if i.type.lower() == s.lower():
                    relevant += [i]
            messages = (await self.messagify_ownership(user, relevant, "{}".format(s)))
        elif s.lower() in eras:
            for i in self.cardlist:
                if i.era.lower() == s.lower():
                    relevant += [i]
            messages = (await self.messagify_ownership(user, relevant, "{} Era".format(s)))
        else:
            for i in self.cardlist:
                if s.lower() in i.role.lower():
                    relevant += [i]
            if len(relevant) > 0:
                messages = (await self.messagify_ownership(user, relevant, "{} Role".format(s)))
            else:
                for i in self.cardlist:
                    if s.lower() in i.name.lower():
                        relevant += [i]
                if len(relevant) > 0:
                    messages = (await self.messagify_ownership(user, relevant, "{}".format(s)))
                else:
                    for i in self.cardlist:
                        if s.lower() in i.house.lower() or s.lower() in i.type.lower() or s.lower() in i.era.lower():
                            relevant += [i]
                    if len(relevant) > 0:
                        messages = (await self.messagify_ownership(user, relevant, "{}".format(s)))
                    else:
                        messages = ["Could not find any cards that matched the **{}** filter".format(s)]
        for i in messages:
            await ctx.send(i)

    async def grant(self, who, amount):
        if not who in self.bonus_claim:
            self.bonus_claim[who] = 0
        self.bonus_claim[who] += amount

    async def craft(self, ctx, who, *args):
        s = ""
        for i in args:
            s += i + " "
        s = s[:-1]
        if s == "help":
            message = "Pass in three cards you own to craft one of a higher rarity. "
            message += "Mixing card raritys spreads your probability of getting an upgraded rarity "
            message += "(ie [Rarity A, Rarity A, Rarity C] = 66% chance of Rarity S, 33% chance of Rarity B).\n"
            message += "`%tc craft [Card 1, Card 2, Card 3]`"
            await ctx.send(message)
            return
        nil,s = s.split("[")
        s,nil = s.split("]")
        c1,c2,c3 = s.split(",")
        c1 = c1.strip()
        c2 = c2.strip()
        c3 = c3.strip()
        my_cards = [c1,c2,c3]
        if not await self.has_cards(who, my_cards):
            await ctx.send("You don't have all those cards available to craft with!")
            return
        upgrade = {"Common": "Uncommon", "Uncommon": "Rare", "Rare": "Legendary"}
        roll = []
        cards_to_remove = []
        for i in range(0,len(my_cards)):
            for j in self.cardlist:
                if my_cards[i] == j.name:
                    if j.rarity == "S":
                        await ctx.send("Can't upgrade from Legendary rarity cards")
                        return
                    roll += [upgrade[j.rarity]]
                    cards_to_remove += [j]
                    break
        
        target = roll[random.randrange(0,3)]
        if target == "Uncommon":
            await ctx.send("Crafting an **{} Rarity** card".format(target))
        else:
            await ctx.send("Crafting a **{} Rarity** card".format(target))
        relevant = []
        for i in self.cardlist:
            if i.rarity == target:
                relevant += [i]
        selection = relevant[random.randrange(0,len(relevant))]
        r_card_index = []
        for i in cards_to_remove:
            self.trading[who].remove(i)
            r_card_index += [self.cardlist.index(i)]
        await sheets.remove_cards(who, r_card_index)
        self.trading[who] += [selection]
        await sheets.gain_card(who, self.cardlist.index(selection))
        await ctx.send("Crafted **{}** card".format(selection.name))

    @commands.command()
    async def tc(self, ctx, action, *args):
        '''Do things for the Parahumans server trading card game.
            %tc claim - Claim your daily free card
            %tc view [Card] - View all the cards you own
            %tc submit - Get the link to submit new cards for review
            %tc masterlist - View the existing rarity masterlist
            %tc trade [offer/view/accept/reject/cancel/help] @username - Make a trade
            %tc craft [Card 1, Card 2, Card 3] - Craft three cards together into a new one
        '''
        # Wellwick, Kim, sequoia
        granters = ["227834498019098624","347524359830634496","472241913467240449"]
        if action == "unpause" and str(ctx.author.id) == "227834498019098624":
            self.pause = False
            return
        if self.pause:
            # For when developing on a secondary bot
            return
        if not self.cached:
            await ctx.send("Caching things on first run")
            await self.set_local_cache()
        if action == "claim":
            #await ctx.send("Claiming paused while Wellwick fixes things")
            await self.random_claim(ctx, str(ctx.author.id))
        elif action == "recache" and str(ctx.author.id) in granters:
            self.cardlist = []
            self.trading = {}
            await self.set_local_cache()
        elif action == "view" or action == "list" or action == "check":
            await self.view(ctx, str(ctx.author.id), *args)
        elif action == "submit":
            await ctx.send("<https://docs.google.com/forms/d/e/1FAIpQLSct5VoUSyxg6SOOwQV6UBFh6ir4Vk2W6RiX-D0D03ZsrP-MYA/viewform>")
        elif action == "masterlist":
            await ctx.send("<https://docs.google.com/spreadsheets/d/1nH_QNDpc9M9Xl5Uxx_vWdi862N35VQKDODTp8n-vEOc/edit?usp=sharing>")
        elif action == "trade":
            if len(args) == 0:
                await ctx.send("Missing trade subcommand (ie offer, accept, reject, view, cancel)")
            else:
                await self.trade(ctx, str(ctx.author.id), args[0], *args[1:])
        elif action == "offer" and len(args) > 0 and args[1] == "trade":
            await self.trade(ctx, str(ctx.author.id), "offer", *args[1:])
        elif action == "filter":
            await self.filter(ctx, str(ctx.author.id), *args)
        elif action == "pause" and str(ctx.author.id) == "227834498019098624":
            self.pause = True
        elif action == "grant" and str(ctx.author.id) in granters:
            who = await self.at_to_id(args[0])
            amount = int(args[1])
            await self.grant(who, amount)
        elif action == "craft":
            await self.craft(ctx, str(ctx.author.id), *args)

    async def recc(self, ctx, command, *args):
        '''recommend and mywork have the same format, so this shares the code
        '''
        s = ""
        for i in args:
            s += i + " "
        recc = s.split("|")
        for i in range(0,len(recc)):
            recc[i] = recc[i].strip()
        if len(recc) > 6:
            await ctx.send("Too many parts to your {}, look at `%help {}`".format(command, command))
            return
        if recc[0] == "":
            await ctx.send("Couldn't see a link! Look at `%help {}`".format(command))
            return
        return recc


    @commands.command()
    async def recommend(self, ctx, *args):
        '''Recommend a fic to everyone, inserts the recommendation in the Recs sheet of the patreon recommendations.
        Format of recommend is %recommend link | title | tags | characters/pairings | length | additional notes
        All but link are optional, but encouraged!
        '''
        recc = await self.recc(ctx, "recommend", *args)
        await sheets.recommend(str(ctx.author.name), recc)
        await self.grant(str(ctx.author.id), 1)
        await ctx.send("Thanks for recommending a fic, you have been granted a bonus card you can `%tc claim`!")

    @commands.command()
    async def mywork(self, ctx, *args):
        '''Submit one of your fics, inserts the link in the Works sheet of the patreon recommendations.
        Format of mywork is %mywork link | title | tags | characters/pairings | length | additional notes
        All but link are optional, but encouraged!
        '''
        recc = await self.recc(ctx, "mywork", *args)
        await sheets.mywork(str(ctx.author.name), recc)
        await self.grant(str(ctx.author.id), 3)
        await ctx.send("Thanks for writing a fic, you have been granted bonus cards you can `%tc claim`!")

