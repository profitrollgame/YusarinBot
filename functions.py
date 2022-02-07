import os
import sys
import json
import shutil
import discord

from datetime import datetime
from pathlib import Path

path = Path(__file__).resolve().parent

log_size = 512

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
def appendLog(message, guild="none"):
    global path
    
    message_formatted = f'[{datetime.now().strftime("%d.%m.%Y")}] [{datetime.now().strftime("%H:%M:%S")}] [{str(guild)}] {message}'
    
    print(message_formatted)

    checkSize()

    log = open(path + '/logs/latest.log', 'a')
    log.write(f'{message_formatted}\n')
    log.close()

def saveJson(value, filename):
    with open(filename, 'w', encoding="utf-8") as f:
        json.dump(value, f, indent=4, ensure_ascii=False)
        f.close()

def loadJson(filename):
    try:
        with open(filename, 'r', encoding="utf-8") as json_file:
            output = json.load(json_file)
            json_file.close()
    except Exception as exp:
        appendLog(f"Could not get contents of json file {filename} due to exception {exp}")
        output = {}
    return output

def guildConfGet(guild, variable):
    global path
    config = loadJson(f"{path}/guilds/{str(guild)}/config.json")
    try:
        return config[variable]
    except:
        return None

def guildConfSet(guild, variable, value):
    global path
    config = loadJson(f"{path}/guilds/{str(guild)}/config.json")
    config[variable] = value
    try:
        saveJson(config, f"{path}/guilds/{str(guild)}/config.json")
    except:
        os.mkdir(f"{path}/guilds/{str(guild)}")
        os.mkdir(f"{path}/guilds/{str(guild)}/channels")
        saveJson(config, f"{path}/guilds/{str(guild)}/config.json")

def guildConfReset(guild, variable):
    global path
    config = loadJson(f"{path}/guilds/{str(guild)}/config.json")
    del config[variable]
    try:
        saveJson(config, f"{path}/guilds/{str(guild)}/config.json")
    except:
        os.mkdir(f"{path}/guilds/{str(guild)}")
        os.mkdir(f"{path}/guilds/{str(guild)}/channels")
        saveJson(config, f"{path}/guilds/{str(guild)}/config.json")

def guildLocaleGet(guild):
    global path
    config = loadJson(f"{path}/config.json")
    try:
        locale = guildConfGet(guild.id, "locale")
    except:
        return config["bot_locale"]
    if locale is None:
        return config["bot_locale"]
    else:
        return locale

def getMsg(string, guild):
    global path
    config = loadJson("config.json")
    try:
        locale = loadJson(f'{path}/locale/{guildLocaleGet(guild)}.json')
        return locale["messages"][string]
    except Exception as exp:
        appendLog(f"Could not get locale string named {string} due to exception {exp}")
        return f"Could not get locale string {string}"

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
    channels_list = os.listdir(f"{path}/guilds/{str(vc.guild.id)}/channels/")
    if f"{vc.id}.json" in channels_list:
        vc_file = f"{path}/guilds/{str(vc.guild.id)}/channels/{str(vc.id)}.json"
        vc_conf = loadJson(vc_file)
        
        needed_channel = discord.utils.get(vc.guild.channels, id=vc.id)
        nomic_channel = discord.utils.get(vc.guild.channels, id=vc_conf["nomic"])
        
        os.remove(vc_file)
        
        await needed_channel.delete()
        appendLog(f"Removed voice channel {str(needed_channel.id)} of user {str(vc_conf['ownerid'])}", guild=vc.guild.id)
        await nomic_channel.delete()
        appendLog(f"Removed nomic channel {str(nomic_channel.id)} of channel {str(needed_channel.id)}", guild=vc.guild.id)
    else:
        return

async def createUserVoice(vc, category, member):
    global path
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
    appendLog(f"Created voice channel {str(created_channel.id)} for user {str(member.id)}", guild=vc.guild.id)
    if not os.path.isdir(f"{path}/guilds/{str(created_channel.guild.id)}/channels"):
        os.mkdir(f"{path}/guilds/{str(created_channel.guild.id)}/channels")
    vc_file = f"{path}/guilds/{str(created_channel.guild.id)}/channels/{str(created_channel.id)}.json"
    chan["ownerid"] = member.id
    saveJson(chan, vc_file)
    nomic_channel = await vc.guild.create_text_channel(getMsg("name_nomic", vc.guild).format(created_channel.id), category=category, overwrites=overwrites_nomic, topic=getMsg("description_nomic", vc.guild).format(str(created_channel.id)))
    appendLog(f"Created nomic channel {str(nomic_channel.id)} for channel {str(created_channel.id)}", guild=vc.guild.id)
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

async def guildConfigured(guild):

    output = {}
    config = loadJson("config.json")

    for kind in ["channel", "category", "prefix"]:
        if guildConfGet(guild.id, kind) is not None:
            try:
                if kind == "channel":
                    guild_object = discord.utils.get(guild.channels, id=guildConfGet(guild.id, kind))
                    output[kind] = getMsg("configured_"+kind, guild).format(guild_object.name)
                elif kind == "category":
                    guild_object = discord.utils.get(guild.categories, id=guildConfGet(guild.id, kind))
                    output[kind] = getMsg("configured_"+kind, guild).format(guild_object.name)
                elif kind == "prefix":
                    output[kind] = getMsg("info_prefix", guild).format(guildConfGet(guild.id, kind))
            except Exception as exp:
                if kind == "prefix":
                    output[kind] = getMsg("info_prefix", guild).format(config["bot_prefix"])
                else:
                    output[kind] = getMsg("unconfigured_"+kind, guild)
        else:
            if kind == "prefix":
                output[kind] = getMsg("info_prefix", guild).format(config["bot_prefix"])
            else:
                output[kind] = getMsg("unconfigured_"+kind, guild)

    return getMsg("server_config", guild).format(output["prefix"], getMsg("info_locale", guild).format(getMsg("locale_name", guild)), output["channel"], output["category"])
