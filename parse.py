import os
from datetime import datetime
from itertools import chain
from operator import add

from dotenv import load_dotenv
from riotwatcher import ValWatcher

PATH = os.path.dirname(__file__)
load_dotenv(os.path.join(PATH, r"Secrets\.env"))
SECRETS = os.environ
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
response = ValWatcher(SECRETS["API_KEY"]).content.contents("na")
for agent in response["characters"]:
    agent_converter.update({agent["id"].lower(): agent["name"]})
for m in response["maps"]:
    if m["name"] != "Null UI Data!":
        map_converter.update({m["assetPath"]: m["name"]})

locationVars = {
    "Ascent": {"X": [0.00007, 0.423895], "Y": [-0.00007, 0.183242]},
    "Bind": {"X": [0.000059, 0.034554], "Y": [-0.000059, 0.422058]},
    "Breeze": {"X": [0.00007, 0.165123], "Y": [-0.00007, 0.533078]},
    "Haven": {"X": [0.000075, 0.35945], "Y": [-0.000075, -0.093272]},
    "Icebox": {"X": [0.000072, 0.700214], "Y": [-0.000072, 0.539687]},
    "Split": {"X": [0.000078, 0.302108], "Y": [-0.000078, 0.158073]}
}


def puuid_filter(players, puuid):
    for player in players:
        if player["puuid"] == puuid:
            return player

def get_rank(match_data, puuid):
    for player in match_data["players"]:
            if player["puuid"] == puuid:
                rank = rank_converter[player["competitiveTier"]]

    return rank
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
        out.append(sorted_ids.index(puuid)+1)

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
        try:
            stat.pop("receiver")
        except KeyError:
            pass
        stats = list(map(add, stats, stat.values()))  # total the stats

    return stats


def get_death_locations(match_data_list, puuid=""):
    out = []
    team_options = ["Red", "Blue"]

    for match in match_data_list:
        teams = {}
        for player in match["players"]:
            teams[player["puuid"]] = player["teamId"]
        player_stats = chain.from_iterable(map(lambda x: x["playerStats"], match["roundResults"]))
        kills = map(lambda x: x["kills"], player_stats)
        team_list  = []
        final_kills = []
        for i, round_kills in enumerate(kills):
            for kill in round_kills:
                if puuid:
                    if kill["victim"] == puuid:
                        final_kills.append(kill)
                        team_index = team_options.index(teams[kill["victim"]])
                        team_list.append(team_options[team_index-int(i>=13)])
                else:
                    final_kills.append(kill)
                    team_index = team_options.index(teams[kill["victim"]])
                    team_list.append(team_options[team_index-int(i>=13)])
        locations = map(lambda x: x["victimLocation"], final_kills)
        
        out.append(list(zip(locations, team_list)))

    return list(chain.from_iterable(out))


def convert_location(locations, game_map):
    def formula(loc):
        xvars = locationVars[game_map]["X"]
        yvars = locationVars[game_map]["Y"]
        return (loc["x"] * xvars[0] + xvars[1]), 1 - (loc["y"] * yvars[0] + yvars[1])

    return list(map(lambda x: (x[0] * 1024, x[1] * 1024), map(formula, locations)))


def agent_stats(player_data_list):
    return list(map(lambda x: agent_converter[x["characterId"]], player_data_list))


def rank_stats(match_data_list, puuid):
    dates = []
    ranks = []
    for match in match_data_list:
        start_time = datetime.fromtimestamp(match["matchInfo"]["gameStartMillis"] / 1000)
        ranks.append(puuid_filter(match["players"], puuid)["competitiveTier"])
        dates.append(start_time.strftime("%b %d"))

    return ranks, dates  # tier and date of getting said tier


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
    return list(filter(lambda x: x["matchInfo"]["queueId"] in ["competitive", "unrated"], match_data_list))


def map_filter(match_data_list, game_map):
    return list(filter(lambda x: map_converter[x["matchInfo"]["mapId"]] == game_map, match_data_list))

pass
