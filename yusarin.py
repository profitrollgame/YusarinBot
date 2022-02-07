import os
import sys
import json
import requests
import threading

try:
    import discord
except Exception as exp:
    print(f"Module discord.py is not installed. Make sure to run 'pip install -r requirements.txt' before first start")
    sys.exit()

from functions import *
pid = os.getpid()
version = 1.1

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
async def on_voice_state_update(member, before, after):

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
        if vc_to.id == guildConfGet(vc_to.guild.id, "channel"):
            if guildConfGet(vc_to.guild.id, "category") is not None:
                voice_chan = await createUserVoice(vc_to, discord.utils.get(vc_to.guild.categories, id=guildConfGet(vc_to.guild.id, "category")), member)
                try:
                    await member.move_to(voice_chan)
                except:
                    await removeUserVoice(voice_chan)
            else:
                appendLog(f"Category for guild {str(vc_to.guild.id)} is not set", guild=vc_to.guild.id)

# ==========================================================================================

@client.event
async def on_message(message):

    config = loadJson("config.json")
    
    if message.guild is not None:
        try:
            prefix = guildConfGet(message.guild.id, "prefix")
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
        
        if message.author.id == config["owner"]:
            
            await message.channel.send(getMsg("shutdown", message.guild))
            os.system(f"kill -9 {str(pid)}")
            
        else:
            
            return
        
    elif message.content.startswith(f"{prefix}channel"):
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
                
                try:
                    
                    if fullcmd[1] == "reset":
                        
                        if guildConfGet(message.guild.id, "channel") is not None:
                            
                            guildConfReset(message.guild.id, "channel")
                            
                            await message.channel.send(getMsg("reset_channel", message.guild))
                            
                        else:
                            
                            await message.channel.send(getMsg("none_channel", message.guild))
                        
                    else:
                    
                        selected_channel = discord.utils.get(message.guild.channels, id=int(fullcmd[1]))
                        
                        guildConfSet(message.guild.id, "channel", int(fullcmd[1]))
                        
                        await message.channel.send(getMsg("result_channel", message.guild).format(selected_channel.name))
                        
                        if guildConfGet(message.guild.id, "category") is None:
                            
                            await message.channel.send(getMsg("warn_category", message.guild).format(prefix))
                    
                except Exception as exp:
                    
                    #print(exp)
                    
                    await message.channel.send(getMsg("usage_channel", message.guild).format(prefix))
                
            else:
                
                await message.channel.send(getMsg("command_forbidden", message.guild))

        else:
            await message.channel.send(getMsg("command_in_dm", message.guild))
        
    elif message.content.startswith(f"{prefix}category"):
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
            
                try:
                
                    if fullcmd[1] == "reset":
                        
                        if guildConfGet(message.guild.id, "category") is not None:
                        
                            guildConfReset(message.guild.id, "category")
                            
                            await message.channel.send(getMsg("reset_category", message.guild))
                            
                        else:
                            
                            await message.channel.send(getMsg("none_category", message.guild))
                        
                    else:
                    
                        selected_category = discord.utils.get(message.guild.channels, id=int(fullcmd[1]))
                        
                        guildConfSet(message.guild.id, "category", int(fullcmd[1]))
                        
                        await message.channel.send(getMsg("result_category", message.guild).format(selected_category.name))
                        
                        if guildConfGet(message.guild.id, "channel") is None:
                            
                            await message.channel.send(getMsg("warn_channel", message.guild).format(prefix))
                    
                except Exception as exp:
                
                    #print(exp)
                    
                    await message.channel.send(getMsg("usage_category", message.guild).format(prefix))
                
            else:
                
                await message.channel.send(getMsg("command_forbidden", message.guild))
            
        else:
            await message.channel.send(getMsg("command_in_dm", message.guild))

    elif message.content.startswith(f"{prefix}prefix"):
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
            
                try:
                
                    if fullcmd[1] == "reset":
                    
                        if guildConfGet(message.guild.id, "prefix") is not None:
                        
                            guildConfReset(message.guild.id, "prefix")
                            
                            await message.channel.send(getMsg("reset_prefix", message.guild).format(config["bot_prefix"]))
                            
                        else:
                            
                            await message.channel.send(getMsg("none_prefix", message.guild).format(prefix))
                        
                    else:
                        
                        guildConfSet(message.guild.id, "prefix", fullcmd[1])
                        
                        await message.channel.send(getMsg("result_prefix", message.guild).format(fullcmd[1]))
                    
                except:
                    
                    await message.channel.send(getMsg("usage_prefix", message.guild).format(prefix))
                
            else:
                await message.channel.send(getMsg("command_forbidden", message.guild))
            
        else:
            await message.channel.send(getMsg("command_in_dm", message.guild))

    elif message.content.startswith(f"{prefix}locale"):
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
            
                try:
                
                    if fullcmd[1] == "reset":
                    
                        if guildConfGet(message.guild.id, "locale") is not None:
                        
                            guildConfReset(message.guild.id, "locale")
                            appendLog(f"Server's locale has been reset", message.guild.id)
                            await message.channel.send(getMsg("reset_locale", message.guild).format(getMsg("locale_name", message.guild)))
                            
                        else:
                            
                            await message.channel.send(getMsg("none_locale", message.guild).format(getMsg("locale_name", message.guild)))
                        
                    else:
                        
                        for locale_file in os.listdir(f"{path}/locale/"):
                            if locale_file[:-5] == fullcmd[1]:
                                guildConfSet(message.guild.id, "locale", fullcmd[1])
                                appendLog(f"Server's locale is now set to {fullcmd[1]}", message.guild.id)
                                await message.channel.send(getMsg("locale_set", message.guild))
                                return
                         
                        locales = []
                    
                        for locale_file in os.listdir(f"{path}/locale/"):
                            locales.append(f"`{locale_file[:-5]}`")
                    
                        await message.channel.send(getMsg("usage_locale", message.guild).format(prefix, ", ".join(locales)))
                    
                except:
                    
                    locales = []
                    
                    for locale_file in os.listdir(f"{path}/locale/"):
                        locales.append(f"`{locale_file[:-5]}`")
                    
                    await message.channel.send(getMsg("usage_locale", message.guild).format(prefix, ", ".join(locales)))
                
            else:
                await message.channel.send(getMsg("command_forbidden", message.guild))
            
        else:
            await message.channel.send(getMsg("command_in_dm", message.guild))

    elif message.content.startswith(f"{prefix}help"):
        if message.author.id == config["owner"]:
            if message.guild is not None:
                await message.channel.send(await guildConfigured(message.guild) + getMsg("help", message.guild).format(getMsg("help_owner", message.guild).format(prefix), prefix, prefix, prefix, prefix))
            else:
                await message.channel.send(getMsg("help", message.guild).format(getMsg("help_owner", message.guild).format(prefix), prefix, prefix, prefix, prefix))
        else:
            if message.guild is not None:
                await message.channel.send(await guildConfigured(message.guild) + getMsg("help").format("", prefix, prefix, prefix))
            else:
                await message.channel.send(getMsg("help", message.guild).format("", prefix, prefix, prefix))

#if loadJson("config.json")["auto_clear_trash"]:
    # run func

appendLog(f"Trying to log in...")

client.run(loadJson("config.json")["bot_token"])