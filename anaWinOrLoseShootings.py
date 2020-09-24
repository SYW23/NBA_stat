import pickle
import os
import re
import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
from util import LoadPickle, notEarlierThan


def findPlayerName(playerMark, allPlayers):
    for i in allPlayers[1:]:
        if i[1].split('/')[-1].rstrip('.html') == playerMark:
            return i[0]


def diffBeforeScore(play):
    [atTeamScore, homeTeamScore] = [int(x) for x in play[3].split('-')]
    if play[2]:
        s = int(play[2])
        if s >= 4:
            if 'free throw' in play[1]:
                score = 1
            elif '2-pt' in play[1]:
                score = 2
            elif '3-pt' in play[1]:
                score = 3
        return (atTeamScore - s) - homeTeamScore
    elif play[4]:
        s = int(play[4])
        if s >= 4:
            if 'free throw' in play[5]:
                score = 1
            elif '2-pt' in play[5]:
                score = 2
            elif '3-pt' in play[5]:
                score = 3
        return atTeamScore - (homeTeamScore - s)
    else:
        return atTeamScore - homeTeamScore


f = open('./data/playerBasicInformation.pickle', 'rb')
allPlayers = pickle.load(f)
f.close()

regularOrPlayoffs = ['regular', 'playoff']
regularOrPlayoff = 1
# player = {'playerMark':np.zeros((1, 16))}
# 0全部1投中2投失3全部罚球4投中5投失6全部两分7投中8投失9全部三分10投中11投失12助攻两分成功13助攻两分失败14助攻三分成功15助攻三分失败
player = {}
lastSecs = '0:24.0'


for n, season in enumerate(range(1996, 2019)):
    gameDir = './data/seasons/%d_%d/%s/' % (season, season+1, regularOrPlayoffs[regularOrPlayoff])
    if regularOrPlayoff:
        gameDir = gameDir[:-1] + 's/'
    upROP = regularOrPlayoffs[regularOrPlayoff][0].upper() + regularOrPlayoffs[regularOrPlayoff][1:]
    summaryDir = './data/seasons/%d_%d/season%sSummary.pickle' % (season, season+1, upROP)
    summary = LoadPickle(summaryDir)
    print('starting to analysing season %s-%s:' % (season, season+1))
    
    for game in tqdm(summary[1:]):
        c = LoadPickle(gameDir + game[0] + '.pickle')
        for i in range(len(c) - 3):
            for play in c[i+3][::-1]:
                if len(play) == 6:
                    score = -1
                        # 客队/主队比分
                    diff = diffBeforeScore(play)
                    
                    # 落后1~3分、最后n秒内
                    if notEarlierThan(play[0], lastSecs) and diff != 0 and abs(diff) < 4:    # 判断分差与时间是否满足条件
                        trailDisc = play[1 if diff < 0 else 5]
                        
                        if 'misses' in trailDisc:
                            GOM = 2
                            if 'free throw' in trailDisc:
                                score = 1
                            elif '2-pt' in trailDisc:
                                score = 2
                            elif '3-pt' in trailDisc:
                                score = 3
                            else:
                                print('Pointer Error', game[0])
                            # if score == 1:
                                # if 'of 2' in 
                                
                        elif 'makes' in trailDisc:
                            GOM = 1
                            if 'free throw' in trailDisc:
                                score = 1
                            elif '2-pt' in trailDisc:
                                score = 2
                            elif '3-pt' in trailDisc:
                                score = 3
                            else:
                                print('Pointer Error', game[0])
                        
                        if score > 1 and score >= abs(diff):
                            assert score < 4
                            playerMark = trailDisc.split(' ')[0]
                            if playerMark not in player.keys():
                                player[playerMark] = np.zeros((1, 16))
                            player[playerMark][0][0] += 1
                            player[playerMark][0][GOM] += 1
                            player[playerMark][0][score*3] += 1
                            player[playerMark][0][score*3+GOM] += 1
                            # print(play)
                            


#%%
maxFG = 0
for key, value in player.items():
    if value[0][0] > maxFG:
        maxFG = value[0][0]
thres = maxFG * 0

resPlayer = []
for key, value in player.items():
    if value[0][0] > thres:
        name = findPlayerName(key, allPlayers)
        resPlayer.append([name] + list(value[0]))
#%%
df = pd.DataFrame(resPlayer, columns=['球员', '全部', '投中', '投失', '全部罚球', '投中', '投失',
                                      '全部两分', '投中', '投失', '全部三分', '投中', '投失',
                                      '助攻两分成功', '助攻两分失败', '助攻三分成功', '助攻三分失败'], index=None)
df.to_csv('./%sResults/WoLShootings/shootings.csv' % regularOrPlayoffs[regularOrPlayoff], index=None)













        
        