import discord
from discord import Intents, FFmpegPCMAudio, Color
import os
from dotenv import load_dotenv
import pathlib
from discord.ext import commands, tasks
import asyncio
from discord.ext.commands import MemberNotFound, Cog
from datetime import datetime
from youtubesearchpython import VideosSearch
import yt_dlp
from datetime import datetime, timedelta
import traceback
import sys
import json
import shutil

#print(os.environ["PATH"].split(os.pathsep))

class BotData:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.json_file_path):
            with open(self.json_file_path, "r") as file:
                data = json.load(file)
                # Convert authority_roles_list from set to list
                for guild_id, guild_data in data.get("permissions_dict", {}).items():
                    guild_data["authority_roles_list"] = list(guild_data.get("authority_roles_list", []))
                return data
        else:
            return {
                "kick_cooldown": {},
                "permissions_dict": {},
                "song_queue": [],
                "guild_queue": {},
                "mute_Member_list": []
            }

    def save_data(self):
        for guild_id, guild_data in self.data.get("permissions_dict", {}).items():
            guild_data["authority_roles_list"] = list(guild_data.get("authority_roles_list", []))
        with open(self.json_file_path, "w") as file:
            json.dump(self.data, file, indent=4)

    def update_and_save_data(self, kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list):
        self.data["kick_cooldown"] = kick_cooldown
        self.data["permissions_dict"] = permissions_dict
        self.data["song_queue"] = song_queue
        self.data["guild_queue"] = guild_queue
        self.data["mute_Member_list"] = mute_Member_list
        self.save_data()

# Initialize BotData
json_file_path = "bot_data.json"
bot_data = BotData(json_file_path)

song_name = None
local_dir_path = './discord_songs'
num = {}

intents = discord.Intents.all()

client = discord.Client(intents=intents)

class MyBot(commands.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MemberNotFound):
            first_content = f"I could not find member '{error.argument}'. Please try again"
            first = discord.Embed(title="Member Not Found", description=first_content, color=Color.random())
            await ctx.send(embed=first)

        elif isinstance(error, commands.MissingRequiredArgument):
            second_content = f"{error.param.name} is a required argument."
            second = discord.Embed(title="Missing Argument", description=second_content, color=Color.random())
            await ctx.send(embed=second)
        else:
            third_content = f'||In {ctx.command}|| You have entered something wrong. Error: {error}'
            third = discord.Embed(title="Error Message", description=third_content, color=Color.random())
            await ctx.send(embed=third)

            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

client = MyBot(command_prefix='++', intents=intents)
client.remove_command('help')

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.command(name="help", help="Show this help message.")
async def help_command(ctx):
    command_order = [
        "help",
        "hello",
        "details",
        "role_list",
        "name_with_role_list",
        "mute",
        "unmute",
        "permission",
        "assign_role",
        "kick",
        "play",
        "add_song",
        "song_list",
        "current_playing",
        "skip",
        "disconnect",
    ]

    embed = discord.Embed(
        title="Available Commands",
        description="Here are the available commands:",
        color=discord.Color.random()
    )

    for command_name in command_order:
        command = client.get_command(command_name)
        if command:
            embed.add_field(name=command_name, value=command.help, inline=False)

    await ctx.send(embed=embed)


def author_context(ctx):
    return ctx.author

def get_sorted_roles(ctx):
    return sorted(ctx.guild.roles, key=lambda x: x.position, reverse=True)

class UserWithFallback(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.UserConverter().convert(ctx, argument)
        except commands.UserNotFound:
            try:
                return await commands.MemberConverter().convert(ctx, argument)
            except commands.MemberNotFound:
                return None

@client.command(name="hello", help="Say hello to our Oreki. Example: ++hello")
async def hello(ctx):
    author = author_context(ctx)
    context = f"<@{author.id}>, I'm Oreki Houtarou. I am a student at Kamiyama High School and a member of the school's Classic Literature Club. I believe in 'energy conservatism'. Yoroshiku Onegaishimasu."
    embed = discord.Embed(
    title="Hello,",
    description=context,
    color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@client.command(name="details", help="Use this command to know the details about any member or bot. Example: ++details @username")
async def details(ctx, user: UserWithFallback=None):
    if user is None:
        first_content = "You forgot to mention a user. You need to mention a valid user."
        first = discord.Embed(title="Mention A User", description=first_content, color=Color.random())
        await ctx.send(embed=first)
        return
    
    if ctx.guild:
        member = ctx.guild.get_member(user.id)
        author = author_context(ctx)
        if member:
            member_details = f"Username: {member.name}\nID: {member.id}\nBanner: {user.banner}\nAvatar URL: {member.avatar}\nMember Since: {member.created_at.strftime('%d-%m-%Y %H:%M:%S')}\nGuild Member Since: {member.joined_at.strftime('%d-%m-%Y %H:%M:%S')}\n{member.name} Roles: {[role.name for role in member.roles if role.name != '@everyone']}"
            second_content = f"<@{author.id}> searched the details for the member <@{member.id}>:\n{member_details}"
            second = discord.Embed(title="Member Details", description=second_content, color=Color.random())
            await ctx.send(embed=second)
        else:
            third_content = "The mentioned member is not found on the server. Please mention a valid member from the server..."
            third = discord.Embed(title="Member Not Found", description=third_content, color=Color.random())
            await ctx.send(embed=third)
    elif user:
        fourth_content = f"Username: {user.name}\nID: {user.id}\nBanner: {user.banner}\nAvatar URL: {user.avatar}\nMember Since: {user.created_at.strftime('%d-%m-%Y %H:%M:%S')}"
        fourth = discord.Embed(title="User Details", description=fourth_content, color=Color.random())
        await ctx.send(embed=fourth)
    else:
        fifth_content = "The mentioned user is not found. Please mention a valid user..."
        fifth = discord.Embed(title="User Not Found", description=fifth_content, color=Color.random())
        await ctx.send(embed=fifth)

@client.command(name="role_list", help="Use this command to know how many roles (rankwise) are in your server. Example: ++role_list")
async def role_list(ctx):
    if ctx.guild:
        roles = get_sorted_roles(ctx)
        role_info = "\n".join([f"Role Name:{role.name}, Position:{num}" for num, role in enumerate(roles, start=1) if role.name != '@everyone'])
        first_content = f"\n```{role_info}```"
        first = discord.Embed(title="Role(s) List Rankwise", description=first_content, color=Color.random())
        await ctx.send(embed=first)
    else:
        second_content = "You can perform this command only in a server!"
        second = discord.Embed(title="No Role(s) In DM", description=second_content, color=Color.random())
        await ctx.send(embed=second)


@client.command(name="assign_role", help="Use this grant role(s) to other member. But only below yourself can be given to others. Choosen member(s) only. Example: ++assign_role @member @role")
async def assign_role(ctx, member: discord.Member, role: discord.Role):
    author = author_context(ctx)
    permissions_dict = bot_data.data["permissions_dict"]
    
    if ctx.guild:
        all_roles = ctx.guild.roles [::-1]
        all_roles_id = [a.id for a in all_roles]
        top_role = get_sorted_roles(ctx)[0]
        id_list = []
        index = None
        assign_permission = []
        
        if member is None:
            eigth_content = "Please mention a member to assign."
            eigth = discord.Embed(title="Member Not Mentioned", description=eigth_content, color=Color.random())
            await ctx.send(embed=eigth)
        elif role is None:
            ninth_content = "Please mention a role to assign."
            ninth = discord.Embed(title="Reason Not Mentioned", description=ninth_content, color=Color.random())
            await ctx.send(embed=ninth)
        elif member is None and role is None:
            tenth_content = "You need to mention the member and role..."
            tenth = discord.Embed(title="Mention Member And Role", description=tenth_content, color=Color.random())
            await ctx.send(embed=tenth)
        elif role in member.roles:
            seventh_content = f"{member.mention} already has {role.mention} role..."
            seventh = discord.Embed(title="Nothing New...", description=seventh_content, color=Color.random())
            await ctx.send(embed=seventh)
        for r in all_roles:
            role_id = r.id
            for key_outer, value_outer in permissions_dict.items():
                for key_inner, value_inner in value_outer.items():
                    if key_inner == "authority_roles_list" or top_role:
                        id_list.append(value_inner)
                        break
                    else:
                        first_content = f"{author.mention} first get permission from {top_role.mention}"
                        first = discord.Embed(title="Member With Role(s)", description=first_content, color=Color.random())
                        await ctx.send(embed=first)
                        return
            id_list.append(top_role.id)
        for prole in ctx.message.author.roles:
            if (prole.id in sublist for sublist in id_list):
                index = all_roles_id.index(prole.id)
        if index is not None:
            assign_permission = all_roles_id[index+1:]
            
        if assign_permission and role.id in assign_permission:
            await member.add_roles(role)
            third_context = f"{author.mention} assigned role to {member.mention}"
            third = discord.Embed(title="Role Assigned!!", description=third_context, color=Color.random())
            await ctx.send(embed=third)
        else:
            last_context = f"{author.mention} you can't assign your or above role(s)"
            last = discord.Embed(title="Unauthorized...", description=last_context, color=Color.random())
            await ctx.send(embed=last)
    else:
        second_content = "You can perform this command only in a server!"
        second = discord.Embed(title="No Role(s) In DM", description=second_content, color=Color.random())
        await ctx.send(embed=second)


@client.command(name="name_with_role_list", help="Use this command to know which member has which and how many roles. Example: ++name_with_role_list")
async def name_with_role_list(ctx):
    if ctx.guild:
        for member in ctx.guild.members:
            roles_for_member = [role.name for role in member.roles if role.name != '@everyone']
            first_content = f"{member.name}: {roles_for_member}\n"
            first = discord.Embed(title="Member With Role(s)", description=first_content, color=Color.random())
            await ctx.send(embed=first)
    else:
        second_content = "You can perform this command only in a server!"
        second = discord.Embed(title="No Role(s) In DM", description=second_content, color=Color.random())
        await ctx.send(embed=second)


@client.command(name="permission", help="Administrator Privileges. Example: ++permission @role")
async def permission(ctx, mentioned_role: discord.Role=None):
    kick_cooldown = bot_data.data["kick_cooldown"]
    permissions_dict = bot_data.data["permissions_dict"]
    song_queue = bot_data.data["song_queue"]
    guild_queue = bot_data.data["guild_queue"]
    mute_Member_list = bot_data.data["mute_Member_list"]
    
    if mentioned_role == None:
        embeded_content = "You have to mention a role!"
        embeded_ = discord.Embed(title="Missing Role", description=embeded_content, color=Color.random())
        await ctx.send(embed=embeded_)
    if ctx.guild:
        guild = ctx.guild
        if guild.id not in permissions_dict:
            permissions_dict[guild.id] = {'guild name': guild.name, 'authority_roles_list': []}
            bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)
        guild_permissions = permissions_dict[guild.id]
        authority_roles_list = guild_permissions['authority_roles_list']
        
        all_roles = get_sorted_roles(ctx)
        top_role = all_roles[0]
        sub_roles = all_roles[1:]
        author = author_context(ctx)
        
        if top_role in author.roles:
            if mentioned_role in sub_roles:
                if mentioned_role.id in authority_roles_list:
                    first_content = f"<@{author.id}>, authority for giving roles to others was already granted for {mentioned_role.mention} role."
                    first = discord.Embed(title="Authority Already Granted", description=first_content, color=Color.random())
                    await ctx.send(embed=first)
                    members_with_role = None
                else:
                    authority_roles_list.append(mentioned_role.id)
                    bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)
                    second_content = f"<@{author.id}>, based on the {top_role.mention} role granted authority to {mentioned_role.mention} role member(s) so that he/she/they can assign role(s) to the other members {mentioned_role.mention} below any roles."
                    second = discord.Embed(title="Authority Granted", description=second_content, color=Color.random())
                    await ctx.send(embed=second)
                    members_with_role = [member for member in ctx.guild.members if mentioned_role in member.roles]
                    
                if members_with_role is None:
                    return
                elif members_with_role:
                    members_list = "\n".join([member.mention for member in members_with_role])
                    fourth_content = f"\nMember(s) with the {mentioned_role.mention} role:\n{members_list}"
                    fourth = discord.Embed(title="Member(s) of Mentioned Role", description=fourth_content, color=Color.random())
                    await ctx.send(embed=fourth)
                else:
                    third_content = f"\nNo member(s) found with the {mentioned_role.mention} role."
                    third = discord.Embed(title="NIL Member(s)", description=third_content, color=Color.random())
                    await ctx.send(embed=third)
            else:
                fifth_content = f"You can't give {mentioned_role.mention} role."
                fifth = discord.Embed(title="Selected Wrong Role", description=fifth_content, color=Color.random())
                await ctx.send(embed=fifth)
        else:
            six_content = "You do not have the authority for this command."
            six = discord.Embed(title="Your Don't Have Authority", description=six_content, color=Color.random())
            await ctx.send(embed=six)
    else:
        last_content = "You can perform this command only in a server!"
        last = discord.Embed(title="No Permission Settings In DM", description=last_content, color=Color.random())
        await ctx.send(embed=last)

@client.command()
async def hidden(ctx):
    permissions_dict = bot_data.data["permissions_dict"]
    await ctx.send(permissions_dict)

kick_permission = False

async def kick_member(ctx, target_member: discord.User):
    kick_cooldown = bot_data.data["kick_cooldown"]
    permissions_dict = bot_data.data["permissions_dict"]
    song_queue = bot_data.data["song_queue"]
    guild_queue = bot_data.data["guild_queue"]
    mute_Member_list = bot_data.data["mute_Member_list"]
    
    await target_member.kick()
    kick_cooldown[ctx.author.id] = {"time": str(datetime.now())}
    bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)
    first_content = f'{target_member.mention} has been kicked.'
    first = discord.Embed(title="Member Kicked!", description=first_content, color=Color.random())
    await ctx.send(embed=first)

async def mutemember(ctx, member: discord.Member):
    mute_Member_list = bot_data.data["mute_Member_list"]
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if member.id in mute_Member_list:
        return
    else:
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, speak=False, send_messages=False, read_message_history=True, read_messages=True)
        await member.add_roles(role)
    
async def unmutemember(ctx, member: discord.Member):
    mute_Member_list = bot_data.data["mute_Member_list"]
    if member.id not in mute_Member_list:
        return
    else:
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            pass
        else:
            await member.remove_roles(role)

@client.command(name="mute", help="Use to mute member. Example: ++mute @username reason for being muted")
async def mute(ctx, member: discord.Member=None, *, reason=None):
    author = author_context(ctx)
    kick_cooldown = bot_data.data["kick_cooldown"]
    permissions_dict = bot_data.data["permissions_dict"]
    song_queue = bot_data.data["song_queue"]
    guild_queue = bot_data.data["guild_queue"]
    mute_Member_list = bot_data.data["mute_Member_list"]
    
    if member is None:
        first_content = "Please mention a member to mute."
        first = discord.Embed(title="Member Not Mentioned", description=first_content, color=Color.random())
        await ctx.send(embed=first)
    elif reason is None:
        second_content = "Please state your reason."
        second = discord.Embed(title="Reason Not Mentioned", description=second_content, color=Color.random())
        await ctx.send(embed=second)
    elif member is None and reason is None:
        third_content = "You need to mention the member and also state your reason to use mute."
        third = discord.Embed(title="Mention Member And State Reason", description=third_content, color=Color.random())
        await ctx.send(embed=third)
        return
    elif member == author:
        fifth_content = "You can't mention yourself"
        fifth = discord.Embed(title="Can't Use It Like This", description=fifth_content, color=Color.random())
        await ctx.send(embed=fifth)
    elif member.id in mute_Member_list:
        last_content = f"{member.mention} is already muted..."
        last = discord.Embed(title="Already Muted!!", description=last_content, color=Color.random())
        await ctx.send(embed=last)
    elif member not in ctx.guild.members:
        sixth_content = "The mentioned user is not found. Please mention a valid user..."
        sixth = discord.Embed(title="User Not Found", description=sixth_content, color=Color.random())
        await ctx.send(embed=sixth)
    else:
        await mutemember(ctx, member)
        mute_Member_list.append(member.id)
        bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)
        fourth_statement = f"{member.mention} muted!! {reason}"
        fourth = discord.Embed(title="Member Muted", description=fourth_statement, color=Color.random())
        await ctx.send(embed=fourth)

@client.command(name="unmute", help="Use to unmute member. Example: ++unmute @username")
async def unmute(ctx, member: discord.Member=None):
    author = author_context(ctx)
    kick_cooldown = bot_data.data["kick_cooldown"]
    permissions_dict = bot_data.data["permissions_dict"]
    song_queue = bot_data.data["song_queue"]
    guild_queue = bot_data.data["guild_queue"]
    mute_Member_list = bot_data.data["mute_Member_list"]
    
    if member is None:
        first_content = "Please mention a valid member to umute."
        first = discord.Embed(title="Member Not Mentioned", description=first_content, color=Color.random())
        await ctx.send(embed=first)
    elif member == author:
        fifth_content = "You can't mention yourself"
        fifth = discord.Embed(title="Can't Use It Like This", description=fifth_content, color=Color.random())
        await ctx.send(embed=fifth)
    elif member.id not in mute_Member_list:
        sixth_content = "You can't unmute a unmuted member"
        sixth = discord.Embed(title="First Mute To Use Unmute", description=sixth_content, color=Color.random())
        await ctx.send(embed=sixth)
    elif member not in ctx.guild.members:
        last_content = "The mentioned user is not found. Please mention a valid user..."
        last = discord.Embed(title="User Not Found", description=last_content, color=Color.random())
        await ctx.send(embed=last)
    else:
        mute_Member_list.remove(member.id)
        bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)
        await unmutemember(ctx, member)
        seventh_content = "Unmute done."
        seventh = discord.Embed(title="Unmuted", description=seventh_content, color=Color.random())
        await ctx.send(embed=seventh)

        

@client.command(name="kick", help="Use to kick member. Example: ++kick @username")
async def kick(ctx, member: discord.Member=None):
    permissions_dict = bot_data.data["permissions_dict"]
    kick_cooldown = bot_data.data["kick_cooldown"]
    
    global kick_permission
    global num
    
    if member is None:
        first_content = "Please mention a user to kick."
        first = discord.Embed(title="Member Not Mentioned", description=first_content, color=Color.random())
        await ctx.send(embed=first)
        return

    if member in ctx.guild.members:
        all_roles = get_sorted_roles(ctx)
        top_role = all_roles[0]
        role_id = []
        author = author_context(ctx)
        
        if top_role in member.roles:
            if author.id not in num:
                num[author.id] = 0
            num[author.id] += 1
            warning_message_content = f"{author.mention} you can't or should not try to kick {member.mention}. 3 warning will be given, more than that you will be muted automatically. Current Warning Count: {num.get(author.id)}"
            warning_message = discord.Embed(title="Warning Message!!", description=warning_message_content, color=Color.random())
            await ctx.send(embed=warning_message)
            if num.get(author.id) == 3:
                await mutemember(ctx, author)
                mute_message_content = f'{member.mention} will be muted due to misuse of the command.'
                mute_message = discord.Embed(title="Abuse Of Power", description=mute_message_content, color=Color.random())
                send_message_denied = await ctx.send(embed=mute_message)
            return
        
        for key_outer, value_outer in permissions_dict.items():
            #guild_id = key_outer
            for key_inner, value_inner in value_outer.items():
                if key_inner == "authority_roles_list":
                    for i in value_inner:
                        role_id.append(i)
        
        for role in ctx.message.author.roles:
            for role.id in role_id:
                kick_permission = True
                    
        if ctx.guild.id in permissions_dict and kick_permission:
            if ctx.author.id in kick_cooldown:
                last_kick_time = datetime.strptime(kick_cooldown[ctx.author.id]["time"], "%Y-%m-%d %H:%M:%S.%f")
                cooldown_duration = timedelta(hours=24)

                if datetime.now() - last_kick_time < cooldown_duration:
                    wait_message_content = f"{ctx.author.mention} wait for the decision of {top_role.mention}"
                    wait_message = discord.Embed(title="Wait For 1 Mintue...", description=wait_message_content, color=Color.random())
                    waiting_message = await ctx.send(embed=wait_message)
                    
                    await mutemember(ctx, member)
                    mute_message_content = f'{member.mention} will be muted due to the kick command.'
                    mute_message = discord.Embed(title="Decision Is Pending", description=mute_message_content, color=Color.random())
                    send_message_denied = await ctx.send(embed=mute_message)
                    
                    dm_channel = None
                    for user in ctx.guild.members:
                        if top_role in user.roles and user != ctx.guild.me:
                            if dm_channel is None:
                                dm_channel = await user.create_dm()
                            second_content = f"{ctx.author.mention} from {ctx.guild.name} server is attempting to kick {member.mention} in 24 hours. Do you approve? (React with ✅ for Yes, ❌ for No)"
                            second = discord.Embed(title="Warning Message About Member Kicked!!", description=second_content, color=Color.red())
                            dm_message = await dm_channel.send(embed=second)
                            

                            await dm_message.add_reaction("✅")  # Yes
                            await dm_message.add_reaction("❌")  # No
                            
                            await asyncio.sleep(1)

                            def reaction_check(reaction, user):
                                return reaction.message.id == dm_message.id and str(reaction.emoji) in ['✅', '❌']

                            try:
                                print("Waiting for reaction...")
                                reaction, _ = await client.wait_for('reaction_add', check=reaction_check, timeout=60)
                                print("Reaction received!")
                                if str(reaction.emoji) == '❌':
                                    await waiting_message.delete()
                                    await send_message_denied.delete()
                                    
                                    await unmutemember(ctx, member)
                                    reject_message_content = f"{top_role.mention} has denied the request. {member.mention} was not kicked and will be unmuted..."
                                    reject_message = discord.Embed(title="Kick Denied By Administrator!!", description=reject_message_content, color=Color.random())
                                    await ctx.send(embed=reject_message)
                                    return
                                else:
                                    await waiting_message.delete()
                                    await send_message_denied.delete()
                                    
                                    await kick_member(ctx, member)
                                    return
                            except asyncio.TimeoutError:
                                await waiting_message.delete()
                                await send_message_denied.delete()
                                    
                                await unmutemember(ctx, member)
                                fourth_content = f"{top_role.mention} did not respond in time. {member.mention} was not kicked. {member.mention} will be unmuted..."
                                fourth = discord.Embed(title="Administrator Offline", description=fourth_content, color=Color.random())
                                await ctx.send(embed=fourth)
                                return
                else:
                    await kick_member(ctx, member)
                    return
            else:
                await kick_member(ctx, member)
                return
        else:
            fifth_content = "You don't have permission to use this command."
            fifth = discord.Embed(title="Denied!!", description=fifth_content, color=Color.random())
            await ctx.send(embed=fifth)
    else:
        sixth_content = f"You can't kick member(s) in DM."
        sixth = discord.Embed(title="DM Unauthorized", description=sixth_content, color=Color.random())
        await ctx.send(embed=sixth)



async def search_youtube_videos(query):
    videos_search = VideosSearch(query, limit=1)
    results = videos_search.result()

    for video in results['result']:
        title = video['title']
        sanitized_title = "".join(c for c in title if c.isalnum() or c.isspace() or c in ['_', '-'])
        video_id = video['id']
        link = f"https://www.youtube.com/watch?v={video_id}"
        thumbnail_file = f'{sanitized_title}'
        download_path = os.path.join(local_dir_path, f'{sanitized_title}.%(ext)s')
        ydl_opts = {
        'format': 'mp3/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'outtmpl' : download_path,
        'writethumbnail': True,  
            'postprocessor_args': [
                '-y',
                '-vf', 'fps=1,scale=320:240',
            ],
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download(link)
        except yt_dlp.utils.DownloadError as e:
            print(f"An error occurred: {str(e)}")

        if video is not None:
            print("Video downloaded successfully!")
        else:
            print("Failed to download the video.")
    return sanitized_title

   
@client.command(name='play', help="Use this command to play song/music. Example: ++play song name ||or|| ++play music name")
async def play(ctx, *, query=None):
    global song_name
    kick_cooldown = bot_data.data["kick_cooldown"]
    permissions_dict = bot_data.data["permissions_dict"]
    song_queue = bot_data.data["song_queue"]
    guild_queue = bot_data.data["guild_queue"]
    mute_Member_list = bot_data.data["mute_Member_list"]

    if not query:
        first_content = "You need to enter a song/music name..."
        first = discord.Embed(title="Enter A Song/Music Name", description=first_content, color=Color.random())
        await ctx.send(embed=first)
        return

    if ctx.guild.id not in guild_queue:
        guild_queue[ctx.guild.id] = []

    guild_queue[ctx.guild.id].append(query)
    song_queue.append(query)
    bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)

    if ctx.voice_client is not None: 
        second_content = f"Song/music {query} added to the song/music list and will be playing next."
        second = discord.Embed(title="Song/Music Added", description=second_content, color=Color.random())
        await ctx.send(embed=second)
    else:
        if ctx.author.voice and ctx.author.voice.channel:
            voice_channel = await ctx.author.voice.channel.connect()

            while guild_queue.get(ctx.guild.id, []):
                
                third_content = "Loading Song/Music :fast_forward:"
                third = discord.Embed(title="Loading...", description=third_content, color=Color.random())
                loading_message = await ctx.send(embed=third)
                animation_list = ['Loading Song/Music', 'Loading Song/Music :fast_forward:', 'Loading Song/Music', 'Loading Song/Music :fast_forward:', 'Loading Song/Music', 'Loading Song/Music :fast_forward:', 'Loading Song/Music', 'Loading Song/Music :fast_forward:', 'Loading Song/Music', 'Loading Song/Music :fast_forward:', 'Loading Song/Music', 'Loading Song/Music :fast_forward:']
                
                for i in animation_list:
                    await asyncio.sleep(0.4)
                    await loading_message.edit(embed=discord.Embed(title="Loading...", description=i, color=Color.random()))
                        
                song_name = await search_youtube_videos(guild_queue[ctx.guild.id][0])
                
                fourth_content = f'{query.upper()} added to the song/music list.'
                fourth = discord.Embed(title="Song/Music Added", description=fourth_content, color=Color.random())
                await ctx.send(embed=fourth)
                image = pathlib.Path(f'./{local_dir_path}/{song_name}.webp')
                await ctx.send(file=discord.File(image))
                
                if not os.path.exists(local_dir_path):
                    os.makedirs(local_dir_path)

                audio_path = pathlib.Path(local_dir_path) / f'{song_name}.mp3'

                while not voice_channel.is_connected():
                    await asyncio.sleep(1)
                    
                    
                def after_playing(error):
                    if error:
                        print(f"Error while playing audio: {error}")
                    try:
                        os.remove(audio_path)
                        os.remove(image)
                        print(f"Deleted {audio_path} and {image}")
                    except FileNotFoundError:
                        print("Files not found.")
                        

                voice_channel.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=audio_path),
                                after=after_playing)
                await status(ctx)
                
                await loading_message.delete()
                
                while voice_channel.is_playing():
                    await asyncio.sleep(5)
                    
                if guild_queue and song_queue:
                    del guild_queue[ctx.guild.id]
                    song_queue.pop(0)
                    bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)
                
            fifth_content = "Song/music is empty. Use 'song_list' to add more song(s)/music(s)."
            fifth = discord.Embed(title="Empty Song/Music List", description=fifth_content, color=Color.random())
            await ctx.send(embed=fifth)


            while voice_channel.is_playing():
                    await asyncio.sleep(1)
                    
            await voice_channel.disconnect()
        else:
            sixth_content = "You need to be in a voice channel to use this command."
            sixth = discord.Embed(title="Join A Voice Channel", description=sixth_content, color=Color.random())
            await ctx.send(embed=sixth)


async def status(ctx):
    guild_queue = bot_data.data["guild_queue"]
    guild_id = ctx.guild.id
    if guild_id in guild_queue and guild_queue[guild_id]:
        first_content = f"Now playing: {guild_queue[guild_id][0]}"
        first = discord.Embed(title="Current Song/Music", description=first_content, color=Color.random())
        await ctx.send(embed=first) 
    else:
        second_content = "No song/music is currently playing."
        second = discord.Embed(title="Zero Bots In Voice Channel", description=second_content, color=Color.random())
        await ctx.send(embed=second)  

@client.command(name="current_playing", help="Use this command to know the current song name. Example: ++current_playing")
async def current_playing(ctx):
    await status(ctx)
    
    
@client.command(name="disconnect", help="Use this command to disconnect the bot from voice channel. Example: ++disconnect")
async def disconnect(ctx):
    kick_cooldown = bot_data.data["kick_cooldown"]
    permissions_dict = bot_data.data["permissions_dict"]
    song_queue = bot_data.data["song_queue"]
    guild_queue = bot_data.data["guild_queue"]
    mute_Member_list = bot_data.data["mute_Member_list"]
    
    guild_id = ctx.guild.id
    voice_channel = ctx.voice_client

    if voice_channel:
        await voice_channel.disconnect()
        if guild_id in guild_queue:
            del guild_queue[ctx.guild.id]
            song_queue.clear()
            bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)
        first_content = 'Left the voice channel.'
        first = discord.Embed(title="Bot Disconnected From Voice Channel", description=first_content, color=Color.random())
        await ctx.send(embed=first)
        
        try:
            shutil.rmtree('discord_songs')
            print(f"Deleted!!")
        except FileNotFoundError:
            print("File not found.")
            
    else:
        second_content = 'No Bot is in a voice channel.'
        second = discord.Embed(title="Zero Bots In Voice Channel", description=second_content, color=Color.random())
        await ctx.send(embed=second)
    

@client.command(name='add_song', help="Use this command to add songs while playing a song. Also, by adding songs, you don't need to use the play command every time. Example: ++add_song song name")
async def add_song(ctx, *args):
    kick_cooldown = bot_data.data["kick_cooldown"]
    permissions_dict = bot_data.data["permissions_dict"]
    song_queue = bot_data.data["song_queue"]
    guild_queue = bot_data.data["guild_queue"]
    mute_Member_list = bot_data.data["mute_Member_list"]
    
    voice_channel = ctx.voice_client
    if voice_channel and voice_channel.is_playing():
        song_names = ' '.join(args)
        if ctx.guild.id not in guild_queue:
            guild_queue[ctx.guild.id] = []

        guild_queue[ctx.guild.id].append(song_names)
        bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)
        first_content = f'Songs added to the queue: {song_names}'
        first = discord.Embed(title="Song/Music Added", description=first_content, color=Color.random())
        await ctx.send(embed=first)
    else:
        second_content = 'You need to play a song/music first to add more songs...'
        second = discord.Embed(title="Play Your Song/Music First", description=second_content, color=Color.random())
        await ctx.send(embed=second)
        
    
@client.command(name="song_list", help="Use this command to see the playlist that you are playing. Example: ++song_list")
async def song_list(ctx):
    guild_queue = bot_data.data["guild_queue"]
    
    guild_id = ctx.guild.id
    if guild_id in guild_queue:
        first_content = f'This is your current song(s)/music(s) list: \n{guild_queue[guild_id]}'
        first = discord.Embed(title="Song/Music List", description=first_content, color=Color.random())
        await ctx.send(embed=first)
    else:
        second_content = 'The song/music list is empty.'
        second = discord.Embed(title="Empty Song/Music List", description=second_content, color=Color.random())
        await ctx.send(embed=second)
        

@client.command(name='skip', help="Use this command to skip the current song. Example: ++skip")
async def skip(ctx):
    global song_name
    kick_cooldown = bot_data.data["kick_cooldown"]
    permissions_dict = bot_data.data["permissions_dict"]
    song_queue = bot_data.data["song_queue"]
    guild_queue = bot_data.data["guild_queue"]
    mute_Member_list = bot_data.data["mute_Member_list"]
    
    voice_channel = ctx.voice_client
    if voice_channel and voice_channel.is_playing():
        
        voice_channel.stop()
        await asyncio.sleep(1)
        
        try:
            shutil.rmtree('discord_songs')
            print(f"Deleted!!")
        except FileNotFoundError:
            print("File not found.")
            
        first_content = 'Skipping the current song/music.'
        first = discord.Embed(title="Skipping Song/Music", description=first_content, color=Color.random())
        await ctx.send(embed=first)
        if ctx.guild.id in guild_queue and guild_queue[ctx.guild.id]:
            song_queue.clear()
            del guild_queue[ctx.guild.id]
            bot_data.update_and_save_data(kick_cooldown, permissions_dict, song_queue, guild_queue, mute_Member_list)
    else:
        second_content = 'The song list is empty. There is nothing to skip.'
        second = discord.Embed(title="NoneType Can't Execute This Function", description=second_content, color=Color.random())
        await ctx.send(embed=second)

'''
@client.command(name='pause')
async def pause(ctx):
    voice_channel = ctx.voice_client
    if voice_channel and voice_channel.is_playing():
        voice_channel.pause()
        await ctx.send('Song paused.')
                                        ##--TEMPORARY ABANDONED TWO FUNCTIONS--##
@client.command(name='resume')
async def resume(ctx):
    voice_channel = ctx.voice_client
    if voice_channel.is_paused():
        voice_channel.resume()
        await ctx.send('Resuming the song.')
'''


load_dotenv()
my_secret = os.getenv("my_secret")

if __name__ == "__main__":
    client.run(my_secret)