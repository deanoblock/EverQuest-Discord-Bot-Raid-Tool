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
sheets_faceless_raid, df_faceless_raid = read_gsheet(gc, 'https://docs.google.com/spreadsheets/d/1JzwnOJvzIdVtoPUfrMT5fFBZ3ixTEcZUJiPJbLtGTjo', 'Raidbot_input')

help_command = commands.DefaultHelpCommand(
    no_category = "Commands"
)

print(sheets_faceless_raid)
#only allow a few admin CMDs to a special Role in discord server

intent = discord.Intents.default()
intent.message_content = True
bot = commands.Bot(command_prefix='!', help_command=help_command, intents=intent)
admin_role_id = int(config["AdminRole"])
bot.registered_players = None
bot.dump = {}

#Player class assosiation to for dump json parse
player_classes = {
    "Bard",
    "Beastlord",
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

#checks to see if there is a dump.json ready to be used and loads data, this is called during startraid and joinraid cmds
def load_data():
    with open("dump.json", "r") as file:
        bot.dump = json.load(file)



@bot.event
async def on_ready():
    print("Faceless raid tool BOT for Quarm connected...")

#Admin role starts the raid sign up 
@bot.command()
@commands.has_role(admin_role_id)
async def startraid(ctx):
    data = load_data()
    """Start a new raid (admin only)"""
    today = date.today()
    date4 = today.strftime("%b-%d-%Y")

    if bot.registered_players is not None:
        return await ctx.send("Raid already started!! Use !endraid to clear and start again!")

    df_faceless_raid.iloc[0:25,0:17] = ""   
     
    bot.registered_players = []

    sheets_faceless_raid.set_dataframe(df_faceless_raid,start='A1', copy_index=False, copy_head=True, extend=True, fit=False, escape_formulae=True)
    await ctx.send(f"Raid started for: {date4}")
    await ctx.send("Listening to `!joinraid <character_name>`")
    await ctx.send("Listening to `!notflagged` for non-flagged character(PoP only!) eg. `!notflagged <character_name>`")

# WARNING-- this dump file from live raid tool is not needed for Quarm TAKP server.  Feature moved to !register cmd so users can register a character and it will build the dump.json
#Admin role to upload raw guild dump txt to be parsed and create JSON file (dump.json)
#@bot.command()
#@commands.has_role(admin_role_id)
#async def dump(ctx):
#    """
#    Update the guild dump. (Admin only)
#    """
#    if len(ctx.message.attachments) != 1:
#        return await ctx.send("No dump attached!")
#
#        bot.dump = {}
#
#    url = ctx.message.attachments[0]
#    dump = requests.get(url).text
#
#    # Split into lines
#    dump = dump.split("\n")
#
    # Remove last line if it's an empty line
 #   if dump[-1] == "":
#        del dump[-1]
#
#
#    for line in dump:
#        line = line.split("\t")
#        username = line[0]
#        player_class = line[2]
#
#        # Skip class if it doesn't exists
#        if player_class not in player_classes:
#            continue
#
#        username = username.lower()
#
#        bot.dump[username] = player_class
#
#    with open("dump.json", "w") as f:
#        json.dump(bot.dump, f)
#    return await ctx.send("Guild Dump updated!")



@bot.command()
async def register(ctx):
    data = load_data()
    await ctx.send("Please enter your character name:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    name_response = await bot.wait_for('message', check=check)
    user_name = name_response.content

#emoji are external emoji icons you upload in the discord server, use \:emoji: to pull the ID and place below for each class
    predefined_types = [
        {"class": "Bard", "emoji": "<:Bardicon:1163198035153666158>"},
        {"class": "Beastlord", "emoji": "<:Beastlordicon:1163238928824946768>"},
        {"class": "Cleric", "emoji": "<:Clericicon:1163238931064705045>"},
        {"class": "Druid", "emoji": "<:Druidicon:1163238932092293140>"},
        {"class": "Enchanter", "emoji": "<:Enchantericon:1163238932947931288>"},
        {"class": "Magician", "emoji": "<:Magicianicon:1163238935011541002>"},
        {"class": "Monk", "emoji": "<:Monkicon:1163238935808450710>"},
        {"class": "Necromancer", "emoji": "<:Necromancericon:1163238936982859827>"},
        {"class": "Paladin", "emoji": "<:Paladinicon:1163239843195785328>"},
        {"class": "Ranger", "emoji": "<:Rangericon:1163241643193946212>"},
        {"class": "Rogue", "emoji": "<:Rogueicon:1163238940921303100>"},
        {"class": "Shadow Knight", "emoji": "<:Skicon:1163239440139964427>"},
        {"class": "Warrior", "emoji": "<:Warrioricon:1163238943127523359>"},
        {"class": "Wizard", "emoji": "<:Wizardicon:1163239384041136128>"}
        ]
    type_options = "\n".join(f"{index+1}. {type['emoji']} {type['class']}" for index, type in enumerate(predefined_types))
    await ctx.send(f"Please select a `class` (enter the corresponding number):\n{type_options}")

    type_response = await bot.wait_for('message', check=check)
    user_type_index = int(type_response.content) - 1
    user_type = predefined_types[user_type_index]




# Check if JSON file exists, create it if not
    if not os.path.exists('dump.json'):
        with open('dump.json', 'w') as file:
            json.dump({}, file)

    # Update JSON
    with open('dump.json', 'r') as file:
        data = json.load(file)
        data[user_name] = user_type["class"]

    with open('dump.json', 'w') as file:
        json.dump(data, file)

    await ctx.send(f'`{user_name}` has been registered with class {user_type["class"]} {user_type["emoji"]} you are ready to raid!')

@bot.command()
async def status(ctx):
    await ctx.send("Please enter your registered raid character name to check status:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    name_response = await bot.wait_for('message', check=check)
    user_name = name_response.content

    with open('dump.json', 'r') as file:
        data = json.load(file)
        if user_name in data:
            user_type = data[user_name]
            await ctx.send(f'Character Name: `{user_name}`, Type: `{user_type}` is registered to raid')
        else:
            await ctx.send(f'Character Name `{user_name}` not found in guild raid list. Pleas register with !register cmd and type your character name correctly!')


@bot.command()
@commands.has_role(admin_role_id)
async def readreg(ctx):
    try:
        with open("dump.json", "r") as f:
            data = json.load(f)
            formatted_data = json.dumps(data, indent=4)  # Format the data for better readability
            await ctx.send(f"All faceless registered raid characters list:\n```json\n{formatted_data}\n```")
    except FileNotFoundError:
        await ctx.send("The 'dump.json' file does not exist. Please fix bot!!")


@bot.command()
@commands.has_role(admin_role_id)
async def delete(ctx, user_name):
    try:
        with open("dump.json", "r") as f:
            data = json.load(f)

        if user_name in data:
            del data[user_name]

            with open("dump.json", "w") as f:
                json.dump(data, f, indent=4)

            await ctx.send(f"User '{user_name}' and their type have been removed from registered raid characters list")
        else:
            await ctx.send(f"User '{user_name}' not found in the registered raid characters list")
    except FileNotFoundError:
        await ctx.send("The 'dump.json' file does not exist. Please fix bot!!")



#User cmd to sign up for the raid and contains Gsheet API to send the data to the sheet
@bot.command()
async def joinraid(ctx, *, username=None):
    data = load_data()
    """
    Sign up your character to the raid.
    """
    if bot.registered_players is None:
        return await ctx.send("Raid not started yet please wait for raid leader instructions first!")
    if username is None:
        return await ctx.send("Incorrect command usage. `!joinraid <name of your character in game>` eg. `!joinraid zaide`")
    
    username = username.translate({ord(c): None for c in string.whitespace})
    username = username.lower()
    bot.dump = {i.lower():bot.dump[i] for i in bot.dump}
    
    ids = username.split(";")
    ids.insert(1,ids[0])
    
    if len(ids) > 1:

        for i in range(1,len(ids)):
            tmp_username = ids[i]

            if tmp_username not in bot.dump:
                return await ctx.send(f"``{tmp_username}`` not found in guild list, are you a new member? Please register your character with `!register <character_name>`")

            if tmp_username in [p.username for p in bot.registered_players]:
                return await ctx.send(f"``{tmp_username}`` is already signed up to the raid!")

            current_members = list(df_faceless_raid[bot.dump[tmp_username]])            
            
            break_index = next((index for index,val in enumerate(current_members) if val == ""),0)

            if tmp_username in list(map(lambda x: x.split()[0] if x else None,current_members[:break_index])):
                await ctx.send(f"``{tmp_username}`` has already been added!")
                continue

            df_faceless_raid[bot.dump[tmp_username]] = (
                current_members[:break_index]
                + [f"""{tmp_username}""" + (f""" ({username.split(";")[0]} box)""","")[i<=1] ]
                + current_members[break_index + 1 :]
            )

            sheets_faceless_raid.set_dataframe(df_faceless_raid,start='A1', copy_index=False, copy_head=True, extend=True, fit=False, escape_formulae=True)
            await ctx.send(f"``{tmp_username}`` added!")

#User cmd to tag character(s) as not flagged for the raid
@bot.command()
async def notflagged(ctx, *, username=None):
    if bot.registered_players is None:
        return await ctx.send("Raid not started yet please wait for raid leader instructions first!")
    if username is None:
        return await ctx.send("Incorrect command usage. `!notflagged <character_name>`")

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

            current_members = list(df_faceless_raid.iloc[:,16])
            
            
            break_index = next((index for index,val in enumerate(current_members) if val == ""),0)

            if tmp_username in list(map(lambda x: x.split()[0] if x else None,current_members[:break_index])):
                await ctx.send(f"``{tmp_username}`` has already been added!")
                continue

            df_faceless_raid.iloc[:,16] = (
                current_members[:break_index]
                + [f"""{tmp_username}"""]
                + current_members[break_index + 1 :]
            )

            sheets_faceless_raid.set_dataframe(df_faceless_raid,start='A1', copy_index=False, copy_head=True, extend=True, fit=False, escape_formulae=True)
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
        embed=Embed(title=("Current Raid:", date4), url='https://docs.google.com/spreadsheets/d/1JzwnOJvzIdVtoPUfrMT5fFBZ3ixTEcZUJiPJbLtGTjo/htmlembed?single=true&gid=0&range=A39:P102&widget=true&chrome=false', description="Raid posted, **form your groups!!**", color=0xFF5733)
    
    await ctx.send(embed=embed)

#Admin cmd to stop users from Signing up and clears the google sheet
@bot.command()
@commands.has_role(admin_role_id)
async def endraid(ctx):
    """
    Ends the current raid sign up's and clears the Faceless Raid Tool Quarm Google Sheet
    """
    if bot.registered_players is None:
        return await ctx.send("Raid not started!")
    else:
        df_faceless_raid.iloc[0:36,0:17] = "" 
        sheets_faceless_raid.set_dataframe(df_faceless_raid,start='A1', copy_index=False, copy_head=True, extend=True, fit=False, escape_formulae=True)    

    bot.registered_players = None
    await ctx.send("Raid ended and Faceless Raid Tool Quarm Sheet cleared!")

if __name__ == "__main__":
    bot.run(config["BotToken"])