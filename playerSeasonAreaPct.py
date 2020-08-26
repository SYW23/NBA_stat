import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpathes
from util import LoadPickle, yieldGames, gameMarkToDir, getCode
from klasses.Player import Player
import math
import pickle
import os
import numpy as np
import matplotlib.colors as Mcolors

#%%
def distance(p1, p2):
    return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)** 0.5


def angle(p1, p2):
    direct = 'right' if p2[1] > p1[1] else 'left'
    return math.degrees(math.atan((p2[0] - p1[0]) / (p2[1] - p1[1]))), direct

def zone(ang, di, p=2):
    if p == 2:
        if di == 'left':
            if ang >= -45:
                return 0
            else:
                return 1
        else:
            if ang <= 45:
                return 3
            else:
                return 2
    else:
        if di == 'left':
            if ang >= -15:
                return 0
            elif -60 <= ang < -15:
                return 1
            else:
                return 2
        else:
            if ang <= 15:
                return 4
            elif 15 < ang <= 60:
                return 3
            else:
                return 2


def zoom(spot, dis, score):
    center = [54.5, 249.5]
    if dis < 3:
        return 0
    ang, di = angle(center, spot)
    if score == 2:
        if 3 <= dis < 10:
            return 1 + zone(ang, di)
        elif 10 <= dis < 16:
            return 5 + zone(ang, di)
        elif 16 <= dis:
            return 9 + zone(ang, di)
    else:
        if dis < 30:
            return 13 + zone(ang, di, p=3)
        else:
            return 17 + zone(ang, di, p=3)


def getCor(center, radius, angle, left=True):
    xPlus = radius * math.cos(math.radians(angle))
    yPlus = radius * math.sin(math.radians(angle))
    ans = [center[0] + yPlus, center[1] - xPlus] if left else [center[0] + yPlus, center[1] + xPlus]
    return ans

R = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     10, 25, 50, 75, 100, 120, 140, 160, 170, 180, 190, 200, 210, 220]
G = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250,
     255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
     255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255]
B = [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 250,
     240, 230, 220, 210, 200, 190, 180, 170, 160, 150, 140, 130, 120,
     105, 90, 60, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
HomeOrAts = [[4, 5], [2, 1]]    # 主，客
marginX = 5
marginY = 10
r = 49
t = 249.5
radius3 = 239
regularOrPlayoffs = ['regular', 'playoff']

f = open('./data/playerBasicInformation.pickle', 'rb')
playerInf = pickle.load(f)
f.close()

top250 = ['abdulka01', 'malonka01', 'jamesle01', 'bryanko01', 'jordami01', 'nowitdi01', 'chambwi01', 'onealsh01', 'malonmo01', 'hayesel01', 'olajuha01', 'roberos01', 'wilkido01', 'duncati01', 'piercpa01', 'havlijo01', 'anthoca01', 'garneke01', 'cartevi01', 'englial01', 'millere01', 'westje01', 'ewingpa01', 'allenra02', 'iversal01', 'barklch01', 'parisro01', 'dantlad01', 'wadedw01', 'bayloel01', 'duranke01', 'drexlcl01', 'paytoga01', 'birdla01', 'greerha01', 'bellawa01', 'gasolpa01', 'pettibo01', 'robinda01', 'hardeja01', 'gervige01', 'richmmi01', 'johnsjo02', 'westbru01', 'chambto01', 'jamisan01', 'stockjo01', 'kingbe01', 'aldrila01', 'robincl02', 'daviswa03', 'parketo01', 'cummite01', 'crawfja01', 'laniebo01', 'johnsed03', 'goodrga01', 'theusre01', 'ellisda01', 'pippesc01', 'terryja01', 'walkech01', 'thomais01', 'mcadobo01', 'paulch01', 'howardw01', 'randoza01', 'aguirma01', 'schaydo01', 'barryri01', 'mcgratr01', 'ervinju01', 'ricegl01', 'bingda01', 'freewo01', 'murphca01', 'hudsolo01', 'mullich01', 'wilkele01', 'howelba01', 'johnsma02', 'mariosh01', 'blackro01', 'thorpot01', 'kiddja01', 'monroea01', 'nashst01', 'mchalke01', 'finlemi01', 'sikmaja01', 'willike02', 'malonje01', 'boshch01', 'webbech01', 'hillgr01', 'cousybo01', 'brandel01', 'willibu01', 'sprewla01', 'architi01', 'curryst01', 'stackje01', 'dumarjo01', 'worthja01', 'marbust01', 'derozde01', 'millean02', 'arizipa01', 'smithra01', 'howarju01', 'gayru01', 'harpede01', 'wallara01', 'stoudam01', 'vandeki01', 'maravpe01', 'twymaja01', 'billuch01', 'schrede01', 'hamilri01', 'nancela01', 'hornaje01', 'walkean02', 'cassesa01', 'portete01', 'fraziwa01', 'gilmoar01', 'lewisra02', 'johnsde01', 'dandrbo01', 'jonessa01', 'hardati01', 'barnedi01', 'kempsh01', 'perkisa01', 'drewjo01', 'scottby01', 'vanardi01', 'abdursh01', 'mitchmi01', 'jefferi01', 'edwarja01', 'ellismo01', 'bibbymi01', 'gueriri01', 'isselda01', 'richaja01', 'wilkeja01', 'shortpu01', 'haywosp01', 'lillada01', 'houstal01', 'russebi01', 'hawkihe01', 'piercri01', 'stricro02', 'thurmna01', 'willilo02', 'whitejo01', 'jeffeal01', 'mournal01', 'robingl01', 'vanarto01', 'jonesed02', 'willigu01', 'debusda01', 'lucasje01', 'ginobma01', 'westda01', 'brownfr01', 'boozeca01', 'adamsal01', 'harpero01', 'lovebo01', 'johnsma01', 'persoch01', 'millspa01', 'willide01', 'laimbbi01', 'stojape01', 'cunnibi01', 'woolror01', 'mcdanxa01', 'iguodan01', 'cowenda01', 'griffbl01', 'hagancl01', 'davisba01', 'smithst01', 'divacvl01', 'tomjaru01', 'lowryky01', 'denglu01', 'onealje01', 'harrial01', 'roseja01', 'maggeco01', 'johnske02', 'lopezbr01', 'walkeke02', 'artesro01', 'mullije01', 'smithjo03', 'grantho01', 'loveke01', 'jacksst02', 'boozebo01', 'gillke01', 'colemde01', 'tisdawa01', 'smitsri01', 'georgpa01', 'thompmy01', 'westppa01', 'wickssi01', 'odomla01', 'johnsmi01', 'newmajo01', 'cartwbi01', 'youngth01', 'gilliar01', 'jacksji01', 'curryde01', 'sharmbi01', 'vanexni01', 'birdsot01', 'marinja01', 'davisan02', 'newlimi01', 'jacksma01', 'kerrre01', 'carrojo01', 'butleca01', 'oaklech01', 'martike02', 'griffda01', 'russeca01', 'mannida01', 'lucasma01', 'greenac01', 'conlemi01', 'greenjo01', 'floydsl01', 'mcdyean01', 'gasolma01', 'cheekma01', 'heinsto01', 'reedwi01', 'tripuke01', 'longjo01', 'smithjr01']

players = []
for i in playerInf[1:]:
    playerName, playerMark = i[0], i[1].split('/')[-1].rstrip('.html')
    playerName = playerName.replace(' ', '')
    playerName = playerName.replace('-', '')
    if i[2] and i[3]:
        if int(i[6]) >= 1997 and playerMark in top250:
            players.append([playerName, playerMark])

#%%
regularOrPlayoff = 0
ROP = regularOrPlayoffs[regularOrPlayoff]
for i in players[35:36]:
    print("starting analysing %s's games ..." % i[0])
    player = Player(i[1], ROP)
    missing_shot = 0
    areaPct = np.zeros((21,3))    #0miss1make
    for season in player.yieldSeasons():
        for gameInf in player.yieldGames(season):
            gameMark, team = gameInf[1], gameInf[3]
            # 读取比赛文件
            gameDir = gameMarkToDir(gameMark, ROP)
            gameDir_shot = gameMarkToDir(gameMark, ROP, shot=True)
            playerGame = LoadPickle(gameDir)
            playerGame_shot = LoadPickle(gameDir_shot)
            index_shot = 0
            # 判断主客场
            HOA = 1 if team == gameMark[-3:] else 0    # 0客1主
            HomeOrAt = HomeOrAts[HOA-1]
            for index, quarter in enumerate(playerGame):
                for play in quarter:
                    if len(play) == 6:
                        if play[HomeOrAt[1]]:
                            playerPlayed = play[HomeOrAt[1]].split(' ')[0]
                            if playerPlayed == i[1] and (play[HomeOrAt[0]] or 'misses' in play[HomeOrAt[1]]):
                                # 此球员有得分/错失得分
                                score = 0
                                diff = play[3]
                                if HOA == 1:
                                    diff = diff.split('-')[-1] + '-' + diff.split('-')[0]
                                if play[HomeOrAt[0]]:
                                    # 球员得分
                                    DLT = 1
                                    score = int(play[HomeOrAt[0]])
                                    if score >= 4:
                                        if 'free throw' in play[HomeOrAt[1]]:
                                            score = 1
                                        elif '2-pt' in play[HomeOrAt[1]]:
                                            score = 2
                                        elif '3-pt' in play[HomeOrAt[1]]:
                                            score = 3
                                else:
                                    # 球员失手
                                    DLT = 0
                                    if 'free throw' in play[HomeOrAt[1]]:
                                        score = 1
                                    elif '2-pt' in play[HomeOrAt[1]]:
                                        score = 2
                                    elif '3-pt' in play[HomeOrAt[1]]:
                                        score = 3
                                    elif 'misses no shot'in play[HomeOrAt[1]]:
                                        continue
                                # print(score, diff, DLT)
                                while score > 1 and True:
                                    try:
                                        shot = playerGame_shot[HOA][index_shot]
                                    except:
                                        # print('missing record of a shot!')
                                        missing_shot += 1
                                        break
                                    inf = shot[2]
                                    if i[1] not in inf[2]:
                                        index_shot += 1
                                        continue
                                    # print(shot)
                                    if diff != shot[1].split(' ')[-1]:
                                        # print('missing record of a shot!')
                                        missing_shot += 1
                                        break
                                    try:
                                        if DLT == 0:
                                            assert inf[3] == 'miss'
                                        else:
                                            assert inf[3] == 'make'
                                        assert diff == shot[1].split(' ')[-1]
                                    except:
                                        print(play, shot)
                                        break
                                    
                                    cors = shot[0].split(';')
                                    x = int(cors[1].split(':')[1].rstrip('px')) + marginX
                                    y = int(cors[0].split(':')[1].rstrip('px')) + marginY
                                    score = 2 if '2-pointer' in shot[1] else 3
                                    dis = int(shot[1].split('<br>')[-2].split(' ')[-2])
                                    areaPct[zoom([y, x], dis, score), DLT] += 1
                                    index_shot += 1
                                    break
    print('未记录投篮点%d个' % missing_shot)
    for a in range(21):
        areaPct[a, 2] = areaPct[a, 1] / (areaPct[a, 0] + areaPct[a, 1])\
               if areaPct[a, 0] + areaPct[a, 1] > 0 else np.nan


    #%%
    lw = 1
    ls = '--'
    pmax = 60
    pmin = 20
    factor = 99/(pmax - pmin)
    court = mpimg.imread('nbahalfcourt.png')
    center = [r, t]
    plt.imshow(court)
    # plt.scatter([0], [0])
    plt.xlim((0, 499))
    plt.ylim((471, 0))
    # cir = mpathes.Circle((t, r), 235)
    cirs = [plt.Circle((t, r), 30, color='gray', clip_on=True, fill=False, ls=ls, lw=lw),
            plt.Circle((t, r), 100, color='gray', clip_on=True, fill=False, ls=ls, lw=lw),
            plt.Circle((t, r), 160, color='gray', clip_on=True, fill=False, ls=ls, lw=lw),
            # plt.Circle((t, r), 239, color='gray', clip_on=True, fill=False, ls=ls, lw=lw),
            plt.Circle((t, r), 300, color='gray', clip_on=True, fill=False, ls=ls, lw=lw)]
    ax = plt.gcf().gca()
    for c in cirs:
        ax.add_patch(c)
    
    xs = [[getCor(center, 30, 45, left=True)[1], t - radius3 / 2** 0.5],    # 两分45度左
          [getCor(center, 30, 45, left=False)[1], t + radius3 / 2** 0.5],    # 两分45度右
          [t, t],    # 两分90度
          [0, t - 218], [500, t + 218],    # 三分线外15度
          [0, t - radius3 / 2], [500, t + radius3 / 2],
          [t, t]]    # 三分线外60度
    ys = [[getCor(center, 30, 45, left=True)[0], r + radius3 / 2** 0.5],
          [getCor(center, 30, 45, left=False)[0], r + radius3 / 2** 0.5],
          [getCor(center, 30, 90, left=True)[0], r + radius3],
          [r + 66.85, r + 58.4], [r + 66.85, r + 58.4],
          [r + t * 3**0.5, r + radius3 / 2 * 3**0.5], [r + t * 3**0.5, r + radius3 / 2 * 3**0.5],
          [0, 19]]
    for j in range(len(xs)):
        plt.plot(xs[j], ys[j], color='gray', ls=ls, lw=lw)
    x = np.linspace(200, 300, 1000)
    # plt.fill_between(x, cirs[1], cirs[2], facecolor = "yellow")
    
    if areaPct[0, 2]*100 > pmax:
        pp =  0
    elif areaPct[0, 2]*100 < pmin:
        pp =  49
    else:
        pp = int(round((pmax - areaPct[0, 2]*100)*factor)//2)
    fc = [B[pp]/255, G[pp]/255, R[pp]/255]
    ax.text(249.5, 35,
            '%d/%d\n%.2f%%' % (areaPct[0, 1],
                               areaPct[0, 0]+areaPct[0, 1],
                               areaPct[0, 2]*100),
            fontsize = 5, 
            bbox=dict(boxstyle='round, pad=0.5', fc=fc, ec='k', lw=1 ,alpha=0.6))
    ang = [15, 67.5, 67.5, 15] * 4
    dist = [65] * 4 + [130] * 4 + [200] * 4
    LOR = [True, True, False, False] * 3
    for j in range(12):
        if areaPct[j+1, 0] + areaPct[j+1, 1] > 0:
            cor = getCor(center, dist[j], ang[j], left=LOR[j])
            pp = int(round((pmax - areaPct[j+1, 2]*100)*factor)//2)
            fc = [B[pp]/255, G[pp]/255, R[pp]/255]
            ax.text(cor[1], cor[0],
                    '%d/%d\n%.2f%%' % (areaPct[j+1, 1],
                                       areaPct[j+1, 0]+areaPct[j+1, 1],
                                       areaPct[j+1, 2]*100),
                    fontsize=5, 
                    bbox=dict(boxstyle='round, pad=0.5', fc=fc, ec='k', lw=1 ,alpha=0.6))
    
    ang = [0, 37.5, 90, 37.5, 0, 50, 90, 50]
    dist = [235, 270, 270, 270, 235, 350, 340, 350]
    LOR = [True, True, False, False, False, True, False, False]
    for j in range(8):
        if areaPct[j+13, 0] + areaPct[j+13, 1] > 0:
            cor = getCor(center, dist[j], ang[j], left=LOR[j])
            pp = int(round((pmax - areaPct[j+13, 2]*100)*factor)//2)
            if pp > 49:
                pp = 49
            fc = [B[pp]/255, G[pp]/255, R[pp]/255]
            ax.text(cor[1], cor[0],
                    '%d/%d\n%.2f%%' % (areaPct[j+13, 1],
                                       areaPct[j+13, 0]+areaPct[j+13, 1],
                                       areaPct[j+13, 2]*100),
                    fontsize=5, 
                    bbox=dict(boxstyle='round, pad=0.5', fc=fc, ec='k', lw=1 ,alpha=0.6))
    
    Xcolor = []
    for c in range(len(R)):
        Xcolor.append([B[c]/255, G[c]/255, R[c]/255])
    cmap = Mcolors.ListedColormap(Xcolor[::-1], 'indexed')
    psm = ax.pcolormesh([[], []], cmap=cmap, rasterized=True)
    # colorPosi = plt.gcf().add_axes([0.92, 0.25, 0.01, 0.5])
    cl = plt.gcf().colorbar(psm, ax=ax, shrink=.9)
    cl.set_ticks(np.arange(0, 5/4, 1/4))
    cl.set_ticklabels(['20%', '30%', '40%', '50%', '60%'])
    cl.ax.tick_params(labelsize=6)
    
    plt.axis('off')
    plt.title(i[0], fontsize=12)
    plt.savefig('./%sResults/playerSeasonAreaPct/%s_%s.png' % (ROP, i[0], i[1]), bbox_inches='tight', dpi=250)
    # plt.show()
    plt.close()




