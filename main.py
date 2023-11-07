from discord.ext import commands
from discord import Embed
from datetime import date
import discord
import json
import requests
import os
import pandas as pd
import os.path
from pprint import pprint
from gsheet_conn import gsheet_connection,read_gsheet
import configparser
import string

config = configparser.ConfigParser()
config.read("config.ini")
config = config["CONFIG"]

#Gsheet APi connector
gc = gsheet_connection()
sheets__raid, df__raid = read_gsheet(gc, 'https://docs.google.com/spreadsheets/[enter gsheet url here]', 'Raidbot_input')

help_command = commands.DefaultHelpCommand(
    no_category = "Commands"
)

intents = discord.Intents.default()
intents.message_content = True
print(sheets__raid)
#only allow a few admin CMDs to a special Role in discord server
bot = commands.Bot(command_prefix='!', help_command=help_command, intents=intents)
admin_role_id = int(config["AdminRole"])


bot.registered_players = None
bot.dump = {}

#Player class assosiation to for dump json parse
player_classes = {
    "Bard",
    "Beastlord",
    "Berserker",
    "Cleric",
    "Druid",
    "Enchanter",
    "Magician",
    "Monk",
    "Necromancer",
    "Paladin",
    "Ranger",
    "Rogue",
    "Shadow Knight",
    "Shaman",
    "Warrior",
    "Wizard"
}

#checks to see if thre is a dump.json ready to be used
try:
    with open("dump.json", "r") as f:
        bot.dump = json.load(f)
except FileNotFoundError:
    with open("dump.json", "w") as f:
        json.dump(bot.dump, f)

@bot.event
async def on_ready():
    print("raid tool BOT connected...")

#Admin role starts the raid sign up 
@bot.command()
@commands.has_role(admin_role_id)
async def startraid(ctx):
    """Start a new raid (admin only)"""
    today = date.today()
    date4 = today.strftime("%b-%d-%Y")

    if bot.registered_players is not None:
        return await ctx.send("Raid already started!! Use !endraid to clear and start again!")

    df__raid.iloc[0:25,0:17] = ""   
     
    bot.registered_players = []

    sheets__raid.set_dataframe(df__raid,start='A1', copy_index=False, copy_head=True, extend=True, fit=False, escape_formulae=True)
    await ctx.send(f"Raid started for: {date4}")
    await ctx.send("Listening to `!joinraid <main>;<box1>;<box2>;<box3>;<box4>;<box5>`")
    await ctx.send("Listening to `!notflagged` for non-flagged character(s) eg. `!notflagged <box1>;<box2>;<box3>;etc`")

#Admin role to upload raw guild dump txt to be parsed and create JSON file (dump.json)
@bot.command()
@commands.has_role(admin_role_id)
async def dump(ctx):
    """
    Update the guild dump. (Admin only)
    """
    if len(ctx.message.attachments) != 1:
        return await ctx.send("No dump attached!")

        bot.dump = {}

    url = ctx.message.attachments[0]
    dump = requests.get(url).text

    # Split into lines
    dump = dump.split("\n")

    # Remove last line if it's an empty line
    if dump[-1] == "":
        del dump[-1]


    for line in dump:
        line = line.split("\t")
        username = line[0]
        player_class = line[2]

        # Skip class if it doesn't exists
        if player_class not in player_classes:
            continue

        username = username.lower()

        bot.dump[username] = player_class

    with open("dump.json", "w") as f:
        json.dump(bot.dump, f)
    return await ctx.send("Guild Dump updated!")

#User cmd to sign up for the raid and contains Gsheet API to send the data to the sheet
@bot.command()
async def joinraid(ctx, *, username=None):
    """
    Sign up your character(s) to the raid.
    """
    if bot.registered_players is None:
        return await ctx.send("Raid not started yet please wait for raid leader instructions first!")
    if username is None:
        return await ctx.send("Incorrect command usage. `!joinraid <main>;<box1>;<box2>;<box3>;<box4>;<box5>` no spaces semicolon delimited!!")

    username = username.translate({ord(c): None for c in string.whitespace})
    username = username.lower()

    bot.dump = {i.lower():bot.dump[i] for i in bot.dump}
    
    ids = username.split(";")
    ids.insert(1,ids[0])
    
    if len(ids) > 1:

        for i in range(1,len(ids)):
            tmp_username = ids[i]

            if tmp_username not in bot.dump:
                return await ctx.send(f"``{tmp_username}`` not found in guild dump, are you a new member? Please speak to an officer and let them know!")

            if tmp_username in [p.username for p in bot.registered_players]:
                return await ctx.send(f"``{tmp_username}`` is already signed up to the raid!")

            current_members = list(df__raid[bot.dump[tmp_username]])            
            
            break_index = next((index for index,val in enumerate(current_members) if val == ""),0)

            if tmp_username in list(map(lambda x: x.split()[0] if x else None,current_members[:break_index])):
                await ctx.send(f"``{tmp_username}`` has already been added!")
                continue

            df__raid[bot.dump[tmp_username]] = (
                current_members[:break_index]
                + [f"""{tmp_username}""" + (f""" ({username.split(";")[0]} box)""","")[i<=1] ]
                + current_members[break_index + 1 :]
            )

            sheets__raid.set_dataframe(df__raid,start='A1', copy_index=False, copy_head=True, extend=True, fit=False, escape_formulae=True)
            await ctx.send(f"``{tmp_username}`` added!")

#User cmd to tag character(s) as not flagged for the raid
@bot.command()
async def notflagged(ctx, *, username=None):
    if bot.registered_players is None:
        return await ctx.send("Raid not started yet please wait for raid leader instructions first!")
    if username is None:
        return await ctx.send("Incorrect command usage. `!notflagged <main>;<box1>;<box2>;<box3>;etc` no spaces semicolon delimited!!")

    username = username.translate({ord(c): None for c in string.whitespace})
    username = username.lower()
    bot.dump = {i.lower():bot.dump[i] for i in bot.dump}

    ids = username.split(";")
    ids.insert(1,ids[0])
    
    if len(ids) > 1:

        for i in range(1,len(ids)):
            tmp_username = ids[i]

            if tmp_username not in bot.dump:
                return await ctx.send(f"``{tmp_username}`` not found, please check for typos or speak to an officer.")
            if tmp_username in [p.username for p in bot.registered_players]:
                return await ctx.send(f"``{tmp_username}`` is already tagged as not flagged for the raid!!")

            current_members = list(df__raid.iloc[:,16])
            
            
            break_index = next((index for index,val in enumerate(current_members) if val == ""),0)

            if tmp_username in list(map(lambda x: x.split()[0] if x else None,current_members[:break_index])):
                await ctx.send(f"``{tmp_username}`` has already been added!")
                continue

            df__raid.iloc[:,16] = (
                current_members[:break_index]
                + [f"""{tmp_username}"""]
                + current_members[break_index + 1 :]
            )

            sheets__raid.set_dataframe(df__raid,start='A1', copy_index=False, copy_head=True, extend=True, fit=False, escape_formulae=True)
            await ctx.send(f"``{tmp_username}`` tagged as not flagged!")

#Admin cmd to stop users from Signing up and posts the raid splits to Discord
@bot.command()
@commands.has_role(admin_role_id)
async def postraid(ctx):
    """
    Posts the raid splits from the raid tool sheet (Admin only)
    """
    today = date.today()
    date4 = today.strftime("%b-%d-%Y")

    if bot.registered_players is None:
        return await ctx.send("Raid not started!")
    else:
        embed=Embed(title=("Current Raid:", date4), url='https://docs.google.com/spreadsheets/[enter gsheet url here]/htmlembed?single=true&gid=0&range=A39:P102&widget=true&chrome=false', description="Raid posted, **form your groups!!**", color=0xFF5733)
    
    await ctx.send(embed=embed)

#Admin cmd to stop users from Signing up and clears the google sheet
@bot.command()
@commands.has_role(admin_role_id)
async def endraid(ctx):
    """
    Ends the current raid sign up's and clears the Raid Tool Google Sheet
    """
    if bot.registered_players is None:
        return await ctx.send("Raid not started!")
    else:
        df__raid.iloc[0:36,0:17] = "" 
        sheets__raid.set_dataframe(df__raid,start='A1', copy_index=False, copy_head=True, extend=True, fit=False, escape_formulae=True)    

    bot.registered_players = None
    await ctx.send("Raid ended and Raid Tool Sheet cleared!")

if __name__ == "__main__":
    bot.run(config["BotToken"])