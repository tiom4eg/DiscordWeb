import discord
import sqlite3
from discord.ext import commands
import random
import time

bot = commands.Bot(command_prefix="p!")
con = sqlite3.connect("economy.db")
cur = con.cursor()

WORK_COOLDOWN = 600
ROB_COOLDOWN = 7200
WORK_MIN_GAIN = 50
WORK_MAX_GAIN = 100


@bot.event
async def on_ready():
    print("Ready!")


@bot.event
async def on_connect():
    print(f"Connected to Discord as {bot.user.name}!")


@bot.command()
async def balance(ctx):
    # if user in db, send him his balance; otherwise, add him to db and send 0
    uid = ctx.author.id
    onhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    bank = cur.execute(f"""SELECT bankBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    if not onhand:
        addUser(uid)
        await ctx.send(f"Your on-hand balance: 0")
        await ctx.send(f"Your bank balance: 0")
    else:
        await ctx.send(f"Your on-hand balance: {onhand[0]} coins")
        await ctx.send(f"Your bank balance: {bank[0]} coins")


@bot.command()
async def work(ctx):
    # check if user already in db
    uid = ctx.author.id
    onhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
    gain = random.randint(WORK_MIN_GAIN, WORK_MAX_GAIN)
    nowTime = int(time.time())
    # if not, add him to db
    if not onhand:
        addUser(uid, lastWorkTime=nowTime, onhandBalance=gain)
        await ctx.send(f"You've earned {gain} coins for your work!")
    # else, give 'em money and update lastWorkTime
    else:
        lastWorkTime = cur.execute(f"""SELECT lastWorkTime FROM Users WHERE userID={uid}""").fetchone()[0]
        if nowTime - lastWorkTime < WORK_COOLDOWN:
            await ctx.send(f"Please, wait {WORK_COOLDOWN - (nowTime - lastWorkTime)} seconds before using this command again!")
        else:
            cur.execute(f"""UPDATE Balance SET onhandBalance={onhand[0] + gain} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
            cur.execute(f"""UPDATE Users SET lastWorkTime={nowTime} WHERE userID={uid}""")
            con.commit()
            await ctx.send(f"You've earned {gain} coins for your work!")
    # commit


@bot.command()
async def deposit(ctx, depositValue: int):
    if depositValue < 1:
        await ctx.send("Deposit value must be greater than 0!")
    else:
        uid = ctx.author.id
        onhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
        if not onhand:
            addUser(uid)
            await ctx.send("You haven't got enough coins!")
        else:
            if onhand[0] < depositValue:
                await ctx.send("You haven't got enough coins!")
            else:
                bank = cur.execute(f"""SELECT bankBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
                cur.execute(f"""UPDATE Balance SET onhandBalance={onhand[0] - depositValue} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
                cur.execute(f"""UPDATE Balance SET bankBalance={bank[0] + depositValue} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
                con.commit()
                await ctx.send(f"Deposited {depositValue} coins to your bank!")


@bot.command()
async def withdraw(ctx, withdrawValue: int):
    if withdrawValue < 1:
        await ctx.send("Withdraw value must be greater than 0!")
    else:
        uid = ctx.author.id
        bank = cur.execute(f"""SELECT bankBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
        if not bank:
            addUser(uid)
            await ctx.send("You haven't got enough coins!")
        else:
            if bank[0] < withdrawValue:
                await ctx.send("You haven't got enough coins!")
            else:
                onhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={uid})""").fetchone()
                cur.execute(f"""UPDATE Balance SET bankBalance={bank[0] - withdrawValue} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
                cur.execute(f"""UPDATE Balance SET onhandBalance={onhand[0] + withdrawValue} WHERE id=(SELECT id FROM Users WHERE userID={uid})""")
                con.commit()
                await ctx.send(f"Withdrew {withdrawValue} coins from your bank!")


@bot.command()
async def rob(ctx, user: discord.User):
    ruid = ctx.author.id
    ronhand = cur.execute(
        f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={ruid})""").fetchone()
    nowTime = int(time.time())
    if random.randint(1, 10) < 4:
        if not ronhand:
            addUser(ruid)
        lastRobTime = cur.execute(f"""SELECT lastRobTime FROM Users WHERE userID={ruid}""").fetchone()[0]
        if nowTime - lastRobTime < ROB_COOLDOWN:
            await ctx.send(f"Please, wait {ROB_COOLDOWN - (nowTime - lastRobTime)} seconds before using this command again!")
        else:
            vuid = user.id
            vonhand = cur.execute(f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={ruid})""").fetchone()
            if not vonhand:
                addUser(vuid)
                await ctx.send("You can't rob this user, because it haven't got money!")
            else:
                if vonhand[0] == 0:
                    await ctx.send("You can't rob this user, because it haven't got money!")
                else:
                    robbed = random.randint(1, vonhand[0])
                    ronhand = cur.execute(
                    f"""SELECT onhandBalance FROM Balance WHERE id=(SELECT id FROM Users WHERE userID={ruid})""").fetchone()
                    cur.execute(f"""UPDATE Balance SET onhandBalance={ronhand[0] + robbed} WHERE id=(SELECT id FROM Users WHERE userID={ruid})""")
                    cur.execute(
                    f"""UPDATE Balance SET onhandBalance={vonhand[0] - robbed} WHERE id=(SELECT id FROM Users WHERE userID={vuid})""")
                    con.commit()
                    await ctx.send(f"You successfully robbed {robbed} coins from {user.name}!")


def addUser(uid, lastWorkTime=0, lastRobTime=0, onhandBalance=0):
    cur.execute(f"""INSERT INTO Users(userID, lastWorkTime, lastRobTime) VALUES({uid}, {lastWorkTime}, {lastRobTime})""")
    cur.execute(f"""INSERT INTO Balance(onhandBalance, bankBalance) VALUES({onhandBalance}, 0)""")
    con.commit()
