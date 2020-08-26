import pickle
import os
import matplotlib.pyplot as plt
import numpy as np
from math import atan
from pylab import *
from util import *
# mpl.rcParams['font.sans-serif'] = ['SimHei']

f = open('./data/playerBasicInformation.pickle', 'rb')
c = pickle.load(f)
f.close()

counts = []
for games in range(0, 1600, 100):
    minutes = 20 * games
    count = 0
    for i in c[1:]:
        if i[2] and i[3]:
            # if int(i[2]) > games and int(i[3]) > minutes and int(i[6]) >= 1997:
            if int(i[2]) > games and int(i[3]) > minutes:
                count += 1
    counts.append(count)
print(counts)

# =============================================================================
# circles = []
# for i in range(16):
#     circles.append(plt.Circle((i, i), 5 * atan(counts[i] / counts[1]), color=(1, 15*(15-i)/256, 15*(15-i)/256), clip_on=False))
# fig, ax = plt.subplots()
# for i in circles:
#     ax.add_artist(i)
# 
# plt.axis([0, 16, 0, 16])
# plt.xticks(np.arange(0, 16, 1))
# plt.yticks(np.arange(0, 16, 1))
# plt.xlabel('常规赛总出场数(百场)')
# plt.ylabel('常规赛总出场时间(x2000分钟)')
# plt.show()
# =============================================================================


# 共 4800 人，NBA 4144 人，有季后赛经历 2474人
# 常规赛出场数 100+ 时间 5000+：1572 人
# 常规赛出场数 100+ 时间 10000+：1080 人
# 常规赛出场数 200+ 时间 15000+：718 人
# 常规赛出场数 500+ 时间 20000+：463 人
# 常规赛出场数 800+ 时间 20000+：355 人
# 常规赛出场数 1000+ 时间 20000+：132 人
# 常规赛出场数 1200+ 时间 25000+：41 人
# 常规赛出场数 1500+ 时间 30000+：5 人


f = open('./data/playerBasicInformation.pickle', 'rb')
playerInf = pickle.load(f)
f.close()

e = []
dirError = 0
count, maxGames, maxMinutes, aveMinutes = 0, 0, 0, 0
player = []
for index, i in enumerate(playerInf[1:]):
    playerName, playerMark = i[0], i[1].split('/')[-1].rstrip('.html')
    playerName = playerName.replace(' ', '')
    playerName = playerName.replace('-', '')
    playerDir = playerName + '_' + playerMark
    # if i[2] and i[3] and i[4] and i[5]:
    if i[2] and i[3]:
        count += 1
        if int(i[2]) > maxGames:
            maxGames = int(i[2])
        if int(i[3]) > maxMinutes:
            maxMinutes = int(i[3])
        if int(i[3])/int(i[2]) > aveMinutes:
            if int(i[3])/int(i[2]) < 50:
                aveMinutes = int(i[3])/int(i[2])
            else:
                print(i[0])
        # if int(i[7]) >= 1997 and os.path.exists('./data/players/%s' % playerDir):
        if not os.path.exists('./data/players/%s' % playerDir) and '�' not in playerDir:
            dirError += 1
            print(index, playerDir)
            e.append(playerDir)
        if int(i[7]) >= 1997:
            player.append([playerName, playerMark, playerDir])
            
print(count, maxGames, maxMinutes, aveMinutes, dirError)
e.sort()









