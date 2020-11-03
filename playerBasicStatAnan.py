import pickle
import matplotlib.pyplot as plt
import numpy as np
from pylab import mpl
# 设置字体
mpl.rcParams['font.sans-serif'] = ['SimHei']

englishName = 'KobeBryant'
regularOrPlayoff = 'regular'  # 'regular' or 'playoff'

ROP = '常规赛' if regularOrPlayoff == 'regular' else '季后赛'

f = open('./data/%s/%sGames/%sGameBasicStat.pickle' % (englishName, regularOrPlayoff, regularOrPlayoff), 'rb')
basicStat = pickle.load(f)
f.close()


gameNum = 0
pts = []
for season in basicStat:
    colName = season[0]
    seasonGames = season[1:]
    gameNum += len(seasonGames)
    ptsIndex = colName.index('PTS')
    pts += [int(x[ptsIndex]) for x in seasonGames]

gameNum = list(range(gameNum))
averagePts = np.mean(pts)
plt.plot(gameNum, pts, color='blue', label='每场比赛得分')
plt.plot(gameNum, [10] * len(gameNum), color='red', label='得分上双线 10')
plt.plot(gameNum, [averagePts] * len(gameNum), color='green', label='生涯场均得分 %.2f' % averagePts)
plt.legend(loc='upper left')
plt.title('%s%s生涯数据统计' % (englishName, ROP))
plt.show()
