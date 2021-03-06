import pickle
import numpy as np
from PIL import Image
import os
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from util import gameMarkToDir, minusMinutes, playerClutchScoreDistribution, addMinutes, writeToExcel
from pylab import *
from tqdm import tqdm

regularOrPlayoffs = ['regular', 'playoff']
HomeOrAts = [[4, 5], [2, 1]]    # 主，客
colors = [['#004BE8', '#3FAF50', '#FF4500'],    # 得分
          ['#99EAEA', '#A4FF99', '#FFC0CB']]    # 失手

f = open('./data/playerBasicInformation.pickle', 'rb')
playerInf = pickle.load(f)
f.close()
players = []
for i in playerInf[1:]:
    playerName, playerMark = i[0], i[1].split('/')[-1].rstrip('.html')
    playerName = playerName.replace(' ', '')
    playerName = playerName.replace('-', '')
    if i[2] and i[3]:
        if int(i[6]) >= 1997 and os.path.exists('./data/players/%s' % playerMark):
            players.append([playerName, playerMark])

ROP = regularOrPlayoffs[1]
diffPlus = 5
diffMinus = -5
lastMins = '5:00.0'
clutch = []
for i in tqdm(players):
    # print("starting analysing %s's games ..." % i[0], end='')
    playerFileDir = './data/players/' + i[1] + '/%sGames/%sGameBasicStat.pickle' % (ROP, ROP)
    if os.path.exists(playerFileDir):
        res = playerClutchScoreDistribution(i[0], i[1], HomeOrAts, diffPlus, diffMinus, lastMins, ROP)
        if res[-3]:
            clutch.append(res)
    # print('\tDone')
clutch.sort(reverse=True)
#%%
thres = 0
for i in clutch:
    if i[13]> thres:
        thres = i[13]
thres *= 0.4
clutch_ = []
for c in clutch:
    if c[13] >= thres:
        clutch_.append(c)
#%%
writeToExcel('clutch.xls', 
             'score\tplayer\tfreeThrowPct\tfreeThrowMade\tfreeThrowAttempts\ttwoPtPct\ttwoPtMade\ttwoPtAttempts\tthreePtPct\tthreePtMade\tthreePtAttempts\tfieldGoalPct\tfieldGoalMade\tfieldGoalAttempts\teFG%\tTS%\n',
             clutch)
writeToExcel('clutch_.xls', 
             'score\tplayer\tfreeThrowPct\tfreeThrowMade\tfreeThrowAttempts\ttwoPtPct\ttwoPtMade\ttwoPtAttempts\tthreePtPct\tthreePtMade\tthreePtAttempts\tfieldGoalPct\tfieldGoalMade\tfieldGoalAttempts\teFG%\tTS%\n',
             clutch_)




















                        