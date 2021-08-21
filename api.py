import json
import os
from itertools import chain
from datetime import datetime
from operator import add

import requests

dir = os.path.dirname(__file__)
SECRETS = json.load(open(os.path.join(dir, r"Secrets\secrets.json")))
rankConverter = {
    0 : "Unrated",
    3: "Iron 1",
    4 : "Iron 2",
    5 : "Iron 3",
    6 : "Bronze 1",
    7 : "Bronze 2",
    8 : "Bronze 3",
    9 : "Silver 1",
    10 : "Silver 2",
    11 : "Silver 3",
    12 : "Gold 1",
    13 : "Gold 2",
    14 : "Gold 3",
    15 : "Plat 1",
    16 : "Plat 2",
    17 : "Plat 3",
    18 : "Diamond 1",
    19 : "Diamond 2",
    20 : "Diamond 3",
    21 : "Immortal",
    24 : "Radiant"
}
contentsUrl = "https://na.api.riotgames.com/val/content/v1/contents"
agentConverter = {}
mapConverter = {}
response = requests.get(contentsUrl).json()
for agent in response["characters"]:
    agentConverter.update({agent["id"]:agent["name"]})
for m in response["maps"]:
    mapConverter.update({m["id"]:m["name"]})

locationVars = {
    "Ascent": {"X":[0.00007, 0.423895], "Y":[-0.00007, 0.183242]},
    "Bind": {"X":[0.000059, 0.034554], "Y":[-0.000059, 0.422058]},
    "Breeze": {"X":[0.00007, 0.165123], "Y":[-0.00007, 0.533078]},
    "Haven": {"X":[0.000075, 0.35945], "Y":[-0.000075, -0.093272]},
    "Icebox": {"X":[0.000072, 0.700214], "Y":[-0.000072, 0.539687]},
    "Split": {"X":[0.000078, 1.382108], "Y":[-0.000078, 0.158073]}
}


api_header = {"X-Riot-Token": SECRETS["api_key"]}

def getPUUID(gameName,tagLine):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    response = requests.get(url, headers = api_header)
    
    return response.json()["puuid"]

def getRank(matchId, puuid):
    puuidFilter = lambda p: p["puuid"]==puuid
    url = f"https://na.api.riotgames.com/val/match/v1/matches/{matchId}"
    response = requests.get(url, headers = api_header)

    filteredPlayer = list(filter(puuidFilter, response.json()["players"]))[0]
    return rankConverter[filteredPlayer["competitiveTier"]]

def getMatches(puuid):
    url = f"https://na.api.riotgames.com/val/match/v1/matchlists/by-puuid/{puuid}"
    response = requests.get(url, headers = api_header)

    return response.json()["history"]

def getMatchData(matchList, matchCount = 30):
    #takes a list of MatchlistEntryDto and turns them into MatchDto (here called matchDataList) which allows them to be parsed 
    out = []
    
    for match in matchList:
        if len(out)>= matchCount:
            break
        id = match["matchId"]
        url = f"https://na.api.riotgames.com/val/match/v1/matches/{id}"
        response = requests.get(url, headers = api_header)
        out.append(response.json())

    return out

def getPlayerData(matchDataList, puuid):
    out = []
    puuidFilter = lambda p: p["puuid"]==puuid

    for match in matchDataList:
        filteredPlayer = list(filter(puuidFilter, match["players"]))[0]
        out.append(filteredPlayer)

    return out

def getLeaderboard(matchDataList, puuid):
    out = []
    score = lambda x: x["stats"]["score"]
    id = lambda x: x["puuid"]

    for match in matchDataList:
        scores = map(score, match["players"])
        puuids = map(id, match["players"])
        cache = sorted(list(zip(scores, puuids)), reverse=True)
        
        sortedIds = [x for _,x in cache]
        out.append(sortedIds.index(puuid))
    
    return out

def getRoundStats(matchDataList, puuid):
    out = []
    puuidFilter = lambda p: p["puuid"]==puuid
    playerGrabber = lambda x: x["playerStats"]

    for match in matchDataList:
        playerStats = chain.from_iterable(map(playerGrabber, match["roundResults"]))
        filteredStats = list(filter(puuidFilter, playerStats))
        out.append(filteredStats)
    
    return out

def getEconomy(playerRoundStats):
    money = lambda x: x["economy"]["spent"]

    out = sum(map(money, playerRoundStats))

    return out

def getDamage(playerRoundStats):
    damage = lambda x: x["damage"]

    statList = chain.from_iterable(map(damage, playerRoundStats))
    stats = [0,]*4 #in format [damage, legshot, bodyshot, headshot]

    for stat in statList:
        stat.pop("reciever")
        stats = list(map(add, stats,stat.values())) #total the stats

    return stats

def deathLocations(matchDataList, puuid = ""):
    out = []
    teams = {}
    puuidFilter = lambda p: p["killer"] == puuid or p["victim"] == puuid
    playerGrabber = lambda x: x["playerStats"]
    killGrabber = lambda x: x["kills"]
    locationGrabber = lambda x: x["victimLocation"]
    teamGrabber = lambda x: teams[x["victim"]] #currently based on defense/ offense color, can be changed to ally/enemy color


    for match in matchDataList:
        teams = {}
        for player in match["players"]:
            teams[player["puuid"]] = player["teamId"]
        playerStats = chain.from_iterable(map(playerGrabber, match["roundResults"]))
        kills = chain.from_iterable(map(killGrabber, playerStats))
        kills = filter(puuidFilter, kills) * bool(puuid) or kills * bool(puuid) #given puuid- filter else dont
        locations = map(locationGrabber, kills)
        teamList = map(teamGrabber, kills)

        out.append(list(set(zip(locations, teamList))))
    
    return list(chain.from_iterable(out))

def convertLocation(locations, gameMap):
    formula = lambda x: (x[0]*locationVars[gameMap]["X"][0]+locationVars[gameMap]["X"][1], 7000 - x[1]*locationVars[gameMap]["Y"][0]+locationVars[gameMap]["Y"][1])
    changetopixel = lambda x: ((x[0]/7000)*1024, (x[1]/7000)*1024)

    return list(map(changetopixel, map(formula, locations)))

def agentStats(playerDataList):
    getAgent = lambda x: agentConverter[x["characterId"]]

    return list(map(getAgent, playerDataList))

def rankStats(matchDataList, playerDataList):
    getDate = lambda x: datetime.fromtimestamp(x["matchInfo"]["gameStartMillis"]/1000).strftime("%b %d")
    getTier = lambda x: x["competitiveTier"]

    return (list(map(getTier, playerDataList)), list(map(getDate, matchDataList))) #tier and date of getting said tier

def splitStats(playerDataList):
    statList = [match["stats"] for match in playerDataList]
    stats = [0,]*7 #in format [score, rounds, kills, deaths, assists, playtime, abilities]

    for stat in statList:
        stat["abilityCasts"] = sum(stat["abilityCasts"].values())
        stats = list(map(add, stats,stat.values())) #total the stats

    return stats

def rankedFilter(matchDataList):
    ranked = lambda x: x["matchInfo"]["isRanked"]
    
    return list(filter(ranked, matchDataList))

def normalFilter(matchDataList):
    normal = lambda x: x["matchInfo"]["queueId"] in ["COMPETITIVE", "UNRATED"]
    
    return list(filter(normal, matchDataList))

def mapFilter(matchDataList, gameMap):
    maps = lambda x: mapConverter[x["matchInfo"]["mapId"]] ==gameMap

    return list(filter(maps, matchDataList))