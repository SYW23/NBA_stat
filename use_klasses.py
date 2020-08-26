from klasses.Game import Play, Game
from klasses.Player import Player
from klasses.clrbr import cs
from util import score_diff_time, tailTime, groupDiff

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns

mpl.rcParams['font.sans-serif'] = ['SimHei']    # 解决中文乱码

ROP = 'regular'
pm = 'jamesle01'
score = 0
asts = 0
player = Player(pm, ROP)

inter = 600    # 设置按时间归并区间的间隔
inter_s = inter // 10
whole = 34800    # 整场比赛时间（双加时为止）
max_diff = 40
diff_inter = 5
# 1、2、3分 x 命中数、出手数 x -40~40分差 x 间隔统计时间
shoots = np.zeros((3, 2, max_diff * 2 // diff_inter + 1, whole//inter))
prctg = np.zeros((3, max_diff * 2 // diff_inter + 1, whole//inter))

for season in player.yieldSeasons():
    for gameInf in player.yieldGames(season):
        # score += int(gameInf[26])
        gm = gameInf[1]
        team = gameInf[3]
        op = gameInf[5]
        game = Game(gm, ROP, team, op)
        
        for qtr in range(game.quarters):
            for playInf in game.yieldPlay(qtr):
                play = Play(playInf, qtr, pm=pm, HOA=game.HOA)
                if play.playRecord() and play.teamPlay():
                    if play.playerAst():    # 助攻
                        asts += 1
                    elif play.playerMadeShoot():    # 命中投篮
                        s, d, t = score_diff_time(play, game, max_diff)
                        d -= s    # 关注的是球员得分前的分差
                        score += s
                        t = tailTime(t, inter_s)
                        d = groupDiff(d + 40, max_diff, diff_inter)
                        shoots[s-1, 0, d, t] += 1
                        shoots[s-1, 1, d, t] += 1
                    elif play.playerMissShoot():    # 投丢投篮
                        s, d, t = score_diff_time(play, game, max_diff)
                        t = tailTime(t, inter_s)
                        d = groupDiff(d + 40, max_diff, diff_inter)
                        shoots[s-1, 1, d, t] += 1
                        
prctg = shoots[:, 0, :, :] / shoots[:, 1, :, :]

#%%
# 热度图
cs = np.array(cs[::-1]) / 255.0
icmap = colors.ListedColormap(cs, name='my_color')
cmap = icmap    # 色带
xlabels = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '1st',
               '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '2nd',
               '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '3rd',
               '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '4th',
               '1', '2', '3', '4', 'OT1', '1', '2', '3', '4', 'OT2']
ylabels = []
for i in range(-max_diff // diff_inter, max_diff // diff_inter + 1):
    if i == 0:
        ylabels.append('0')
    elif i > 0:
        ylabels.append('%d~%d' % (5*(i-1)+1, 5*i))
    else:
        ylabels.append('%d~%d' % (5*i, 5*i+4))

fig, axs = plt.subplots(3, figsize=(50, 20))
for ind, ax in enumerate(axs):
    sns.set(font_scale=0.5)
    sns.heatmap(prctg[ind], ax=ax, cmap=cmap, linewidths=0.5,
                annot = True, cbar=False, fmt='.2f')
    
    # 布局
    # ax.invert_yaxis()
    ax.tick_params(labelsize=16)    # 轴坐标字体
    ax.set_xticklabels(xlabels)
    ax.set_yticklabels(ylabels, rotation=0)
    
colorPosi = fig.add_axes([0.92, 0.3, 0.01, 0.36])
cb = ax.figure.colorbar(ax.collections[0], cax=colorPosi)
cb.ax.tick_params(labelsize=16, direction='in', top=False, bottom=False, left=False, right=False)
# fig.colorbar(cmap=cmap, shrink = 0.5)
# ax.grid()
plt.suptitle(u'詹姆斯', fontsize=20)
print(score, asts)

plt.savefig('test.jpg', dpi=300)
plt.close('all')

#%%
X = np.arange(0, 17, step=1)    #  X轴的坐标
Y = np.arange(0, 58, step=1)    #Y轴的坐标
Z = shoots[1, 0, :, :]
xx, yy = np.meshgrid(X, Y)    # 网格化坐标
X, Y = xx.ravel(), yy.ravel()    # 矩阵扁平化
bottom = np.zeros_like(X)    # 设置柱状图的底端位值
Z = Z.ravel()    # 扁平化矩阵

width = height = 0.3    # 每一个柱子的长和宽

# 绘图设置
fig = plt.figure(figsize=(30, 30))
ax = fig.gca(projection='3d')    # 三维坐标轴
ax.bar3d(X, Y, bottom, width, height, Z, alpha=0.3)

# 坐标轴设置
ax.set_ylabel('time')
ax.set_yticks(np.arange(1, 59, 1))
ax.set_yticklabels(xlabels)
ax.set_xlabel('diff')
ax.set_xticks(np.arange(0, 17, 1))
ax.set_xticklabels(ylabels, rotation=45)
ax.set_zlabel('made')
plt.show()
plt.savefig('test3D.jpg', dpi=300)
plt.close('all')














