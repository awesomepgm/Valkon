import json
import os
from itertools import groupby
from collections import Counter

import discord
from discord.ext import commands

import api
import visuals

bot = commands.Bot(command_prefix='.', description='A Valorant stat bot.')
bot.remove_command('help')
dir = os.path.dirname(__file__)
SECRETS = json.load(open(os.path.join(dir, r"Secrets\secrets.json")))
dataCache = {} #makes a cache of usernames to matchdata to improve speed and api usage, this is deleted every 24 hrs to protect privacy format: {name: [puuid, matchlistDTO, matchDTO]}

client = discord.Client()

def getMatchData(name, matchCount = 30):
    global dataCache
    
    gameName, tagLine = name.split("#")
    if name not in dataCache.keys:
        puuid = api.getPUUID(gameName, tagLine)
        dataCache[name] = [puuid,0,0] # this also handles the exception when the person does not have a cache yet
    else:
        puuid = dataCache[name][0]

    matches = api.getMatches(puuid)
    if matches == dataCache[name][1]:
        matchData = dataCache[name][2]
    else:
        matchData = api.getMatchData(matches, matchCount)
    
    dataCache[name][1] = matches
    dataCache[name][2] = matchData

    return [matchData, puuid]

@bot.event
async def on_ready():
    print("Ready")

@bot.command(name="rank")
async def checkRank(ctx, name):
    '''.rank [name#tag]:Shows your current competitive rank'''

    matchData, puuid = getMatchData(name)
    rankedMatchData = api.rankedFilter(matchData)
    rank = api.getRank(rankedMatchData[0]["matchInfo"]["matchId"], puuid)

    visuals.drawRank(rank)
    await ctx.send(rank)

@bot.command(name="overview")
async def checkOverview(ctx, name):
    '''.overview [name#tag]:Shows your complete overview'''

    matchData, puuid = getMatchData(name)
    normalMatchData = api.normalFilter(matchData) #filters out special gamemodes (ex: spike rush, deathmatch)
    rankedMatchData = api.rankedFilter(matchData)
    rank = api.getRank(rankedMatchData[0]["matchInfo"]["matchId"], puuid)
    playerData = api.getPlayerData(normalMatchData)
    score, rounds, kills, deaths, _, playtime, _ = api.splitStats(playerData, puuid)
    leaderboard = api.getLeaderboard(normalMatchData, puuid)
    roundStats = api.getRoundStats(normalMatchData, puuid)
    _, legshot, bodyshot, headshot = api.getDamage(roundStats)


    avgLeaderboard = sum(leaderboard) / len(leaderboard)
    acs = score / rounds
    hours = playtime / 3600000
    kdr = kills / deaths
    kpr = kills / rounds
    hsp = (headshot / (legshot+bodyshot+headshot))*100


    finalStats = {"Frag": avgLeaderboard, "ACS": acs, "KD": kdr, "KR": kpr, "Hours": hours, "Rank": rank, "HS%": hsp}

    visuals.drawOverview(finalStats)
    await ctx.send(finalStats)

@bot.command(name = "deathmap", aliases = ["dm",])
async def deathMap(ctx, name, gameMap, filter = False):
    '''.deathmap [name#tag] [map] [optional filter]:Shows your agent pickrates'''

    matchData, puuid = getMatchData(name)
    normalMatchData = api.normalFilter(matchData)
    mapFiltered = api.mapFilter(normalMatchData)
    puuid = puuid * filter
    locData = api.deathLocations(mapFiltered, puuid)
    locations, teams = list(zip(*locData))
    locations = api.convertLocation(locations, gameMap)
    visuals.drawLocmap(locations, teams, gameMap)

    return ctx.send(locData)


@bot.command(name="pickrate")
async def agentPickrate(ctx, name):
    '''.pickrate [name#tag]:Shows your agent pickrates'''

    matchData, puuid = getMatchData(name)
    normalMatchData = api.normalFilter(matchData) #filters out special gamemodes (ex: spike rush, deathmatch)
    playerData = api.getPlayerData(normalMatchData)
    agentStats = api.agentStats(playerData, puuid)

    finalData = Counter(agentStats)
    total = len(agentStats)
    for agent, picks in finalData.items():
        finalData[agent] = picks/total * 100
    finalData = sorted(finalData.items(), key=lambda x: x[1], reverse=True)
    
    visuals.drawPickrate(finalData)
    await ctx.send(finalData)

@bot.command(name="rank")
async def peakRank(ctx, name):
    '''.rank [name#tag]:Shows your current competitive rank'''

    matchData, puuid = getMatchData(name)
    rankedMatchData = api.rankedFilter(matchData)
    rankStats = api.rankStats(rankedMatchData[0]["matchInfo"]["matchId"], puuid)
    peak = sorted(rankStats)[-1]

    visuals.drawRank(peak)
    await ctx.send(peak)

@bot.command(name="rankgraph", aliases = ["rg",])
async def graphRank(ctx, name):
    '''.rankgraph [name#tag]:Shows you a graph of your competitive rank history'''

    matchData, puuid = getMatchData(name, 100)
    rankedMatchData = api.rankedFilter(matchData)
    rankStats = api.rankStats(rankedMatchData[0]["matchInfo"]["matchId"], puuid)
    res = [i[0] for i in groupby(rankStats)] #remove cons dupes
    
    
    visuals.drawGraph
    await ctx.send(res)

@bot.command()
async def help(ctx):
    '''.help:Sends you this help message'''

    embed=discord.Embed(title="Help", color=0x00ff00)
    embed.set_thumbnail(url="https://i.imgur.com/Tk7mSXl.png")
    for command in bot.commands:
        if command.callback.__doc__ != None:
            name,value = command.callback.__doc__.split(":")
            embed.add_field(name=name, value=value, inline=False)
    await ctx.send(embed=embed)

bot.run(SECRETS["discord_token"])