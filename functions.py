import gzip
import os
import sys
import json
import shutil
import discord # type: ignore

from datetime import datetime
from pathlib import Path

path = Path(__file__).resolve().parent

log_size = 512

# This is the default option for "debug" key in
# file config.json, so if cebug is not set in it
# bot will use this value instead.
debug = False

try:
    with open("config.json", 'r', encoding="utf-8") as json_file:
        output = json.load(json_file)
        json_file.close()
    debug = output["debug"]
except:
    debug = debug

# Check latest log size
def checkSize():
    global path
    path = str(path)

    try:
        if not os.path.isdir(f"{path}/logs"):
            os.mkdir(f"{path}/logs")
        
        log = os.stat(path + '/logs/latest.log')
        global log_size

        if (log.st_size / 1024) > log_size:
            with open(path + '/logs/latest.log', 'rb') as f_in:
                with gzip.open(f'{path}/logs/{datetime.now().strftime("%d.%m.%Y_%H:%M:%S")}.log.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    print(f'Copied {path}/logs/{datetime.now().strftime("%d.%m.%Y_%H:%M:%S")}.log.gz')
            open(path + '/logs/latest.log', 'w').close()
    except FileNotFoundError:
        print('Not found')
        pass

# Append string to log
def appendLog(message, guild=None, announce=True):
    global debug
    global path
    
    if guild == None:
        message_formatted = f'[{datetime.now().strftime("%d.%m.%Y")}] [{datetime.now().strftime("%H:%M:%S")}] {message}'
    else:
        if debug:
            message_formatted = f'[{datetime.now().strftime("%d.%m.%Y")}] [{datetime.now().strftime("%H:%M:%S")}] [{guild} | {str(guild.id)}] {message}'
        else:
            message_formatted = f'[{datetime.now().strftime("%d.%m.%Y")}] [{datetime.now().strftime("%H:%M:%S")}] [{guild}] {message}'
    
    if announce:
        print(message_formatted)

    checkSize()

    log = open(path + '/logs/latest.log', 'a')  # type: ignore
    log.write(f'{message_formatted}\n')
    log.close()

def saveJson(value, filename):
    with open(filename, 'w', encoding="utf-8") as f:
        json.dump(value, f, indent=4, ensure_ascii=False)
        f.close()

def loadJson(filename):
    global debug
    try:
        with open(filename, 'r', encoding="utf-8") as json_file:
            output = json.load(json_file)
            json_file.close()
    except Exception as exp:
        if debug:
            appendLog(f"Could not load json file {filename} due to exception {exp}")
        output = {}
    return output

def colorToStr():
    pass

def strToColor(string):
    return int(hex(int(string.replace("#", ""), 16)), 0)

def gotCommand(message):
    global debug
    if debug:
        appendLog(f"Command '{message.content}' from {message.author} ({str(message.author.id)})", message.guild)
    else:
        appendLog(f"Command '{message.content}' from {message.author}", message.guild)

def guildConfGet(guild, variable):
    global path
    global debug
    try:
        config = loadJson(f"{path}/guilds/{str(guild.id)}/config.json")
        return config[variable]
    except Exception as exp:
        if debug:
            appendLog(f"Could not get guild config key '{variable}' due to {exp}", guild)
        return None

def guildConfSet(guild, variable, value):
    global path
    config = loadJson(f"{path}/guilds/{str(guild.id)}/config.json")
    config[variable] = value
    try:
        saveJson(config, f"{path}/guilds/{str(guild.id)}/config.json")
    except:
        os.mkdir(f"{path}/guilds/{str(guild.id)}")
        os.mkdir(f"{path}/guilds/{str(guild.id)}/channels")
        saveJson(config, f"{path}/guilds/{str(guild.id)}/config.json")
    appendLog(f"Guild config key '{variable}' is now set to '{value}'", guild)

def guildConfReset(guild, variable):
    global path
    try:
        config = loadJson(f"{path}/guilds/{str(guild.id)}/config.json")
        del config[variable]
        try:
            saveJson(config, f"{path}/guilds/{str(guild.id)}/config.json")
        except:
            os.mkdir(f"{path}/guilds/{str(guild.id)}")
            os.mkdir(f"{path}/guilds/{str(guild.id)}/channels")
            saveJson(config, f"{path}/guilds/{str(guild.id)}/config.json")
        appendLog(f"Guild config key '{variable}' has been reset", guild)
    except Exception as exp:
        appendLog(f"Could not reset guild config key '{variable}' due to {exp}", guild)

def guildLocaleGet(guild):
    global path
    config = loadJson(f"{path}/config.json")
    try:
        locale = guildConfGet(guild, "locale")
    except:
        return config["bot_locale"]
    if locale is None:
        return config["bot_locale"]
    else:
        return locale

def getMsg(string, guild=None):
    global path
    config = loadJson("config.json")
    try:
        locale = loadJson(f'{path}/locale/{guildLocaleGet(guild)}.json')
        return locale["messages"][string]
    except Exception as exp:
        appendLog(f"Could not get locale string named {string} due to exception {exp}", guild)
        return string

def makeEmbed(title="", description="", footer="", color=0xffffff):
    embed=discord.Embed(title=title, description=description, color=color)
    if footer is not None:
        embed.set_footer(text=footer)
    return embed

def channelExists(number, guild, type="Any"):
    global debug
    if number == None:
        return False
    try:
        if type == "Voice":
            selected_channel = discord.utils.get(guild.channels, id=number)
            if isinstance(selected_channel, discord.VoiceChannel):
                return True
        elif type == "Text":
            selected_channel = discord.utils.get(guild.channels, id=number)
            if isinstance(selected_channel, discord.TextChannel):
                return True
        elif type == "Any":
            selected_channel = discord.utils.get(guild.channels, id=number)
            return True
    except Exception as exp:
        if debug:
            appendLog(f"Channel ID {str(number)} is not a channel due to {exp}")
    return False

def channelGetName(number, guild):
    global debug
    try:
        selected_channel = discord.utils.get(guild.channels, id=number)
        return selected_channel.name
    except Exception as exp:
        if debug:
            appendLog(f"Channel ID {str(number)} is not a channel due to {exp}")
    return "Channel doesn't exist"

def isUserVoice(vc):
    global path
    try:
        channels_list = os.listdir(f"{path}/guilds/{str(vc.guild.id)}/channels/")
        if f"{str(vc.id)}.json" in channels_list:
            return True
        else:
            return False
    except:
        return False
    
async def removeUserVoice(vc):
    global path
    global debug
    channels_list = os.listdir(f"{path}/guilds/{str(vc.guild.id)}/channels/")
    if f"{vc.id}.json" in channels_list:
        vc_file = f"{path}/guilds/{str(vc.guild.id)}/channels/{str(vc.id)}.json"
        vc_conf = loadJson(vc_file)
        
        needed_channel = discord.utils.get(vc.guild.channels, id=vc.id)
        nomic_channel = discord.utils.get(vc.guild.channels, id=vc_conf["nomic"])
        
        os.remove(vc_file)
        
        await needed_channel.delete()
        if debug:
            appendLog(f"Removed voice channel '{needed_channel}' ({str(needed_channel.id)}) of user with id {str(vc_conf['ownerid'])}", guild=vc.guild)
        else:
            appendLog(f"Removed voice channel '{needed_channel}' of user with id {str(vc_conf['ownerid'])}", guild=vc.guild)
        await nomic_channel.delete()
        if debug:
            appendLog(f"Removed nomic channel {nomic_channel} ({str(nomic_channel.id)}) of channel with id {str(needed_channel.id)}", guild=vc.guild)
        else:
            appendLog(f"Removed nomic channel '{nomic_channel}' of channel with id {str(needed_channel.id)}", guild=vc.guild)
    else:
        return

async def createUserVoice(vc, category, member):
    global path
    global debug
    chan = {}
    overwrites_channel = {
        vc.guild.default_role: discord.PermissionOverwrite(view_channel=True),
        vc.guild.me: discord.PermissionOverwrite(read_messages=True, view_channel=True, manage_channels=True),
        member: discord.PermissionOverwrite(read_messages=True, view_channel=True, manage_channels=True)
    }
    overwrites_nomic = {
        vc.guild.default_role: discord.PermissionOverwrite(view_channel=False, read_messages=False),
        vc.guild.me: discord.PermissionOverwrite(read_messages=True, view_channel=True, manage_channels=True),
        member: discord.PermissionOverwrite(read_messages=True, view_channel=True, manage_channels=True)
    }
    created_channel = await vc.guild.create_voice_channel(getMsg("name_voice", vc.guild).format(member.name), category=category, overwrites=overwrites_channel)
    if debug:
        appendLog(f"Created voice channel '{created_channel}' ({str(created_channel.id)}) for user {member} ({str(member.id)})", guild=vc.guild)
    else:
        appendLog(f"Created voice channel '{created_channel}' for user {member}", guild=vc.guild)
    if not os.path.isdir(f"{path}/guilds/{str(created_channel.guild.id)}/channels"):
        os.mkdir(f"{path}/guilds/{str(created_channel.guild.id)}/channels")
    vc_file = f"{path}/guilds/{str(created_channel.guild.id)}/channels/{str(created_channel.id)}.json"
    chan["ownerid"] = member.id
    saveJson(chan, vc_file)
    nomic_channel = await vc.guild.create_text_channel(getMsg("name_nomic", vc.guild).format(created_channel.id), category=category, overwrites=overwrites_nomic, topic=getMsg("description_nomic", vc.guild).format(str(created_channel.id)))
    if debug:
        appendLog(f"Created nomic channel '{nomic_channel}' ({str(nomic_channel.id)}) for channel '{created_channel}' ({str(created_channel.id)})", guild=vc.guild)
    else:
        appendLog(f"Created nomic channel '{nomic_channel}' for channel '{created_channel}'", guild=vc.guild)
    chan["nomic"] = nomic_channel.id
    saveJson(chan, vc_file)
    return created_channel

def isVoiceOfUser(vc, member):
    global path
    vc_file = f"{path}/guilds/{str(vc.guild.id)}/channels/{str(vc.id)}.json"
    vc_conf = loadJson(vc_file)
    if vc_conf["ownerid"] == member.id:
        return True
    else:
        return False

async def changeNomicPerms(mode, vc, member):
    global path
    vc_file = f"{path}/guilds/{str(vc.guild.id)}/channels/{str(vc.id)}.json"
    vc_conf = loadJson(vc_file)
    nomic_channel = discord.utils.get(vc.guild.channels, id=vc_conf["nomic"])
    if mode == "deny":
        await nomic_channel.set_permissions(member, view_channel=False)
    else:
        await nomic_channel.set_permissions(member, view_channel=True)

async def clearTrash(client):
    global path
    if not os.path.isdir(f"{path}/guilds/"):
        os.mkdir(f"{path}/guilds")
    guilds_list = os.listdir(f"{path}/guilds/")
    for guild in guilds_list:
        guild_object = client.get_guild(int(guild))
        if os.path.isdir(f"{path}/guilds/{guild}/channels"):
            channels_list = os.listdir(f"{path}/guilds/{guild}/channels/")
            for channel in channels_list:
                channel_id = channel[:-5]
                try:
                    selected_channel = discord.utils.get(guild_object.voice_channels, id=int(channel_id))
                    channel_owner = loadJson(f"{path}/guilds/{guild}/channels/{channel}")["ownerid"]
                    remove_channel = True
                    for member in selected_channel.members:
                        if member.id == channel_owner:
                            remove_channel = False
                    if remove_channel:
                        await removeUserVoice(selected_channel)
                except:
                    os.remove(f"{path}/guilds/{guild}/channels/{channel_id}.json")

#async def autoClearTrash(client):
    # execute clearTrash every 120 seconds

def getHelpMessage(ctx, version):
    
    #channelExists(number, guild, type="Voice")
    
    config = loadJson("config.json")
    
    if ctx.guild is not None:
        if channelExists(guildConfGet(ctx.guild, 'channel'), ctx.guild, type="Voice"):
            desc_channel = getMsg("help_channel_set", guild=ctx.guild).format(channelGetName(guildConfGet(ctx.guild, 'channel'), ctx.guild))
        else:
            desc_channel = getMsg("help_channel_none", guild=ctx.guild)
        
        if channelExists(guildConfGet(ctx.guild, 'category'), ctx.guild, type="Any"):
            desc_category = getMsg("help_category_set", guild=ctx.guild).format(channelGetName(guildConfGet(ctx.guild, 'category'), ctx.guild))
        else:
            desc_category = getMsg("help_category_none", guild=ctx.guild)
        
        desc_locale = getMsg("help_locale", guild=ctx.guild).format(getMsg("locale_name", ctx.guild))

        description = "\n".join([desc_locale, desc_channel, desc_category])

        embed=discord.Embed(title=getMsg("help_title", ctx.guild), description=description, color=strToColor(config["color_default"]))
    else:
        embed=discord.Embed(title=getMsg("help_title_dm", ctx.guild), color=strToColor(config["color_default"]))
    
    embed.set_author(name=f'{config["bot_name"]} v{str(version)}', url=config["bot_site"], icon_url=config["bot_icon"])
    
    if ctx.author.id == config["owner"]:
        embed.add_field(name=f"/shutdown", value=getMsg("help_cmd_shutdown", ctx.guild), inline=False)
    
    embed.add_field(name=f"/channel set", value=getMsg("help_cmd_channel", ctx.guild), inline=False)
    embed.add_field(name=f"/category set", value=getMsg("help_cmd_category", ctx.guild), inline=False)
    embed.add_field(name=f"/locale set", value=getMsg("help_cmd_locale", ctx.guild), inline=False)
    
    if ctx.guild is None:
        embed.set_footer(text=getMsg("help_server", ctx.guild))
    else:
        embed.set_footer(text=getMsg("help_notice_id", ctx.guild))
    
    return embed

async def guildConfigured(guild):

    output = {}
    config = loadJson("config.json")

    for kind in ["channel", "category"]:
        if guildConfGet(guild, kind) is not None:
            try:
                guild_object = discord.utils.get(guild.categories, id=guildConfGet(guild, kind))
                output[kind] = getMsg("configured_"+kind, guild).format(guild_object.name)
            except Exception as exp:
                output[kind] = getMsg("unconfigured_"+kind, guild)
        else:
            output[kind] = getMsg("unconfigured_"+kind, guild)

    return getMsg("server_config", guild).format(getMsg("info_locale", guild).format(getMsg("locale_name", guild)), output["channel"], output["category"])
