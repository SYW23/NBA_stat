# 篮下进攻和罚球
from klasses.Season import Season
from klasses.Game import Game, GameShooting, Play, Shooting
from util import LoadPickle, writeToPickle

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from adjustText import adjust_text

mpl.rcParams['font.sans-serif'] = ['SimHei']    # 解决中文乱码
plt.rcParams['axes.unicode_minus'] = False    # 解决坐标轴符号显示异常

def sigmoid(x):
    return 1 / (1 + np.exp(-x))
    
#%%
scale = (2, 1)    # 0: 篮下出手, 1: 罚球出手
players = {}
regularOrPlayoff = ['regular', 'playoff']
ROP = 1
for seas in range(1996, 2020):
    print('%d-%d' % (seas, seas + 1))
    season = Season(seas, regularOrPlayoff[ROP])    # 一个赛季
    for gm, _ in season.yieldGM():
        if gm == '202008150POR':
            continue
        game = Game(gm, regularOrPlayoff[ROP])    # 一场比赛
        for qtr in range(game.quarters):    # 一节
            for playInf in game.yieldPlay(qtr):
                play = Play(playInf, qtr)    # 一条记录
                rec, ind = play.record()
                if rec:
                    s = play.score(ind=ind)
                    if s == 1:    # 出手罚球
                        player = rec.split(' ')[0]
                        if player not in players:    # 初次统计某球员：创建新键
                            players[player] = []
                        if not players[player] or players[player][-1][0][:4] != str(seas):
                            players[player].append(['%s-%s' % (seas, seas + 1),
                                                    np.zeros(scale)])
                        
                        players[player][-1][1][1] += 1
        # 该场比赛的投篮记录
        game_shots = GameShooting(gm, regularOrPlayoff[ROP])
        for st in game_shots.yieldPlay():
            shot = Shooting(st)    # 一条投篮记录
            if shot.distance() < 3:    # 出手距离小于3
                player = shot.pm()    # 出手球员
                if player not in players:    # 初次统计某球员：创建新键
                    players[player] = []
                if not players[player] or players[player][-1][0][:4] != str(seas):
                    players[player].append(['%s-%s' % (seas, seas + 1),
                                            np.zeros(scale)])
                players[player][-1][1][0] += 1
            
#%%
pm2pn = LoadPickle('./data/playermark2playername.pickle')
plyrclrs = LoadPickle('./data/plyrclrs.pickle')
plyrs300 = []
plyrs1000 = []
texts = []
ROP_thres = [[300, 1000, 600, 100], [50, 200, 100, 50]]
plt.figure(figsize=(80, 80))
for p in players.keys():
    if p in plyrclrs.keys():
        color = plyrclrs[p]
    else:
        plyrclrs[p] = list(np.random.rand(3, ))
        writeToPickle('./data/plyrclrs.pickle', plyrclrs)
        color = plyrclrs[p]
    for s in players[p]:
        if s[1][0] > ROP_thres[ROP][0] and s[1][1] > ROP_thres[ROP][0]:
            if pm2pn[p] not in plyrs300:
                plyrs300.append(pm2pn[p])
            ss = s[1][0] + s[1][1]
            plt.scatter(s[1][0], s[1][1], alpha=sigmoid(ss/ROP_thres[ROP][2]), c=color,
                        linewidths=ss/ROP_thres[ROP][3]+ROP, label='%s %s' % (p, s[0]))
            if ss > ROP_thres[ROP][1] or s[1][0] > ROP_thres[ROP][2] or s[1][1] > ROP_thres[ROP][2]:
                if pm2pn[p] not in plyrs1000:
                    plyrs1000.append(pm2pn[p])
                texts.append(plt.text(s[1][0]+1, s[1][1]+1,
                                      '%s %s' % (pm2pn[p],s[0]),
                                      color=color, fontsize=25))
                # plt.annotate('%s %s' % (pm2pn[p], s[0]), color=color,
                #              xy=(s[1][0], s[1][1]),
                #              xytext=(s[1][0]+2, s[1][1]+2), fontsize=25)
adjust_text(texts, only_move={'text':'y'})    # 防止数据标注重叠
plt.xlabel('篮下出手(<3ft)', fontsize=50)
plt.ylabel('罚球出手', fontsize=50)
plt.xticks(fontsize=50)
plt.yticks(fontsize=50)
plt.grid()
plt.savefig('./%sResults/basket2FT/basket2FT.jpg' % regularOrPlayoff[ROP], dpi = 200)
plt.close('all')








