from posix import X_OK
from PIL import Image, ImageFont, ImageDraw
import os
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap

dir = os.path.dirname(__file__)
ASSETSDIR = os.path.join(dir, "Assets")
CACHEPATH = os.path.join(ASSETSDIR, "cache.png") #deleted every 24hrs to preserve privacy
FONTSPATH = os.path.join(ASSETSDIR, "Fonts")
ICONSPATH = os.path.join(ASSETSDIR, "Icons")
MAPSPATH = os.path.join(ASSETSDIR, "Maps")
font = ImageFont.truetype(os.path.join(FONTSPATH, "Roboto-Regular.ttf"), 40)
agentIcons = {
    "Astra" : Image.open(os.path.join(ICONSPATH, r"Agents\astra.png")),
    "Breach" : Image.open(os.path.join(ICONSPATH, r"Agents\breach.png")),
    "Brimstone" : Image.open(os.path.join(ICONSPATH, r"Agents\brimstone.png")),
    "Cypher" : Image.open(os.path.join(ICONSPATH, r"Agents\cypher.png")),
    "Jett" : Image.open(os.path.join(ICONSPATH, r"Agents\jett.png")),
    "KAY/O" : Image.open(os.path.join(ICONSPATH, r"Agents\kayo.png")),
    "Killjoy" : Image.open(os.path.join(ICONSPATH, r"Agents\killjoy.png")),
    "Omen" : Image.open(os.path.join(ICONSPATH, r"Agents\omen.png")),
    "Phoenix" : Image.open(os.path.join(ICONSPATH, r"Agents\phoenix.png")),
    "Raze" : Image.open(os.path.join(ICONSPATH, r"Agents\raze.png")),
    "Reyna" : Image.open(os.path.join(ICONSPATH, r"Agents\reyna.png")),
    "Sage" : Image.open(os.path.join(ICONSPATH, r"Agents\sage.png")),
    "Skye" : Image.open(os.path.join(ICONSPATH, r"Agents\skye.png")),
    "Sova" : Image.open(os.path.join(ICONSPATH, r"Agents\sova.png")),
    "Viper" : Image.open(os.path.join(ICONSPATH, r"Agents\viper.png")),
    "Yoru" : Image.open(os.path.join(ICONSPATH, r"Agents\yoru.png"))
}
rankIcons = dict()
for file in os.listdir(os.path.join(ICONSPATH, r"Ranks")):
    rankIcons[file[:-4]] = Image.open(os.path.join(ICONSPATH, rf"Ranks\{file}"))

mapIcons = dict()
for file in os.listdir(os.path.join(MAPSPATH)):
    mapIcons[file[:-4]] = Image.open(os.path.join(MAPSPATH, rf"{file}"))


def drawPickrate(agentStats: dict):
    prbg = Image.open(os.path.join(ASSETSDIR, "pickratebg.png"))
    drawpr = ImageDraw.Draw(prbg)
    agents, precentage = agentStats.items()
    text1 = f"Agent:      Pickrate:\n\n{agents[0]}\n\{agents[1]}\n\{agents[2]}\n\{agents[3]}\n\{agents[4]}"
    text2 = f"{precentage[0]}%\n\{precentage[1]}%\n\{precentage[2]}%\n\n{precentage[3]}%\n\n{precentage[4]}%"

    drawpr.multiline_text((152, 23), text1, (255, 255, 255), font=font, spacing = 13)
    drawpr.multiline_text((381, 124), text2, (255, 255, 255), font=font, spacing = 13, align = "center")
    
    for i, agent in enumerate(agents):
        prbg.paste(agentIcons[agent], (26,80+104*i), agentIcons[agent])

    prbg.save(CACHEPATH)

def drawOverview(overviewStats: dict):
    ovbg = Image.open(os.path.join(ASSETSDIR, "overviewbg.png"))
    drawpr = ImageDraw.Draw(ovbg)
    text1 = f"Avg. Frag\n{overviewStats['Frag']}\n\nTime Played\n{overviewStats['Hours']} hours"
    text2 = f"ACS\n{overviewStats['ACS']}\n\nK/D\n{overviewStats['KD']}"
    text3 = f"HS%\n{overviewStats['HS%']}%\n\nK/R\n{overviewStats['KR']}"

    drawpr.multiline_text((280, 24), text1, (255, 255, 255), font=font, spacing = 13, align = "center")
    drawpr.multiline_text((591, 24), text2, (255, 255, 255), font=font, spacing = 13, align = "center")
    drawpr.multiline_text((829, 24), text3, (255, 255, 255), font=font, spacing = 13, align = "center")
    
    ovbg.paste(rankIcons[overviewStats["Rank"]], (9,21), rankIcons[overviewStats["Rank"]])

    ovbg.save(CACHEPATH)

def drawRank(rank: str):
    rabg = Image.open(os.path.join(ASSETSDIR, "rankbg.png"))
    drawpr = ImageDraw.Draw(rabg)

    drawpr.text((150.5, 274), rank, (255, 255, 255), font=font, spacing = 13, align = "center", anchor = "ma")
    
    rabg.paste(rankIcons[rank], (22,10), rankIcons[rank])

    rabg.save(CACHEPATH)

def drawGraph(rankStats: list):
    rankTiers, dates = rankStats
    plt.figure(figsize=(10, 10), dpi=70)
    positions = (0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23, 24)
    labels = ("Un", "I1", "I2", "I3", "B1", "B2", "B3", "S1", "S2", "S3", "G1", "G2", "G3", "P1", "P2", "P3", "D1", "D2", "D3", "Im", "Rad")
    plt.xticks(list(range(len(rankTiers))),dates)
    plt.yticks(positions, labels)
    plt.grid()
    ax = plt.gca()
    ax.set_facecolor('#36393f')
    lines = []
    cmap = []
    for i, point in enumerate(rankTiers[1:]):
        lp = rankTiers[i]
        if point - lp < 0:
            cmap.append("r")
        else:
            cmap.append("g")
        lines.append([[i,lp],[i+1,point]])

    rankTiers=LineCollection(lines, colors=cmap, lw = 5)
    rankTiers.set_capstyle("round")
    ax.add_collection(rankTiers)
    ax.margins(x=0, y=0.05)
    plt.savefig("cache.png")

def drawLocmap(locations, teams, gameMap):
    mapbg = mapIcons[gameMap]
    drawmap = ImageDraw.Draw(mapbg)
    mix = zip(locations,teams)
    teamDict = {"red":(255,0,0), "green": (0,255,0)}
    
    for x, team in mix:
        drawmap.text(x, "x", teamDict[team.lower()], font=font, spacing = 13, align = "center", anchor = "mm")
    
    mapbg.save(CACHEPATH)