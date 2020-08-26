import pickle
import numpy as np
from PIL import Image
import os
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from util import gameMarkToDir, minusMinutes, playerGameScoreDistribution, addMinutes
from pylab import *
import matplotlib as mpl
import matplotlib.colors as Mcolors

mpl.rcParams['font.sans-serif'] = ['STXinwei']    # 解决中文乱码
plt.rcParams['axes.unicode_minus'] = False    # 解决坐标轴符号显示异常
plt.style.use('ggplot')    # 预设风格绘图
plt.rcParams['axes.facecolor'] = 'white'    # 背景设置为白色
plt.close('all')

regularOrPlayoffs = ['regular', 'playoff']
HomeOrAts = [[4, 5], [2, 1]]    # 主，客
colors = [['#004BE8', '#3FAF50', '#FF4500'],    # 得分
          ['#99EAEA', '#A4FF99', '#FFC0CB']]    # 失手
R = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     10, 25, 50, 75, 100, 120, 140, 160, 170, 180, 190, 200, 210, 220]
G = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250,
     255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
     255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255]
B = [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 250,
     240, 230, 220, 210, 200, 190, 180, 170, 160, 150, 140, 130, 120,
     105, 90, 60, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


f = open('./data/playerBasicInformation.pickle', 'rb')
playerInf = pickle.load(f)
f.close()

player = []
for i in playerInf[1:]:
    playerName, playerMark = i[0], i[1].split('/')[-1].rstrip('.html')
    playerName = playerName.replace(' ', '')
    playerName = playerName.replace('-', '')
    if i[2] and i[3]:
        if int(i[6]) >= 1997 and os.path.exists('./data/players/%s' % playerMark):
            player.append([playerName, playerMark])
inter = 60
diff = 5
regularOrPlayoff = 1
thres = [30, 50, 5]
for i in player[35:36]:
    print("starting analysing %s's games ..." % i[0], end='')
    goalOrMiss = playerGameScoreDistribution(i[0], i[1], HomeOrAts, colors, inter, regularOrPlayoffs[regularOrPlayoff])
    #%%
    pct_sort = [[], [], []]
    diffs = [[-50, -40], [-40, -30], [-30, -20], [-20, -15], [-15, -10], [-10, -5], [-5, 0],
             [0, 5], [5, 10], [10, 15], [15, 20], [20, 30], [30, 40], [40, 50]]
    for method in range(3):
        for m in diffs:    # 分差（不包含上界）
            start = m[0] + 50
            end = m[1] + 50
            ts_start = '0:00.0'
            fake_grow = '0:00.0'
            goal_, miss_ = 0, 0
            for n in range(4080//inter):
                # print(ts_start, goal_, miss_)
                goal, miss = 0, 0
                s = n * inter
                ms = s // 60
                ss = s % 60
                ts = '%d:%02d.0' % (ms, ss)
                ts_end = addMinutes(ts, '0:%02d.0' % inter)
                interval = minusMinutes(ts_end, ts_start)
                for x in range(start, end):
                    goal += int(goalOrMiss[0, method, x, n])
                    miss += int(goalOrMiss[1, method, x, n])
                goal_ += goal
                miss_ += miss
                if goal + miss + goal_ + miss_ == 0:
                    ts_start = ts_end
                    fake_grow = '0:00.0'
                    continue
                elif goal_ >= thres[method] or \
                     (int(interval[:-5]) >= 3 and goal_ + miss_ > 0) or \
                     (ts_start[:-5] < '12' and ts_end[:-5] >= '12') or \
                     (ts_start[:-5] < '24' and ts_end[:-5] >= '24') or \
                     (ts_start[:-5] < '36' and ts_end[:-5] >= '36') or \
                     (ts_start[:-5] < '48' and ts_end[:-5] >= '48') or \
                     (ts_start[:-5] < '53' and ts_end[:-5] >= '53') or \
                     (ts_start[:-5] < '58' and ts_end[:-5] >= '58'):
                    if goal + miss > 0 and fake_grow != '0:00.0':
                        fake_grow = minusMinutes(fake_grow, '0:%02d.0' % inter)
                    ts_end = minusMinutes(ts_end, fake_grow)
                    pct_sort[method].append([(goal_/(goal_ + miss_)*100),
                                             '%s,%s' % (ts_start, ts_end),
                                             '%f,%f' % (m[0]-0.5, m[1]-0.5), 
                                             '%d/%d' % (goal_, goal_+miss_)])
                    ts_start = ts_end
                    goal_, miss_, fake_grow = 0, 0, '0:00.0' 
                else:
                    if goal + miss == 0:
                        fake_grow = addMinutes(fake_grow, '0:%02d.0' % inter)
                    goal_ += goal
                    miss_ += miss
                    continue
            pct_sort[method].sort()
    
    # 画图
    fig, ax = plt.subplots(3, figsize=(70,27), sharey=True)
    # colorbar
    Xcolor = []
    for c in range(len(R)):
        Xcolor.append([B[c]/255, G[c]/255, R[c]/255])
    cmap = Mcolors.ListedColormap(Xcolor[::-1], 'indexed')
    for sub in range(3):
        psm = ax[sub].pcolormesh([[], []], cmap=cmap, rasterized=True)
        # colorPosi = fig.add_axes([0.92, 0.25, 0.01, 0.5])
        cl = fig.colorbar(psm, ax=ax[sub])
        cl.set_ticks(np.arange(0, 2, 1))
        cl.set_ticklabels(['%.2f%%' % pct_sort[sub][0][0], '%.2f%%' % pct_sort[sub][-1][0]])
        cl.ax.tick_params(labelsize=24)
    
    xlabels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '第一节完',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '第二节完',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '第三节完',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '第四节完',
                   '1', '2', '3', '4', '加时1完', '1', '2', '3', '4', '加时2完',
                   '1', '2', '3', '4', '加时3完', '1', '2', '3', '4', '加时4完']
    ylabels = ['-50', '-40', '-30', '-20', '-10', '0', '10', '20', '30', '40', '50']
    for sub in range(3):
        ax[sub].set_xticks(np.arange(0, 828, 12))
        ax[sub].set_yticks(np.arange(-50, 60, 10))
        ax[sub].set_yticklabels(ylabels, fontsize=18)
        ax[sub].xaxis.grid(True, linestyle='--', color='#D3D3D3')
        ax[sub].yaxis.grid(True, linestyle='--', color='#D3D3D3')
        a = ax[sub].get_ygridlines()[5]
        a.set_linestyle('-')
        a.set_linewidth(2)
        a = ax[sub].get_xgridlines()
        b = [a[12], a[24], a[36], a[48], a[53], a[58], a[63]]
        for c in b:
            c.set_linestyle('-')
            c.set_linewidth(2)
        ax[sub].set_ylabel('分差', fontsize=30)
        axis = ['top', 'bottom', 'left', 'right']
        for axi in axis:
            ax[sub].spines[axi].set_visible(True)
            ax[sub].spines[axi].set_color('black')
        ax[sub].label_outer()
    ax[0].set_xticklabels([])
    ax[1].set_xticklabels([])
    ax[2].set_xticklabels(xlabels, fontsize=18)
    thres = [30, 30, 5]
    for sub in range(3):
        cur_ax = plt.gca()
        ppmin = pct_sort[sub][0][0]
        ppmax = pct_sort[sub][-1][0]
        factor = 99/(ppmax-ppmin)
        for square in pct_sort[sub]:
            alpha = 0.9 * int(square[-1].split('/')[1]) / thres[sub]
            if alpha < 0.1:
                alpha = 0.1
            elif alpha > 0.9:
                alpha = 0.9
            xx = square[1].split(',')[0]
            minute, second = [int(x) for x in [xx[:-5], xx[-4:-2]]]
            xx = (60*minute+second)/5
            yy = float(square[2].split(',')[0])
            width = square[1].split(',')[1]
            minute, second = [int(x) for x in [width[:-5], width[-4:-2]]]
            width = (60*minute+second)/5 - xx
            height = float(square[2].split(',')[1]) - float(square[2].split(',')[0])
            pp = round(99 - (square[0]-ppmin)*factor)//2
            facecolor = [B[pp]/255, G[pp]/255, R[pp]/255]
            ax[sub].add_artist(plt.Rectangle(xy=(xx, yy), width=width, height=height,
                                                fill=True, facecolor=facecolor,
                                                linewidth=0.5, alpha=alpha))
            if int(square[-1].split('/')[1]) > thres[sub]:
                ax[sub].text(xx+0.3*width, yy+0.3*height, square[-1], fontsize = 8)
    ax[0].set_title('罚球', fontsize=30)
    ax[1].set_title('两分', fontsize=30)
    ax[2].set_title('三分', fontsize=30)
    ax[2].set_xlabel('比赛时长', fontsize=30)
    fig.subplots_adjust(hspace=0.08)
    fig.suptitle(i[0], fontsize=36)
    plt.savefig('./%sResults/playerGameScoreDistribution/%s_%s_color.jpg' % (regularOrPlayoffs[regularOrPlayoff], i[0], i[1]), dpi = 200)
    plt.close('all')
    
    print('\tDone')
