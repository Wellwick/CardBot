#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
path_here = os.path.dirname(os.path.realpath(__file__))
os.chdir(path_here)
# Lets us not care where smiley runs from
import discord, git
from discord.ext import commands
import asyncio, sys
import sheets
import cards, ficwriter
import episodes
import bingo
import randomfic

'''My (CardBot's) Main Script
I'm friendly, and I have commands to support the Fanatical Fics discord
'''

b = commands.Bot(command_prefix=('%'),  case_insensitive=True)

@b.command()
async def hi(ctx, *args):
    '''The hi command. I'll greet the user.
    '''
    await ctx.send('Hi, <@' + str(ctx.author.id) + '>!')

@b.command()
async def members(ctx, *args):
    '''View a breakdown of the amount of people in each role.
    '''
    breakdown = {"Gryffindor": 0,
                 "Hufflepuff": 0,
                 "Ravenclaw": 0,
                 "Slytherin": 0,
                 "Unsorted": -3}
    for user in ctx.channel.members:
        if user.bot:
            continue
        sorted = False
        for role in user.roles:
            if role.name in breakdown:
                breakdown[role.name] += 1
                sorted = True
        if not sorted:
            breakdown["Unsorted"] += 1
    string = "House Members\n"
    for i in breakdown:
        string += f"> {i}: {breakdown[i]}\n"
    await ctx.send(string)

c = cards.Cards()
b.add_cog(c)
b.add_cog(ficwriter.FicWriter(c))
b.add_cog(episodes.Episodes())
b.add_cog(bingo.Bingo())
b.add_cog(randomfic.RandomFic())

with open('secret') as s:
    token = s.read()[:-1]
# Read the Discord bot token from a soup or secret file

print("Card Bot is going live!")
b.run(token)
# Start the bot, finally!
