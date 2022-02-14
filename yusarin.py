import os
import sys
import json
import shutil
import requests
import threading

try:
    import discord
except Exception as exp:
    print(f"Module discord.py is not installed. Make sure to run 'pip install -r requirements.txt' before first start")
    sys.exit()

from functions import *
pid = os.getpid()
version = 1.4

if loadJson("config.json")["owner"] == "SET-OWNER-ID" or loadJson("config.json")["bot_token"] == "SET-BOT-TOKEN":
    print(f"Bot is not correctly configured.\nMake sure you've set up owner id and bot token in {path}/config.json\nLearn more here: https://github.com/profitrollgame/YusarinBot")
    sys.exit()

if loadJson("config.json")["check_for_updates"]:
    try:
        serv_ver = requests.get("https://www.end-play.xyz/yusarin/version.txt").text.replace('\n', '')
        if float(serv_ver) > version:
            appendLog(f"YusarinBot version {serv_ver} is available. Download new version here: https://github.com/profitrollgame/YusarinBot/releases/latest")
            appendLog(f"Currently using YusarinBot v{str(version)}")
    except Exception as exp:
        appendLog(f"Could not get YusarinBot cloud version due to {exp}. Currently using {str(version)}")

intents = discord.Intents().all()
client = discord.Client(intents=intents)

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

# ==========================================================================================

@client.event
async def on_message(message):

    config = loadJson("config.json")
    
    if message.guild is not None:
        try:
            prefix = guildConfGet(message.guild, "prefix")
            if prefix is None:
                prefix = config["bot_prefix"]
        except Exception as exp:
            print(exp)
            prefix = config["bot_prefix"]
    else:
        prefix = config["bot_prefix"]

    if message.author == client.user:
        
        return

    if message.content in [f"{prefix}reboot", f"{prefix}restart", f"{prefix}shutdown", f"{prefix}die"]:
        
        gotCommand(message)
        
        if message.author.id == config["owner"]:
            
            await message.reply(embed=makeEmbed(description=getMsg("shutdown", message.guild).format(message.author), color=strToColor(config["color_default"])), mention_author=False)
            os.system(f"kill -9 {str(pid)}")
            
        else:
            
            return
        
    elif message.content.startswith(f"{prefix}channel"):
        
        gotCommand(message)
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
                
                try:
                    
                    if fullcmd[1] == "reset":
                        
                        if guildConfGet(message.guild, "channel") is not None:
                            
                            guildConfReset(message.guild, "channel")
                            
                            await message.reply(embed=makeEmbed(title=getMsg("reset_channel_title", message.guild), description=getMsg("reset_channel_description", message.guild).format(prefix), color=strToColor(config["color_ok"])), mention_author=False)
                            
                        else:
                            
                            await message.reply(embed=makeEmbed(title=getMsg("hint_none_channel_title", message.guild), description=getMsg("hint_none_channel_description", message.guild).format(prefix), color=strToColor(config["color_warn"])), mention_author=False)
                        
                    else:
                    
                        selected_channel = discord.utils.get(message.guild.channels, id=int(fullcmd[1]))

                        if isinstance(selected_channel, discord.VoiceChannel):
                        
                            guildConfSet(message.guild, "channel", int(fullcmd[1]))
                            
                            await message.reply(embed=makeEmbed(title=getMsg("set_channel_title", message.guild), description=getMsg("set_channel_description", message.guild).format(selected_channel.name), color=strToColor(config["color_ok"])), mention_author=False)
                        
                            if guildConfGet(message.guild, "category") is None:
                            
                                await message.channel.send(embed=makeEmbed(title=getMsg("hint_none_category_title", message.guild), description=getMsg("hint_none_category_description", message.guild).format(prefix), color=strToColor(config["color_warn"])))
                
                        else:

                            await message.reply(embed=makeEmbed(title=getMsg("error_text_channel_title", message.guild), description=getMsg("error_text_channel_description", message.guild), color=strToColor(config["color_error"])), mention_author=False)
    
                except Exception as exp:
                    
                    if debug:
                        print(exp)
                    
                    await message.reply(embed=makeEmbed(title=getMsg("error_channel_title", message.guild), description=getMsg("error_channel_description", message.guild).format(prefix), footer=getMsg("help_notice_id", message.guild), color=strToColor(config["color_error"])), mention_author=False)
                
            else:
                
                await message.reply(embed=makeEmbed(title=getMsg("forbidden_title", message.guild), description=getMsg("forbidden_description", message.guild), color=strToColor(config["color_error"])), mention_author=False)

        else:
            await message.reply(embed=makeEmbed(title=getMsg("dm_title", message.guild), description=getMsg("dm_description", message.guild), color=strToColor(config["color_error"])), mention_author=False)
        
    elif message.content.startswith(f"{prefix}category"):
        
        gotCommand(message)
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
            
                try:
                
                    if fullcmd[1] == "reset":
                        
                        if guildConfGet(message.guild, "category") is not None:
                        
                            guildConfReset(message.guild, "category")
                            
                            await message.reply(embed=makeEmbed(title=getMsg("reset_category_title", message.guild), description=getMsg("reset_category_description", message.guild).format(prefix), color=strToColor(config["color_ok"])), mention_author=False)
                            
                        else:
                            
                            await message.reply(embed=makeEmbed(title=getMsg("hint_none_category_title", message.guild), description=getMsg("hint_none_category_description", message.guild).format(prefix), color=strToColor(config["color_warn"])), mention_author=False)
                        
                    else:
                    
                        selected_category = discord.utils.get(message.guild.channels, id=int(fullcmd[1]))
                        
                        guildConfSet(message.guild, "category", int(fullcmd[1]))
                        
                        await message.reply(embed=makeEmbed(title=getMsg("set_category_title", message.guild), description=getMsg("set_category_description", message.guild).format(selected_category.name), color=strToColor(config["color_ok"])), mention_author=False)
                        
                        if guildConfGet(message.guild, "channel") is None:
                            
                            await message.channel.send(embed=makeEmbed(title=getMsg("hint_none_channel_title", message.guild), description=getMsg("hint_none_channel_description", message.guild).format(prefix), color=strToColor(config["color_warn"])))
                    
                except Exception as exp:
                
                    if debug:
                        print(exp)
                    
                    await message.reply(embed=makeEmbed(title=getMsg("error_category_title", message.guild), description=getMsg("error_category_description", message.guild).format(prefix), footer=getMsg("help_notice_id_category", message.guild), color=strToColor(config["color_error"])), mention_author=False)
                
            else:
                
                await message.reply(embed=makeEmbed(title=getMsg("forbidden_title", message.guild), description=getMsg("forbidden_description", message.guild), color=strToColor(config["color_error"])), mention_author=False)
            
        else:
            await message.reply(embed=makeEmbed(title=getMsg("dm_title", message.guild), description=getMsg("dm_description", message.guild), color=strToColor(config["color_error"])), mention_author=False)

    elif message.content.startswith(f"{prefix}prefix"):
        
        gotCommand(message)
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
            
                try:
                
                    if fullcmd[1] == "reset":
                    
                        if guildConfGet(message.guild, "prefix") is not None:
                        
                            guildConfReset(message.guild, "prefix")
                            
                            await message.reply(embed=makeEmbed(title=getMsg("reset_prefix_title", message.guild), description=getMsg("reset_prefix_description", message.guild).format(config["bot_prefix"], config["bot_prefix"]), color=strToColor(config["color_ok"])), mention_author=False)
                            
                        else:
                            
                            await message.reply(embed=makeEmbed(title=getMsg("hint_none_prefix_title", message.guild), description=getMsg("hint_none_prefix_description", message.guild).format(prefix, prefix), color=strToColor(config["color_warn"])), mention_author=False)
                        
                    else:
                        
                        guildConfSet(message.guild, "prefix", fullcmd[1])
                        
                        await message.reply(embed=makeEmbed(title=getMsg("set_prefix_title", message.guild), description=getMsg("set_prefix_description", message.guild).format(fullcmd[1]), color=strToColor(config["color_ok"])), mention_author=False)
                    
                except:
                    
                    await message.reply(embed=makeEmbed(title=getMsg("error_prefix_title", message.guild), description=getMsg("error_prefix_description", message.guild).format(prefix), color=strToColor(config["color_error"])), mention_author=False)
                
            else:
                await message.reply(embed=makeEmbed(title=getMsg("forbidden_title", message.guild), description=getMsg("forbidden_description", message.guild), color=strToColor(config["color_error"])), mention_author=False)
            
        else:
            await message.reply(embed=makeEmbed(title=getMsg("dm_title", message.guild), description=getMsg("dm_description", message.guild), color=strToColor(config["color_error"])), mention_author=False)

    elif message.content.startswith(f"{prefix}locale"):
        
        gotCommand(message)
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
            
                try:
                
                    if fullcmd[1] == "reset":
                    
                        if guildConfGet(message.guild, "locale") is not None:
                        
                            guildConfReset(message.guild, "locale")
                            appendLog(f"Server's locale has been reset", message.guild)
                            await message.reply(embed=makeEmbed(title=getMsg("reset_locale_title", message.guild), description=getMsg("reset_locale_description", message.guild).format(getMsg("locale_name", message.guild), prefix), color=strToColor(config["color_ok"])), mention_author=False)
                            
                        else:
                            
                            await message.reply(embed=makeEmbed(title=getMsg("hint_none_locale_title", message.guild), description=getMsg("hint_none_locale_description", message.guild).format(getMsg("locale_name", message.guild), prefix), color=strToColor(config["color_warn"])), mention_author=False)
                        
                    else:
                        
                        for locale_file in os.listdir(f"{path}/locale/"):
                            if locale_file[:-5] == fullcmd[1]:
                                guildConfSet(message.guild, "locale", fullcmd[1])
                                appendLog(f"Server's locale is now set to {fullcmd[1]}", message.guild)
                                await message.reply(embed=makeEmbed(title=getMsg("set_locale_title", message.guild), description=getMsg("set_locale_description", message.guild).format(getMsg("locale_name", message.guild)), color=strToColor(config["color_ok"])), mention_author=False)
                                return
                         
                        locales = []
                    
                        for locale_file in os.listdir(f"{path}/locale/"):
                            locales.append(f"`{locale_file[:-5]}`")
                    
                        await message.reply(embed=makeEmbed(title=getMsg("error_locale_title", message.guild), description=getMsg("error_locale_description", message.guild).format(prefix, ", ".join(locales)), color=strToColor(config["color_error"])), mention_author=False)
                    
                except:
                    
                    locales = []
                    
                    for locale_file in os.listdir(f"{path}/locale/"):
                        locales.append(f"`{locale_file[:-5]}`")
                    
                    await message.reply(embed=makeEmbed(title=getMsg("error_locale_title", message.guild), description=getMsg("error_locale_description", message.guild).format(prefix, ", ".join(locales)), color=strToColor(config["color_error"])), mention_author=False)
                
            else:
                await message.reply(embed=makeEmbed(title=getMsg("forbidden_title", message.guild), description=getMsg("forbidden_description", message.guild), color=strToColor(config["color_error"])), mention_author=False)
            
        else:
            await message.reply(embed=makeEmbed(title=getMsg("dm_title", message.guild), description=getMsg("dm_description", message.guild), color=strToColor(config["color_error"])), mention_author=False)

    elif message.content.startswith(f"{prefix}help"):
        
        gotCommand(message)
        
        await message.reply(embed=getHelpMessage(message, version, prefix=prefix), mention_author=False)

#if loadJson("config.json")["auto_clear_trash"]:
    # run func

appendLog(f"Trying to log in...")

client.run(loadJson("config.json")["bot_token"])
