import json
import os
from itertools import chain
from datetime import datetime
from operator import add

import requests

PATH = os.path.dirname(__file__)
SECRETS = json.load(open(os.path.join(PATH, r"Secrets\secrets.json")))
rank_converter = {
    0: "Unrated",
    3: "Iron 1",
    4: "Iron 2",
    5: "Iron 3",
    6: "Bronze 1",
    7: "Bronze 2",
    8: "Bronze 3",
    9: "Silver 1",
    10: "Silver 2",
    11: "Silver 3",
    12: "Gold 1",
    13: "Gold 2",
    14: "Gold 3",
    15: "Plat 1",
    16: "Plat 2",
    17: "Plat 3",
    18: "Diamond 1",
    19: "Diamond 2",
    20: "Diamond 3",
    21: "Immortal",
    24: "Radiant"
}
contents_url = "https://na.api.riotgames.com/val/content/v1/contents"
agent_converter = {}
map_converter = {}
response = requests.get(contents_url).json()
for agent in response["characters"]:
    agent_converter.update({agent["id"]: agent["name"]})
for m in response["maps"]:
    map_converter.update({m["id"]: m["name"]})

locationVars = {
    "Ascent": {"X": [0.00007, 0.423895], "Y": [-0.00007, 0.183242]},
    "Bind": {"X": [0.000059, 0.034554], "Y": [-0.000059, 0.422058]},
    "Breeze": {"X": [0.00007, 0.165123], "Y": [-0.00007, 0.533078]},
    "Haven": {"X": [0.000075, 0.35945], "Y": [-0.000075, -0.093272]},
    "Icebox": {"X": [0.000072, 0.700214], "Y": [-0.000072, 0.539687]},
    "Split": {"X": [0.000078, 1.382108], "Y": [-0.000078, 0.158073]}
}

api_header = {"X-Riot-Token": SECRETS["api_key"]}


def puuid_filter(players, puuid):
    for player in players:
        if player["puuid"] == puuid:
            return player


def get_puuid(username, tagline):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{username}/{tagline}"
    r = requests.get(url, headers=api_header)

    return r.json()["puuid"]


def get_rank(match_id, puuid):
    url = f"https://na.api.riotgames.com/val/match/v1/matches/{match_id}"
    r = requests.get(url, headers=api_header)

    filtered_player = puuid_filter(r.json()["players"], puuid)
    return rank_converter[filtered_player["competitiveTier"]]


def get_matches(puuid):
    url = f"https://na.api.riotgames.com/val/match/v1/matchlists/by-puuid/{puuid}"
    r = requests.get(url, headers=api_header)

    return r.json()["history"]


def get_match_data(match_list, match_count=30):
    # takes a list of MatchlistEntryDto and turns them into MatchDto (here called match_data_list) which allows them
    # to be parsed
    out = []

    for match in match_list:
        if len(out) >= match_count:
            break
        match_id = match["matchId"]
        url = f"https://na.api.riotgames.com/val/match/v1/matches/{match_id}"
        r = requests.get(url, headers=api_header)
        out.append(r.json())

    return out


def get_player_data(match_data_list, puuid):
    out = []

    for match in match_data_list:
        filtered_player = puuid_filter(match["players"], puuid)
        out.append(filtered_player)

    return out


def get_leaderboard(match_data_list, puuid):
    out = []

    for match in match_data_list:
        scores = map(lambda x: x["stats"]["score"], match["players"])
        puuids = map(lambda x: x["puuid"], match["players"])
        cache = sorted(list(zip(scores, puuids)), reverse=True)

        sorted_ids = [x for _, x in cache]
        out.append(sorted_ids.index(puuid))

    return out


def get_round_stats(match_data_list, puuid):
    out = []

    for match in match_data_list:
        player_stats = chain.from_iterable(map(lambda x: x["playerStats"], match["roundResults"]))
        filtered_stats = puuid_filter(player_stats, puuid)
        out.append(filtered_stats)

    return out


def get_economy(player_round_stats):
    out = sum(map(lambda x: x["economy"]["spent"], player_round_stats))

    return out


def get_damage(player_round_stats):
    stat_list = chain.from_iterable(map(lambda x: x["damage"], player_round_stats))
    stats = [0, ] * 4  # in format [damage, legshot, bodyshot, headshot]

    for stat in stat_list:
        stat.pop("receiver")
        stats = list(map(add, stats, stat.values()))  # total the stats

    return stats


def get_death_locations(match_data_list, puuid=""):
    out = []
    teams = {}

    for match in match_data_list:
        teams = {}
        for player in match["players"]:
            teams[player["puuid"]] = player["teamId"]
        player_stats = chain.from_iterable(map(lambda x: x["playerStats"], match["roundResults"]))
        kills = chain.from_iterable(map(lambda x: x["kills"], player_stats))
        if bool(puuid):  # currently based on defense/ offense color, can be changed to ally/enemy color
            kills = filter(lambda p: p["killer"] == puuid or p["victim"] == puuid, kills)
        locations = map(lambda x: x["victimLocation"], kills)
        team_list = map(lambda x: teams[x["victim"]], kills)

        out.append(list(set(zip(locations, team_list))))

    return list(chain.from_iterable(out))


def convert_location(locations, gamemap):
    def formula(loc):
        xvars = locationVars[gamemap]["X"]
        yvars = locationVars[gamemap]["Y"]
        return loc[0] * xvars[0] + xvars[1], 7000 - loc[1] * yvars[0] + yvars[1]

    return list(map(lambda x: (x[0]/7000 * 1024, x[1]/7000 * 1024), map(formula, locations)))


def agent_stats(player_data_list):
    return list(map(lambda x: agent_converter[x["characterId"]], player_data_list))


def rank_stats(match_data_list, player_data_list):
    dates = []
    for match in match_data_list:
        start_time = datetime.fromtimestamp(match["matchInfo"]["gameStartMillis"] / 1000)
        dates.append(start_time.strftime("%b %d"))

    return list(map(lambda x: x["competitiveTier"], player_data_list)), dates  # tier and date of getting said tier


def split_stats(player_data_list):
    stat_list = [match["stats"] for match in player_data_list]
    stats = [0, ] * 7  # in format [score, rounds, kills, deaths, assists, playtime, abilities]

    for stat in stat_list:
        stat["abilityCasts"] = sum(stat["abilityCasts"].values())
        stats = list(map(add, stats, stat.values()))  # total the stats

    return stats


def ranked_filter(match_data_list):
    return list(filter(lambda x: x["matchInfo"]["isRanked"], match_data_list))


def normal_filter(match_data_list):
    return list(filter(lambda x: x["matchInfo"]["queueId"] in ["COMPETITIVE", "UNRATED"], match_data_list))


def map_filter(match_data_list, gamemap):
    return list(filter(lambda x: map_converter[x["matchInfo"]["mapId"]] == gamemap, match_data_list))
