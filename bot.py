import discord
import sqlite3
from discord.ext import commands
from youtube_dl import YoutubeDL
import random
import asyncio
from discord.utils import get

token = open("token.txt").read()
bot = commands.Bot(command_prefix="p!")
con = sqlite3.connect("economy.db")
cur = con.cursor()


EXP_DELTA_FOR_LEVEL = 100
EXP_GAIN_PER_COMMAND = 5
WORK_MIN_GAIN = 50
WORK_MAX_GAIN = 100
translate = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15}
data = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"]
FFMPEG_PATH = r"G:\tiom4eg\.py\ffmpeg-n4.3.2-163-g6c414cf8f7-win64-lgpl-4.3\bin\ffmpeg.exe"

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
MM_HANDLER = {}
TTT_HANDLER = {}
server_channel = {}
channel_queue = {}


"""EVENTS"""


@bot.event
async def on_ready():
    print("Ready!")


@bot.event
async def on_connect():
    print(f"Connected to Discord as {bot.user.name}!")

"""ECONOMY COMMANDS"""


@bot.command()
async def balance(ctx):
    await preAction(ctx)
    uid = ctx.author.id
    onhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    bank = cur.execute(f"""SELECT bankBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    await ctx.send(f"Your on-hand balance: {onhand[0]} coins")
    await ctx.send(f"Your bank balance: {bank[0]} coins")


@commands.cooldown(1, 600)
@bot.command()
async def work(ctx):
    await preAction(ctx)
    uid = ctx.author.id
    onhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    gain = random.randint(WORK_MIN_GAIN, WORK_MAX_GAIN)
    cur.execute(f"""UPDATE Balance SET onhandBalance={onhand[0] + gain} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
    con.commit()
    await ctx.send(f"You've earned {gain} coins for your work!")


@bot.command()
async def deposit(ctx, depositValue: int):
    await preAction(ctx)
    if depositValue < 1:
        await ctx.send("Deposit value must be greater than 0!")
        return
    uid = ctx.author.id
    onhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    if onhand[0] < depositValue:
        await ctx.send("You haven't got enough coins!")
        return
    bank = cur.execute(f"""SELECT bankBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    cur.execute(f"""UPDATE Balance SET onhandBalance={onhand[0] - depositValue} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
    cur.execute(f"""UPDATE Balance SET bankBalance={bank[0] + depositValue} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
    con.commit()
    await ctx.send(f"Deposited {depositValue} coins to your bank!")


@bot.command()
async def withdraw(ctx, withdrawValue: int):
    await preAction(ctx)
    if withdrawValue < 1:
        await ctx.send("Withdraw value must be greater than 0!")
        return
    uid = ctx.author.id
    bank = cur.execute(f"""SELECT bankBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    if bank[0] < withdrawValue:
        await ctx.send("You haven't got enough coins!")
        return
    onhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    cur.execute(f"""UPDATE Balance SET bankBalance={bank[0] - withdrawValue} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
    cur.execute(f"""UPDATE Balance SET onhandBalance={onhand[0] + withdrawValue} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
    con.commit()
    await ctx.send(f"Withdrew {withdrawValue} coins from your bank!")


@commands.cooldown(1, 7200)
@bot.command()
async def rob(ctx, user: discord.User):
    await preAction(ctx)
    ruid = ctx.author.id
    if random.randint(1, 10) >= 4:
        ctx.send("You were caught on robbery!")
        return
    vuid = user.id
    if ruid == vuid:
        await ctx.send("You can't rob yourself, silly boy!")
        return
    vonhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={ruid})""").fetchone()
    if not vonhand:
        addUser(vuid)
        await ctx.send("You can't rob this user, because it haven't got coins!")
        return
    if vonhand[0] == 0:
        await ctx.send("You can't rob this user, because it haven't got coins!")
        return
    robbed = random.randint(1, vonhand[0])
    ronhand = cur.execute(
    f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={ruid})""").fetchone()
    cur.execute(f"""UPDATE Balance SET onhandBalance={ronhand[0] + robbed} WHERE id=(SELECT id FROM Users WHERE userID={ruid})""")
    cur.execute(
    f"""UPDATE Balance SET onhandBalance={vonhand[0] - robbed} WHERE id=(SELECT id FROM Users WHERE userID={vuid})""")
    con.commit()
    await ctx.send(f"You successfully robbed {robbed} coins from {user.name}!")


@bot.command()
async def transfer(ctx, user: discord.User, transferValue: int):
    await preAction(ctx)
    suid = ctx.author.id
    ruid = user.id
    if transferValue < 0:
        ctx.send("Transfer value must be greater than 0!")
        return
    sonhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={suid})""").fetchone()
    ronhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={ruid})""").fetchone()
    if not ronhand:
        addUser(ruid)
    if transferValue > sonhand[0]:
        await ctx.send("You haven't got enough coins!")
        return
    cur.execute(
        f"""UPDATE Balance SET onhandBalance={sonhand[0] - transferValue} WHERE id=(SELECT id FROM Users WHERE userID={suid})""")
    cur.execute(
        f"""UPDATE Balance SET onhandBalance={ronhand[0] + transferValue} WHERE id=(SELECT id FROM Users WHERE userID={ruid})""")
    con.commit()
    await ctx.send(f"You transfered {transferValue} coins to {user.mention} balance.")

"""GET INFO ABOUT USER"""


@bot.command()
async def info(ctx):
    await preAction(ctx)
    uid = ctx.author.id
    uexp = cur.execute(f"""SELECT userExp from Users WHERE userID={uid}""").fetchone()
    ulvl = cur.execute(f"""SELECT userLevel from Users WHERE userID={uid}""").fetchone()
    await ctx.send(f"Your level: {ulvl[0]}")
    await ctx.send(f"Your current experience: {uexp[0]}/{ulvl[0] * 100}")


@bot.command()
async def reset(ctx):
    await preAction(ctx)
    uid = ctx.author.id
    cur.execute(f"""UPDATE Balance SET onhandBalance=0 WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
    cur.execute(f"""UPDATE Balance SET bankBalance=0 WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
    cur.execute(f"""UPDATE Users SET userExp=0 WHERE userID={uid}""")
    cur.execute(f"""UPDATE Users SET userLevel=1 WHERE userID={uid}""")
    con.commit()
    await ctx.send("Your account was resetted!")

"""ADMINISTRATION COMMANDS"""


@bot.command()
@commands.has_permissions(ban_members=True)
@commands.cooldown(1, 60)
async def ban(ctx, member: discord.Member, reason="You got banned lol"):
    await ctx.guild.ban(member, reason=reason)
    await ctx.send(f"{member} was banned. Reason: {reason}.")


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member):
    await ctx.guild.kick(member)
    await ctx.send(f"{member} was kicked from guild.")


@bot.command(pass_context=True)
@commands.has_permissions(manage_messages=True)
async def purge(ctx, limit: int):
    await ctx.channel.purge(limit=limit + 1)
    await ctx.send(f'Cleared {limit} messages by {ctx.author.mention}.')
    await ctx.message.delete()

"""MISCELLANEOUS"""


@bot.command()
async def play(ctx, track: str):
    user = ctx.message.author
    if user.voice:  # check if user in ANY voice channel
        if not server_channel.get(ctx.guild, 0):  # if this guild hasn't vc with bot
            server_channel[ctx.guild] = user.voice.channel.id  # set this VoiceChannel as guild's vc
            # getting url with youtube_dl
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(track, download=False)
            url = info['formats'][0]['url']
            channel_queue[user.voice.channel.id] = [(url, track)]
            # let music make you lose control!
            vc = await user.voice.channel.connect()
            while channel_queue[user.voice.channel.id]:
                # executable takes path to ffmpeg.exe as argument
                vc.play(discord.FFmpegPCMAudio(executable=FFMPEG_PATH, source=channel_queue[user.voice.channel.id][0][0]))
                while vc.is_playing():
                    await asyncio.sleep(3)
                channel_queue[user.voice.channel.id].pop(0)
            # bye-bye!
            del server_channel[ctx.guild]
            del channel_queue[user.voice.channel.id]
            await ctx.send("Thank you for listening!")
            await vc.disconnect()
        else:  # otherwise, check if this user joined to vc our bot in
            if user.voice.channel.id != server_channel[ctx.guild]:
                await ctx.send("You're not allowed to use bot commands, if you're not joined voice channel with bot.")
            else:  # everything is all right, let's add to queue
                # getting url...
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(track, download=False)
                url = info['formats'][0]['url']
                channel_queue[user.voice.channel.id].append((url, track))
    else:  # if not, he is not allowed to use .play()
        await ctx.send("You're not in voice channel on this server.")


@bot.command()
async def queue(ctx):
    if server_channel.get(ctx.guild, 0):
        await ctx.send("\n".join(map(lambda x: f"{x[0]}. {x[1][1]}", enumerate(channel_queue[server_channel[ctx.guild]], 1))))


@bot.command()
async def leave(ctx):
    if server_channel.get(ctx.guild, 0):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected():
            await ctx.send("Thank you for listening!")
            await voice_client.disconnect()


@bot.command()
async def mm_start(ctx, number="4"):
    if MM_HANDLER.get(ctx.author.id, 0):
        await ctx.send("You already started the game!")
    else:
        number = int(number)
        if gstart(number):
            MM_HANDLER[ctx.author.id] = gstart(number)
            await ctx.send("OK, I came up with a number. Can you guess it?")
        else:
            await ctx.send("Hey, you typed wrong value. Try again.")


@bot.command()
async def mm_guess(ctx, guess):
    if MM_HANDLER.get(ctx.author.id, 0):
        result = gresult(guess, MM_HANDLER[ctx.author.id])
        if not result:
            await ctx.send("You guessed the number!!!")
            del MM_HANDLER[ctx.author.id]
        else:
            await ctx.send(f"{result[0]} cows and {result[1]} bulls.")
    else:
        await ctx.send("Hey, pal, you forgot to start game. Try again?")


@bot.command()
async def ttt_start(ctx):
    if TTT_HANDLER.get(ctx.message.channel.id, 0):
        if len(TTT_HANDLER[ctx.message.channel.id][0]) == 2:
            await ctx.send("There is a game in this channel right now! Please, wait.")
        else:
            TTT_HANDLER[ctx.message.channel.id][0].append(ctx.author.id)
            TTT_HANDLER[ctx.message.channel.id][1] = ttt_create()
            TTT_HANDLER[ctx.message.channel.id][2] = 1
            await ctx.send(f"Game started! <@{TTT_HANDLER[ctx.message.channel.id][0][0]}>, make your turn!")
            await ttt_field(ctx, TTT_HANDLER[ctx.message.channel.id][1])
    else:
        TTT_HANDLER[ctx.message.channel.id] = [[ctx.author.id], None, None]
        await ctx.send("Added you to game! Please wait for another player to join!")


@bot.command()
async def ttt(ctx, x: int, y: int):
    if ctx.author.id == TTT_HANDLER[ctx.message.channel.id][0][TTT_HANDLER[ctx.message.channel.id][2] - 1]:
        if not TTT_HANDLER[ctx.message.channel.id][1][x][y]:
            TTT_HANDLER[ctx.message.channel.id][1][x][y] = TTT_HANDLER[ctx.message.channel.id][2]
            TTT_HANDLER[ctx.message.channel.id][2] = 1 if TTT_HANDLER[ctx.message.channel.id][2] == 2 else 2
            await ctx.send(
                f"<@{ctx.author.id}> successfully placed {'X' if TTT_HANDLER[ctx.message.channel.id][2] == 2 else 'O'} on ({x}, {y}).")
            await ttt_field(ctx, TTT_HANDLER[ctx.message.channel.id][1])
            status = ttt_check_endgame(TTT_HANDLER[ctx.message.channel.id][1])
            if status == 1:
                await ctx.send(f"<@{TTT_HANDLER[ctx.message.channel.id][0][0]}> won!!!")
                del TTT_HANDLER[ctx.message.channel.id]
            if status == 2:
                await ctx.send(f"<@{TTT_HANDLER[ctx.message.channel.id][0][1]}> won!!!")
                del TTT_HANDLER[ctx.message.channel.id]
            if status == 3:
                await ctx.send("It's a draw!")
                del TTT_HANDLER[ctx.message.channel.id]
        elif TTT_HANDLER[ctx.message.channel.id][1][x][y]:
            await ctx.send(f"You can't place {'X' if not TTT_HANDLER[ctx.message.channel.id][2] else 'O'} there.")
    else:
        await ctx.send("It's not your turn!")

"""METHODS THAT CLOSED TO USER"""


def addUser(uid, onhandBalance=0):
    cur.execute(f"""INSERT INTO Users(userID, userExp, userLevel) VALUES({uid}, 0, 1)""")
    cur.execute(f"""INSERT INTO Balance(onhandBalance, bankBalance) VALUES({onhandBalance}, 0)""")
    con.commit()


async def preAction(ctx):
    uid = ctx.author.id
    if not cur.execute(f"""SELECT id FROM Users WHERE userID={uid}""").fetchone():
        addUser(uid)
    uexp = cur.execute(f"""SELECT userExp from Users WHERE userID={uid}""").fetchone()
    ulvl = cur.execute(f"""SELECT userLevel from Users WHERE userID={uid}""").fetchone()
    rulvl = ulvl[0]
    ruexp = uexp[0] + EXP_GAIN_PER_COMMAND
    if ruexp >= EXP_DELTA_FOR_LEVEL * ulvl[0]:
        await ctx.send(f"{ctx.author.mention} reached level {ulvl[0] + 1}!")
        rulvl += 1
        ruexp %= EXP_DELTA_FOR_LEVEL * ulvl[0]
    cur.execute(f"""UPDATE Users SET userExp={ruexp} WHERE userID={uid}""")
    cur.execute(f"""UPDATE Users SET userLevel={rulvl} WHERE userID={uid}""")
    con.commit()


def ttt_create():
    return [[0, 0, 0], [0, 0, 0], [0, 0, 0]]


def ttt_check_endgame(field):
    if (field[0]) == [1, 1, 1] or (field[1]) == [1, 1, 1] or (field[2]) == [1, 1, 1] or (field[0][0], field[1][0], field[2][0]) == [1, 1, 1] or (field[0][1], field[1][1], field[2][1]) == [1, 1, 1] or (field[0][2], field[1][2], field[2][2]) == [1, 1, 1] or (field[0][0], field[1][1], field[2][2]) == [1, 1, 1] or (field[0][2], field[1][1], field[2][0]) == [1, 1, 1]:
        return 1
    elif (field[0]) == [2, 2, 2] or (field[1]) == [2, 2, 2] or (field[2]) == [2, 2, 2] or (field[0][0], field[1][0], field[2][0]) == [2, 2, 2] or (field[0][1], field[1][1], field[2][1]) == [2, 2, 2] or (field[0][2], field[1][2], field[2][2]) == [2, 2, 2] or (field[0][0], field[1][1], field[2][2]) == [2, 2, 2] or (field[0][2], field[1][1], field[2][0]) == [2, 2, 2]:
        return 2
    elif not field[0].count(0) and not not field[1].count(0) and not not field[2].count(0):
        return 3
    else:
        return 0


def gstart(n):
    if n > 16 or n < 4:
        return 0
    else:
        starter = data
        src = ""
        for i in range(n):
            elem = random.choice(starter)
            del starter[starter.index(elem)]
            src += elem
        return src


def gresult(numb: str, source):
    c, b = 0, 0
    for i in range(len(numb)):
        if numb[i] == source[i]:
            b += 1
        elif numb[i] in source:
            c += 1
    if b != len(source):
        return (c, b)
    else:
        return 0


async def ttt_field(ctx, field):
    result = ""
    for row in field:
        for element in row:
            if element == 0:
                result += ":black_large_square:"
            if element == 1:
                result += ":x:"
            if element == 2:
                result += ":o:"
        result += "\n"
    await ctx.send(result)


bot.run(token)
