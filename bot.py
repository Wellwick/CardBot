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

'''My (CardBot's) Main Script
I'm friendly, and I have commands to support playing PD and WD!
'''

b = commands.Bot(command_prefix=('%'),  case_insensitive=True)

@b.command()
async def hi(ctx, *args):
    '''The hi command. I'll greet the user.
    '''
    await ctx.send('Hi, <@' + str(ctx.author.id) + '>!')

c = cards.Cards()
b.add_cog(c)
b.add_cog(ficwriter.FicWriter(c))

with open('secret') as s:
    token = s.read()[:-1]
# Read the Discord bot token from a soup or secret file

b.run(token)
# Start the bot, finally!
