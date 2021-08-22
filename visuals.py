from PIL import Image, ImageFont, ImageDraw
import os
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

PATH = os.path.dirname(__file__)
ASSETS_PATH = os.path.join(PATH, "Assets")
CACHE_PATH = os.path.join(ASSETS_PATH, "cache.png")  # deleted every 24hrs to preserve privacy
FONTS_PATH = os.path.join(ASSETS_PATH, "Fonts")
ICONS_PATH = os.path.join(ASSETS_PATH, "Icons")
MAPS_PATH = os.path.join(ASSETS_PATH, "Maps")
font = ImageFont.truetype(os.path.join(FONTS_PATH, "Roboto-Regular.ttf"), 40)
agent_icons = {
    "Astra": Image.open(os.path.join(ICONS_PATH, r"Agents\astra.png")),
    "Breach": Image.open(os.path.join(ICONS_PATH, r"Agents\breach.png")),
    "Brimstone": Image.open(os.path.join(ICONS_PATH, r"Agents\brimstone.png")),
    "Cypher": Image.open(os.path.join(ICONS_PATH, r"Agents\cypher.png")),
    "Jett": Image.open(os.path.join(ICONS_PATH, r"Agents\jett.png")),
    "KAY/O": Image.open(os.path.join(ICONS_PATH, r"Agents\kayo.png")),
    "Killjoy": Image.open(os.path.join(ICONS_PATH, r"Agents\killjoy.png")),
    "Omen": Image.open(os.path.join(ICONS_PATH, r"Agents\omen.png")),
    "Phoenix": Image.open(os.path.join(ICONS_PATH, r"Agents\phoenix.png")),
    "Raze": Image.open(os.path.join(ICONS_PATH, r"Agents\raze.png")),
    "Reyna": Image.open(os.path.join(ICONS_PATH, r"Agents\reyna.png")),
    "Sage": Image.open(os.path.join(ICONS_PATH, r"Agents\sage.png")),
    "Skye": Image.open(os.path.join(ICONS_PATH, r"Agents\skye.png")),
    "Sova": Image.open(os.path.join(ICONS_PATH, r"Agents\sova.png")),
    "Viper": Image.open(os.path.join(ICONS_PATH, r"Agents\viper.png")),
    "Yoru": Image.open(os.path.join(ICONS_PATH, r"Agents\yoru.png"))
}
rankIcons = dict()
for file in os.listdir(os.path.join(ICONS_PATH, r"Ranks")):
    rankIcons[file[:-4]] = Image.open(os.path.join(ICONS_PATH, rf"Ranks\{file}"))

mapIcons = dict()
for file in os.listdir(os.path.join(MAPS_PATH)):
    mapIcons[file[:-4]] = Image.open(os.path.join(MAPS_PATH, rf"{file}"))


def draw_pickrate(agent_stats: dict):
    prbg = Image.open(os.path.join(ASSETS_PATH, "pickratebg.png"))
    drawpr = ImageDraw.Draw(prbg)
    agents, precentage = agent_stats.items()
    text1 = f"Agent:      Pickrate:" \
            f"\n\n{agents[0]}" \
            f"\n\n{agents[1]}" \
            f"\n\n{agents[2]}" \
            f"\n\n{agents[3]}" \
            f"\n\n{agents[4]}"

    text2 = f"{precentage[0]}%" \
            f"\n\n{precentage[1]}% " \
            f"\n\n{precentage[2]}% " \
            f"\n\n{precentage[3]}% " \
            f"\n\n{precentage[4]}%"

    drawpr.multiline_text((152, 23), text1, (255, 255, 255), font=font, spacing=13)
    drawpr.multiline_text((381, 124), text2, (255, 255, 255), font=font, spacing=13, align="center")

    for i, agent in enumerate(agents):
        prbg.paste(agent_icons[agent], (26, 80 + 104 * i), agent_icons[agent])

    prbg.save(CACHE_PATH)


def draw_overview(overview_stats: dict):
    ovbg = Image.open(os.path.join(ASSETS_PATH, "overviewbg.png"))
    drawpr = ImageDraw.Draw(ovbg)
    text1 = f"Avg. Frag\n{overview_stats['Frag']}\n\nTime Played\n{overview_stats['Hours']} hours"
    text2 = f"ACS\n{overview_stats['ACS']}\n\nK/D\n{overview_stats['KD']}"
    text3 = f"HS%\n{overview_stats['HS%']}%\n\nK/R\n{overview_stats['KR']}"

    drawpr.multiline_text((280, 24), text1, (255, 255, 255), font=font, spacing=13, align="center")
    drawpr.multiline_text((591, 24), text2, (255, 255, 255), font=font, spacing=13, align="center")
    drawpr.multiline_text((829, 24), text3, (255, 255, 255), font=font, spacing=13, align="center")

    ovbg.paste(rankIcons[overview_stats["Rank"]], (9, 21), rankIcons[overview_stats["Rank"]])

    ovbg.save(CACHE_PATH)


def draw_rank(rank: str):
    rabg = Image.open(os.path.join(ASSETS_PATH, "rankbg.png"))
    drawpr = ImageDraw.Draw(rabg)

    drawpr.text((150.5, 274), rank, (255, 255, 255), font=font, spacing=13, align="center", anchor="ma")

    rabg.paste(rankIcons[rank], (22, 10), rankIcons[rank])

    rabg.save(CACHE_PATH)


def draw_graph(rank_stats: list):
    rank_tiers, dates = rank_stats
    plt.figure(figsize=(10, 10), dpi=70)
    positions = (0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23, 24)
    labels = (
        "Un", "I1", "I2", "I3", "B1", "B2", "B3", "S1", "S2", "S3", "G1", "G2", "G3", "P1", "P2", "P3", "D1", "D2",
        "D3",
        "Im", "Rad")
    plt.xticks(list(range(len(rank_tiers))), dates)
    plt.yticks(positions, labels)
    plt.grid()
    ax = plt.gca()
    ax.set_facecolor('#36393f')
    lines = []
    cmap = []
    for i, point in enumerate(rank_tiers[1:]):
        lp = rank_tiers[i]
        if point - lp < 0:
            cmap.append("r")
        else:
            cmap.append("g")
        lines.append([[i, lp], [i + 1, point]])

    rank_tiers = LineCollection(lines, colors=cmap, lw=5)
    rank_tiers.set_capstyle("round")
    ax.add_collection(rank_tiers)
    ax.margins(x=0, y=0.05)
    plt.savefig("cache.png")


def draw_locmap(locations, teams, gamemap):
    mapbg = mapIcons[gamemap]
    drawmap = ImageDraw.Draw(mapbg)
    mix = zip(locations, teams)
    team_dict = {"red": (255, 0, 0), "green": (0, 255, 0)}

    for x, team in mix:
        drawmap.text(x, "x", team_dict[team.lower()], font=font, spacing=13, align="center", anchor="mm")

    mapbg.save(CACHE_PATH)
