import pickle
import numpy as np
from PIL import Image
import os
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from util import gameMarkToDir, minusMinutes, playerPerformanceWithTime, addMinutes
from pylab import *
mpl.rcParams['font.sans-serif'] = ['STXinwei']    # 解决中文乱码
plt.rcParams['axes.unicode_minus'] = False    # 解决坐标轴符号显示异常
# plt.style.use('ggplot')    # 固定风格绘图
# plt.rcParams['axes.facecolor'] = 'white'    # 背景设置为白色

regularOrPlayoffs = ['regular', 'playoff']
HomeOrAts = [[4, 5], [2, 1]]    # 主，客
colors = ['#FF8C00', '#FF0000', '#FFFF00',    # 分差、得分、前板
          '#000080', '#32CD32', '#FF00FF',    # 后板、篮板、助攻
          '#00BFFF', '#13EAC9', '#7B0323',    # 助攻得分、抢断、盖帽
          '#000000', '#6B7C85', '#C1F80A']    # 失误、犯规、时间

inter = 15
f = open('./data/playerBasicInformation.pickle', 'rb')
playerInf = pickle.load(f)
f.close()
players = []
for i in playerInf[1:]:
    playerName, playerMark = i[0],i[1].split('/')[-1].rstrip('.html')
    playerName = playerName.replace(' ', '')
    playerName = playerName.replace('-', '')
    if i[2] and i[3]:
        if int(i[6]) >= 1997 and os.path.exists('./data/players/%s' % playerMark):
            players.append([playerName, playerMark])

#%%
for i in players[244:245]:
    print("starting analysing %s's games ..." % i[0])
    scoreMethod, statAll = playerPerformanceWithTime(i[0], i[1], HomeOrAts, colors, regularOrPlayoffs[0])
    print('\tDone')












                        