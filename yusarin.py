import os
import sys
import json
import shutil
import requests
import threading

try:
    import discord # type: ignore
    from discord import ApplicationContext, Option, Intents  # type: ignore
except Exception as exp:
    print(f"Module py-cord is not installed. Make sure to run 'pip install -r requirements.txt' before first start")
    sys.exit()

from functions import *
pid = os.getpid()
version = 1.5

if loadJson("config.json")["owner"] == "SET-OWNER-ID" or loadJson("config.json")["bot_token"] == "SET-BOT-TOKEN":
    print(f"Bot is not correctly configured.\nMake sure you've set up owner id and bot token in {path}/config.json\nLearn more here: https://github.com/profitrollgame/YusarinBot")
    sys.exit()

if loadJson("config.json")["check_for_updates"]:
    try:
        serv_ver = json.loads(requests.get("https://api.end-play.xyz/version&apikey=publickey&app=yusarinbot").text)["version"]
        if float(serv_ver) > version:
            appendLog(f"YusarinBot version {serv_ver} is available. Download new version here: https://github.com/profitrollgame/YusarinBot/releases/latest")
            appendLog(f"Currently using YusarinBot v{str(version)}")
    except Exception as exp:
        appendLog(f"Could not get YusarinBot cloud version due to {exp}. Currently using {str(version)}")

intents = Intents().all()
client = discord.Bot(intents=intents)

@client.event
async def on_ready():

    appendLog(f"Logged in as {client.user}")
    
    config = loadJson("config.json")
    
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=config["bot_activity"]))
    
    await clearTrash(client)

@client.event
async def on_guild_join(guild):
    
    global path
    
    os.mkdir(f"{path}/guilds/{str(guild.id)}")
    os.mkdir(f"{path}/guilds/{str(guild.id)}/channels")
    saveJson({}, f"{path}/guilds/{str(guild.id)}/config.json")
    
    appendLog(f"Joined guild '{guild}' with id {str(guild.id)}")

@client.event
async def on_guild_remove(guild):
    
    global path

    try:
        shutil.rmtree(f"{path}/guilds/{str(guild.id)}")
    except:
        pass
    
    appendLog(f"Left guild '{guild}' with id {str(guild.id)}")

@client.event
async def on_voice_state_update(member, before, after):

    global debug

    config = loadJson("config.json")

    vc_from = before.channel
    vc_to = after.channel
    
    # If user left vc
    if vc_to is None:
        if isUserVoice(vc_from):
            if isVoiceOfUser(vc_from, member):
                await removeUserVoice(vc_from)
                return
            else:
                await changeNomicPerms("deny", vc_from, member)
        
    # If user joined vc
    else:
        if isUserVoice(vc_from):
            if isVoiceOfUser(vc_from, member):
                await removeUserVoice(vc_from)
            else:
                await changeNomicPerms("deny", vc_from, member)
        if isUserVoice(vc_to):
            await changeNomicPerms("allow", vc_to, member)
        if vc_to.id == guildConfGet(vc_to.guild, "channel"):
            if guildConfGet(vc_to.guild, "category") is not None:
                voice_chan = await createUserVoice(vc_to, discord.utils.get(vc_to.guild.categories, id=guildConfGet(vc_to.guild, "category")), member)
                try:
                    await member.move_to(voice_chan)
                except:
                    await removeUserVoice(voice_chan)
            else:
                if debug:
                    appendLog(f"Category for guild {vc_to.guild} ({str(vc_to.guild.id)}) is not set", guild=vc_to.guild)
                else:
                    appendLog(f"Category for guild {vc_to.guild} is not set", guild=vc_to.guild)

#=========================================================================================================================
@client.slash_command(name="shutdown", description="Restart the bot")
async def shutdown(ctx: ApplicationContext):
    config = loadJson("config.json")
    if ctx.author.id == config["owner"]:  
        await ctx.respond(embed=makeEmbed(description=getMsg("shutdown", ctx.guild).format(ctx.author), color=strToColor(config["color_default"])))
        os.system(f"kill -9 {str(pid)}")
    else:
        await ctx.respond(embed=makeEmbed(title=getMsg("admin_title", ctx.guild), description=getMsg("admin_description", ctx.guild), color=strToColor(config["color_error"])))
#=========================================================================================================================

#=========================================================================================================================
@client.slash_command(name="help", description="Get information about this server")
async def help(ctx: ApplicationContext):
    await ctx.respond(embed=getHelpMessage(ctx, version))
#=========================================================================================================================

#=========================================================================================================================
locale = client.create_group("locale", "Commands related to bot's locale")

valid_locales = []
files_locales = os.listdir(f"{path}/locale/")
for entry in files_locales:
    valid_locales.append(".".join(entry.split(".")[:-1]))

@locale.command(name="set", description="Set bot's messages language")
async def locale_set(ctx: ApplicationContext, language: Option(str, "One of the languages in list", choices=valid_locales)): # type: ignore
    config = loadJson("config.json")
    if ctx.guild is not None:
        if language+".json" in os.listdir(f"{path}/locale/"):
            guildConfSet(ctx.guild, "locale", language)
            appendLog(f"Server's locale is now set to {language}", ctx.guild)
            await ctx.respond(embed=makeEmbed(title=getMsg("set_locale_title", ctx.guild), description=getMsg("set_locale_description", ctx.guild).format(getMsg("locale_name", ctx.guild)), color=strToColor(config["color_ok"])))
        else:
            valid_locales = []
            files_locales = os.listdir(f"{path}/locale/")
            for entry in files_locales:
                valid_locales.append(entry.split(".")[:-1])
            await ctx.respond(embed=makeEmbed(title=getMsg("error_locale_title", ctx.guild), description=getMsg("error_locale_description", ctx.guild).format(", ".join(valid_locales)), color=strToColor(config["color_error"])))
    else:
        await ctx.respond(embed=makeEmbed(title=getMsg("dm_title", ctx.guild), description=getMsg("dm_description", ctx.guild), color=strToColor(config["color_error"])))

@locale.command(name="reset", description="Reset the bot's language in this guild")
async def locale_reset(ctx: ApplicationContext): # type: ignore
    config = loadJson("config.json")
    if ctx.guild is not None:
        if guildConfGet(ctx.guild, "locale") is not None:
            guildConfReset(ctx.guild, "locale")
            appendLog(f"Server's locale has been reset", ctx.guild)
            await ctx.respond(embed=makeEmbed(title=getMsg("reset_locale_title", ctx.guild), description=getMsg("reset_locale_description", ctx.guild).format(getMsg("locale_name", ctx.guild)), color=strToColor(config["color_ok"])))
        else:
            await ctx.respond(embed=makeEmbed(title=getMsg("hint_none_locale_title", ctx.guild), description=getMsg("hint_none_locale_description", ctx.guild).format(getMsg("locale_name", ctx.guild)), color=strToColor(config["color_warn"])))
    else:
        await ctx.respond(embed=makeEmbed(title=getMsg("dm_title", ctx.guild), description=getMsg("dm_description", ctx.guild), color=strToColor(config["color_error"])))
#=========================================================================================================================

#=========================================================================================================================
channel = client.create_group("channel", "Commands related to parent voice channel")

@channel.command(name="set", description="Select the voice channel that will be parent to private ones")
async def channel_set(ctx: ApplicationContext, channel: Option(discord.VoiceChannel, "Parent Voice Channel")): # type: ignore
    config = loadJson("config.json")
    if ctx.guild is not None:
        guildConfSet(ctx.guild, "channel", channel.id)
        await ctx.respond(embed=makeEmbed(title=getMsg("set_channel_title", ctx.guild), description=getMsg("set_channel_description", ctx.guild).format(channel.name), color=strToColor(config["color_ok"])))
        if guildConfGet(ctx.guild, "category") is None:
            await ctx.respond(embed=makeEmbed(title=getMsg("hint_none_category_title", ctx.guild), description=getMsg("hint_none_category_description", ctx.guild), color=strToColor(config["color_warn"])))
    else:
        await ctx.respond(embed=makeEmbed(title=getMsg("dm_title", ctx.guild), description=getMsg("dm_description", ctx.guild), color=strToColor(config["color_error"])))

@channel.command(name="reset", description="Reset the currently selected parent voice channel")
async def channel_reset(ctx: ApplicationContext): # type: ignore
    config = loadJson("config.json")
    if ctx.guild is not None:
        if guildConfGet(ctx.guild, "channel") is not None:
            guildConfReset(ctx.guild, "channel")
            await ctx.respond(embed=makeEmbed(title=getMsg("reset_channel_title", ctx.guild), description=getMsg("reset_channel_description", ctx.guild), color=strToColor(config["color_ok"])))
        else:
            await ctx.respond(embed=makeEmbed(title=getMsg("hint_none_channel_title", ctx.guild), description=getMsg("hint_none_channel_description", ctx.guild), color=strToColor(config["color_warn"])))
    else:
        await ctx.respond(embed=makeEmbed(title=getMsg("dm_title", ctx.guild), description=getMsg("dm_description", ctx.guild), color=strToColor(config["color_error"])))
#=========================================================================================================================

#=========================================================================================================================
category = client.create_group("category", "Commands related to parent channels category")

@category.command(name="set", description="Select the voice channel that will be parent to private ones")
async def category_set(ctx: ApplicationContext, category: Option(discord.CategoryChannel, "Parent Channel Category")): # type: ignore
    config = loadJson("config.json")
    if ctx.guild is not None:
        guildConfSet(ctx.guild, "category", category.id)
        await ctx.respond(embed=makeEmbed(title=getMsg("set_category_title", ctx.guild), description=getMsg("set_category_description", ctx.guild).format(category.name), color=strToColor(config["color_ok"])))
        if guildConfGet(ctx.guild, "channel") is None:
            await ctx.respond(embed=makeEmbed(title=getMsg("hint_none_channel_title", ctx.guild), description=getMsg("hint_none_channel_description", ctx.guild), color=strToColor(config["color_warn"])))
    else:
        await ctx.respond(embed=makeEmbed(title=getMsg("dm_title", ctx.guild), description=getMsg("dm_description", ctx.guild), color=strToColor(config["color_error"])))

@category.command(name="reset", description="Reset the currently selected parent channel category")
async def category_reset(ctx: ApplicationContext): # type: ignore
    config = loadJson("config.json")
    if ctx.guild is not None:
        if guildConfGet(ctx.guild, "category") is not None:
            guildConfReset(ctx.guild, "category")
            await ctx.respond(embed=makeEmbed(title=getMsg("reset_category_title", ctx.guild), description=getMsg("reset_category_description", ctx.guild), color=strToColor(config["color_ok"])))
        else:
            await ctx.respond(embed=makeEmbed(title=getMsg("hint_none_category_title", ctx.guild), description=getMsg("hint_none_category_description", ctx.guild), color=strToColor(config["color_warn"])))
    else:
        await ctx.respond(embed=makeEmbed(title=getMsg("dm_title", ctx.guild), description=getMsg("dm_description", ctx.guild), color=strToColor(config["color_error"])))
#=========================================================================================================================

appendLog(f"Trying to log in...")
client.run(loadJson("config.json")["bot_token"])