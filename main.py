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
PATH = os.path.dirname(__file__)
SECRETS = json.load(open(os.path.join(PATH, r"Secrets\secrets.json")))
data_cache = {}
# makes a cache of usernames to matchdata to improve speed and api usage, this is deleted every 24 hrs
# to protect privacy format: {name: [puuid, matchlistDTO, matchDTO]}

client = discord.Client()


def get_match_data(name, match_count=30):
    global data_cache

    username, tagline = name.split("#")
    if name not in data_cache.keys:
        puuid = api.get_puuid(username, tagline)
        data_cache[name] = [puuid, 0, 0]  # this also handles the exception when the person does not have a cache yet
    else:
        puuid = data_cache[name][0]

    matches = api.get_matches(puuid)
    if matches == data_cache[name][1]:
        match_data = data_cache[name][2]
    else:
        match_data = api.get_match_data(matches, match_count)

    data_cache[name][1] = matches
    data_cache[name][2] = match_data

    return [match_data, puuid]


@bot.event
async def on_ready():
    print("Ready")


@bot.command(name="rank")
async def check_rank(ctx, name):
    """.rank [name#tag]:Shows your current competitive rank"""

    match_data, puuid = get_match_data(name)
    ranked_match_data = api.ranked_filter(match_data)
    rank = api.get_rank(ranked_match_data[0]["matchInfo"]["matchId"], puuid)

    visuals.draw_rank(rank)
    await ctx.send(rank)


@bot.command(name="overview")
async def check_overview(ctx, name):
    """.overview [name#tag]:Shows your complete overview"""

    match_data, puuid = get_match_data(name)
    normal_match_data = api.normal_filter(match_data)  # filters out special gamemodes (ex: spike rush, deathmatch)
    ranked_match_data = api.ranked_filter(match_data)
    rank = api.get_rank(ranked_match_data[0]["matchInfo"]["matchId"], puuid)
    player_data = api.get_player_data(normal_match_data, puuid)
    score, rounds, kills, deaths, _, playtime, _ = api.split_stats(player_data)
    leaderboard = api.get_leaderboard(normal_match_data, puuid)
    round_stats = api.get_round_stats(normal_match_data, puuid)
    _, legshot, bodyshot, headshot = api.get_damage(round_stats)

    avg_leaderboard = sum(leaderboard) / len(leaderboard)
    acs = score / rounds
    hours = playtime / 3600000
    kdr = kills / deaths
    kpr = kills / rounds
    hsp = (headshot / (legshot + bodyshot + headshot)) * 100

    final_stats = {"Frag": avg_leaderboard, "ACS": acs, "KD": kdr, "KR": kpr, "Hours": hours, "Rank": rank, "HS%": hsp}

    visuals.draw_overview(final_stats)
    await ctx.send(final_stats)


@bot.command(name="deathmap", aliases=["dm", ])
async def death_map(ctx, name, game_map, f=False):
    """.deathmap [name#tag] [map] [optional f]:Shows your agent pickrates"""

    match_data, puuid = get_match_data(name)
    normal_match_data = api.normal_filter(match_data)
    map_filtered = api.map_filter(normal_match_data, game_map)
    puuid = puuid * f
    loc_data = api.get_death_locations(map_filtered, puuid)
    locations, teams = list(zip(*loc_data))
    locations = api.convert_location(locations, game_map)
    visuals.draw_locmap(locations, teams, game_map)

    return ctx.send(loc_data)


@bot.command(name="pickrate")
async def agent_pickrate(ctx, name):
    """.pickrate [name#tag]:Shows your agent pickrates"""

    match_data, puuid = get_match_data(name)
    normal_match_data = api.normal_filter(match_data)  # filters out special gamemodes (ex: spike rush, deathmatch)
    player_data = api.get_player_data(normal_match_data, puuid)
    agent_stats = api.agent_stats(player_data)

    final_data = Counter(agent_stats)
    total = len(agent_stats)
    for agent, picks in final_data.items():
        final_data[agent] = picks / total * 100
    final_data = sorted(final_data.items(), key=lambda x: x[1], reverse=True)

    visuals.draw_pickrate(dict(final_data))
    await ctx.send(final_data)


@bot.command(name="rank")
async def peak_rank(ctx, name):
    """.rank [name#tag]:Shows your current competitive rank"""

    match_data, puuid = get_match_data(name)
    ranked_match_data = api.ranked_filter(match_data)
    rank_stats = api.rank_stats(ranked_match_data[0]["matchInfo"]["matchId"], puuid)
    peak = sorted(rank_stats)[-1]

    visuals.draw_rank(peak)
    await ctx.send(peak)


@bot.command(name="rankgraph", aliases=["rg", ])
async def graph_rank(ctx, name):
    """.rankgraph [name#tag]:Shows you a graph of your competitive rank history"""

    match_data, puuid = get_match_data(name, 100)
    ranked_match_data = api.ranked_filter(match_data)
    rank_stats = api.rank_stats(ranked_match_data[0]["matchInfo"]["matchId"], puuid)
    res = [i[0] for i in groupby(rank_stats)]  # remove consecutive dupes

    visuals.draw_graph(res)
    await ctx.send(res)


@bot.command(name="help")
async def display_help(ctx):
    """.help:Sends you this help message"""

    embed = discord.Embed(title="Help", color=0x00ff00)
    embed.set_thumbnail(url="https://i.imgur.com/Tk7mSXl.png")
    for command in bot.commands:
        if command.callback.__doc__ is not None:
            name, value = command.callback.__doc__.split(":")
            embed.add_field(name=name, value=value, inline=False)
    await ctx.send(embed=embed)


bot.run(SECRETS["discord_token"])
