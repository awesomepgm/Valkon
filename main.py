import copy
import os
import queue
from collections import Counter
from itertools import groupby
from threading import Thread

import discord
import riotwatcher as rw
from discord.ext import commands
from dotenv import load_dotenv

import parse
import visuals

PATH = os.path.dirname(__file__)
load_dotenv(os.path.join(PATH, r"Secrets\.env"))
SECRETS = os.environ

bot = commands.Bot(command_prefix='.', description='A Valorant stat bot.')
acctwatcher = rw.RiotWatcher(SECRETS["API_KEY"])
watcher = rw.ValWatcher(SECRETS["API_KEY"])
bot.remove_command('help')


data_cache = {}
# makes a cache of usernames to matchdata to improve speed and api usage, this is deleted every 24 hrs
# to protect privacy format: {name: [puuid, matchlistDTO, matchDTO]}

client = discord.Client()

def perform_web_requests(matches, no_workers):
    class Worker(Thread):
        def __init__(self, request_queue):
            Thread.__init__(self)
            self.queue = request_queue
            self.results = []

        def run(self):
            while True:
                content = self.queue.get()
                if content == "":
                    break
                response = watcher.match.by_id("NA", content["matchId"])
                self.results.append(response)
                self.queue.task_done()

    # Create queue and add addresses
    q = queue.Queue()
    for url in matches:
        q.put(url)

    # Create workers and add tot the queue
    workers = []
    for _ in range(no_workers):
        worker = Worker(q)
        worker.start()
        workers.append(worker)
    # Workers keep working till they receive an empty string
    for _ in workers:
        q.put("")
    # Join workers to wait till they finished
    for worker in workers:
        worker.join()

    # Combine results from all workers
    r = []
    for worker in workers:
        r.extend(worker.results)
    return r

def get_match_data(name, match_count=30):
    global data_cache

    username, tagline = name.split("#")
    if name not in data_cache.keys():
        puuid = acctwatcher.account.by_riot_id("AMERICAS", username, tagline)["puuid"]
        data_cache[name] = [puuid, 0, 0]  # this also handles the exception when the person does not have a cache yet
    else:
        puuid = data_cache[name][0]

    matches = watcher.match.matchlist_by_puuid("NA", puuid)["history"]
    if matches == data_cache[name][1]:
        results = data_cache[name][2]
    else:
        cut_matches = matches[:match_count]
        results = perform_web_requests(cut_matches, 5)


    data_cache[name][1] = matches
    data_cache[name][2] = results

    return results, puuid


@bot.event
async def on_ready():
    print("Ready")


@bot.command(name="rank")
async def check_rank(ctx, name):
    """.rank [name#tag]:Shows your current competitive rank"""

    match_data, puuid = get_match_data(name)
    ranked_match_data = parse.ranked_filter(match_data)
    rank = parse.get_rank(ranked_match_data[0], puuid)

    visuals.draw_rank(rank)
    await ctx.send(file=discord.File(r"C:\Users\parsa\Desktop\Code\Python\Discord\Valkon\Assets\cache.png"))


@bot.command(name="overview")
async def check_overview(ctx, name):
    """.overview [name#tag]:Shows your complete overview"""

    match_data, puuid = get_match_data(name)
    normal_match_data = parse.normal_filter(match_data)  # filters out special gamemodes (ex: spike rush, deathmatch)
    ranked_match_data = parse.ranked_filter(match_data)
    rank = parse.get_rank(ranked_match_data[0], puuid)
    player_data = copy.deepcopy(parse.get_player_data(normal_match_data, puuid))
    score, rounds, kills, deaths, _, _, abilities = parse.split_stats(player_data)
    leaderboard = parse.get_leaderboard(normal_match_data, puuid)
    round_stats = parse.get_round_stats(normal_match_data, puuid)
    _, legshot, bodyshot, headshot = parse.get_damage(round_stats)

    avg_leaderboard = sum(leaderboard) / len(leaderboard)
    abilitiespr = abilities/rounds
    acs = score / rounds
    kdr = kills / deaths
    kpr = kills / rounds
    hsp = (headshot / (legshot + bodyshot + headshot)) * 100

    final_stats = {"Frag": avg_leaderboard, "ACS": acs, "KD": kdr, "KR": kpr, "Ability": abilitiespr, "Rank": rank, "HS%": hsp}

    visuals.draw_overview(final_stats)
    await ctx.send(file=discord.File(r"C:\Users\parsa\Desktop\Code\Python\Discord\Valkon\Assets\cache.png"))


@bot.command(name="deathmap", aliases=["dm", ])
async def death_map(ctx, name, game_map, f=True):
    """.deathmap [name#tag] [map] [optional f]:Shows your agent pickrates"""

    match_data, puuid = get_match_data(name)
    normal_match_data = parse.normal_filter(match_data)
    map_filtered = parse.map_filter(normal_match_data, game_map)
    puuid = puuid * f
    loc_data = parse.get_death_locations(map_filtered, puuid)
    locations, teams = list(zip(*loc_data))
    locations = parse.convert_location(locations, game_map)
    visuals.draw_locmap(locations, teams, game_map)

    await ctx.send(file=discord.File(r"C:\Users\parsa\Desktop\Code\Python\Discord\Valkon\Assets\cache.png"))


@bot.command(name="pickrate")
async def agent_pickrate(ctx, name):
    """.pickrate [name#tag]:Shows your agent pickrates"""

    match_data, puuid = get_match_data(name)
    normal_match_data = parse.normal_filter(match_data)  # filters out special gamemodes (ex: spike rush, deathmatch)
    player_data = parse.get_player_data(normal_match_data, puuid)
    agent_stats = parse.agent_stats(player_data)

    final_data = Counter(agent_stats)
    total = len(agent_stats)
    for agent, picks in final_data.items():
        final_data[agent] = picks / total * 100
    final_data = sorted(final_data.items(), key=lambda x: x[1], reverse=True)

    visuals.draw_pickrate(dict(final_data))
    await ctx.send(file=discord.File(r"C:\Users\parsa\Desktop\Code\Python\Discord\Valkon\Assets\cache.png"))


@bot.command(name="rankgraph", aliases=["rg", ])
async def graph_rank(ctx, name):
    """.rankgraph [name#tag]:Shows you a graph of your competitive rank history"""

    match_data, puuid = get_match_data(name, 50)
    ranked_match_data = parse.ranked_filter(match_data)
    rank_stats = parse.rank_stats(ranked_match_data, puuid)
    res = [i[0] for i in groupby(rank_stats)]  # remove consecutive dupes

    visuals.draw_graph(res)
    await ctx.send(file=discord.File(r"C:\Users\parsa\Desktop\Code\Python\Discord\Valkon\Assets\cache.png"))


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

bot.run(SECRETS["DISCORD_TOKEN"])
