import json, os, sys

try:
    import discord
except Exception as exp:
    print(f"Module discord.py is not installed. Make sure to run 'pip install -r requirements.txt' before first start")
    sys.exit()

from functions import *
#from discord_slash import SlashCommand, SlashContext

pid = os.getpid()

intents = discord.Intents().all()
client = discord.Client(intents=intents)
#slash = SlashCommand(client)

@client.event
async def on_ready():

    print('Logged in as {0.user}'.format(client))
    
    config = loadJson("config.json")
    
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=config["bot_activity"]))
    
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
            
            await message.channel.send(getMsg("shutdown"))
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
                            
                            await message.channel.send(getMsg("reset_channel"))
                            
                        else:
                            
                            await message.channel.send(getMsg("none_channel"))
                        
                    else:
                    
                        selected_channel = discord.utils.get(message.guild.channels, id=int(fullcmd[1]))
                        
                        guildConfSet(message.guild.id, "channel", int(fullcmd[1]))
                        
                        await message.channel.send(getMsg("result_channel").format(selected_channel.name))
                        
                        if guildConfGet(message.guild.id, "category") is None:
                            
                            await message.channel.send(getMsg("warn_category").format(prefix))
                    
                except Exception as exp:
                    
                    #print(exp)
                    
                    await message.channel.send(getMsg("usage_channel").format(prefix))
                
            else:
                
                await message.channel.send(getMsg("command_forbidden"))

        else:
            await message.channel.send(getMsg("command_in_dm"))
        
    elif message.content.startswith(f"{prefix}category"):
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
            
                try:
                
                    if fullcmd[1] == "reset":
                        
                        if guildConfGet(message.guild.id, "category") is not None:
                        
                            guildConfReset(message.guild.id, "category")
                            
                            await message.channel.send(getMsg("reset_category"))
                            
                        else:
                            
                            await message.channel.send(getMsg("none_category"))
                        
                    else:
                    
                        selected_category = discord.utils.get(message.guild.channels, id=int(fullcmd[1]))
                        
                        guildConfSet(message.guild.id, "category", int(fullcmd[1]))
                        
                        await message.channel.send(getMsg("result_category").format(selected_category.name))
                        
                        if guildConfGet(message.guild.id, "channel") is None:
                            
                            await message.channel.send(getMsg("warn_channel").format(prefix))
                    
                except Exception as exp:
                
                    #print(exp)
                    
                    await message.channel.send(getMsg("usage_category").format(prefix))
                
            else:
                
                await message.channel.send(getMsg("command_forbidden"))
            
        else:
            await message.channel.send(getMsg("command_in_dm"))

    elif message.content.startswith(f"{prefix}prefix"):
        
        fullcmd = message.content.split()
        
        if message.guild is not None:
        
            if message.author.guild_permissions.administrator:
            
                try:
                
                    if fullcmd[1] == "reset":
                    
                        if guildConfGet(message.guild.id, "prefix") is not None:
                        
                            guildConfReset(message.guild.id, "prefix")
                            
                            await message.channel.send(getMsg("reset_prefix").format(config["bot_prefix"]))
                            
                        else:
                            
                            await message.channel.send(getMsg("none_prefix").format(prefix))
                        
                    else:
                        
                        guildConfSet(message.guild.id, "prefix", fullcmd[1])
                        
                        await message.channel.send(getMsg("result_prefix").format(fullcmd[1]))
                    
                except:
                    
                    await message.channel.send(getMsg("usage_prefix").format(prefix))
                
            else:
                await message.channel.send(getMsg("command_forbidden"))
            
        else:
            await message.channel.send(getMsg("command_in_dm"))

    elif message.content.startswith(f"{prefix}help"):
        if message.author.id == config["owner"]:
            if message.guild is not None:
                await message.channel.send(await guildConfigured(message.guild) + getMsg("help").format(getMsg("help_owner").format(prefix), prefix, prefix, prefix, prefix))
            else:
                await message.channel.send(getMsg("help").format(getMsg("help_owner").format(prefix), prefix, prefix, prefix, prefix))
        else:
            if message.guild is not None:
                await message.channel.send(await guildConfigured(message.guild) + getMsg("help").format("", prefix, prefix, prefix))
            else:
                await message.channel.send(getMsg("help").format("", prefix, prefix, prefix))

client.run(loadJson("config.json")["bot_token"])