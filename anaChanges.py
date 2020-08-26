import pickle
import os
import re
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib as mpl
from util import LoadPickle
mpl.rcParams['font.sans-serif'] = ['STXinwei']
regularOrPlayoffs = ['regular', 'playoff']
regularOrPlayoff = 0

#%%
# 0输1赢2总；0全部1投中2投失3全部两分4投中5投失6全部三分7投中8投失
numGames = []
cnt = np.zeros((24, 4, 3, 9))
dis = np.zeros((24, 4, 3, 9))
score = np.zeros((24, 2))

for n, season in enumerate(range(1996, 2020)):
    gameDir = './data/seasons_shot/%d_%d/%s/' % (season, season+1, regularOrPlayoffs[regularOrPlayoff])
    upROP = regularOrPlayoffs[regularOrPlayoff][0].upper() + regularOrPlayoffs[regularOrPlayoff][1:]
    summaryDir = './data/seasons/%d_%d/season%sSummary.pickle' % (season, season+1, upROP)
    summary = LoadPickle(summaryDir)
    numGames.append(len(summary)-1)
    print('starting to analysing season %s-%s:' % (season, season+1))
    
    for game in tqdm(summary[1:]):
        f = open(gameDir + game[0] + '_shot.pickle', 'rb')
        c = pickle.load(f)
        f.close()
        if season < 2000:
            win = 0 if int(game[2]) > int(game[4]) else 1
            score[n][0] += min(int(game[2]), int(game[4]))
            score[n][1] += max(int(game[2]), int(game[4]))
        else:
            win = 0 if int(game[3]) > int(game[5]) else 1
            score[n][0] += min(int(game[3]), int(game[5]))
            score[n][1] += max(int(game[3]), int(game[5]))
        assert len(c) == 2
        for i in range(2):
            index = int(i == win)
            # print(index)
            for disc in c[i]:
                shoot = disc[1]
                d = int(re.match( r'(.*) ft(.*?) .*', shoot, re.M|re.I).group(1).split(' ')[-1])
                m = 1 if '2-pointer' in shoot else 2
                mm = 1 if 'made' in shoot else 2
                qtr = int(shoot[0][0]) - 1
                
                dis[n][qtr][2][0] += d
                dis[n][qtr][2][mm] += d
                dis[n][qtr][2][m*3] += d
                dis[n][qtr][2][m*3+mm] += d
                cnt[n][qtr][2][0] += 1
                cnt[n][qtr][2][mm] += 1
                cnt[n][qtr][2][m*3] += 1
                cnt[n][qtr][2][m*3+mm] += 1
                
                dis[n][qtr][index][0] += d
                dis[n][qtr][index][mm] += d
                dis[n][qtr][index][m*3] += d
                dis[n][qtr][index][m*3+mm] += d
                cnt[n][qtr][index][0] += 1
                cnt[n][qtr][index][mm] += 1
                cnt[n][qtr][index][m*3] += 1
                cnt[n][qtr][index][m*3+mm] += 1

#%%
plt.figure(figsize=(10,5))
xlabels = ['96-97', '97-98', '98-99', '99-00', '00-01', '01-02', '02-03', '03-04', '04-05', '05-06', '06-07', '07-08',
           '08-09', '09-10', '10-11', '11-12', '12-13', '13-14', '14-15', '15-16', '16-17', '17-18', '18-19', '19-20']
labels = ['lose', 'win']
for i in range(2):
    plt.plot(list(range(24)), score[:, i]/np.array(numGames), label=labels[i])
plt.xticks(list(range(24)), xlabels, rotation=45)
plt.legend()
plt.title('球队场均得分')
plt.show()
plt.close()

plt.figure(figsize=(10,5))
labels = ['2-pointer', '3-pointer']
plt.plot(list(range(24)), np.sum(cnt[:, :, i, 3], axis=1)/np.array(numGames), label=labels[0])
plt.plot(list(range(24)), np.sum(cnt[:, :, i, 6], axis=1)/np.array(numGames), label=labels[1])
plt.xticks(list(range(24)), xlabels, rotation=45)
plt.legend()
plt.title('球队场均出手次数')
plt.show()
plt.close()



#%%
# 比赛双方总得分中，1、2、3分得分占比
index = list(range(24))
fig, axs = plt.subplots(2, 3, figsize=(40,15))

for i in range(3):
    pointer2 = 2 * np.sum(cnt[:, :, i, 4], axis=1)
    pointer3 = 3 * np.sum(cnt[:, :, i, 7], axis=1)
    if i == 2:
        pointer1 = (np.sum(score, axis=1) - pointer2 - pointer3)
    else:
        pointer1 = score[:, i] - pointer2 - pointer3
    pointer1 = pointer1 / np.array(numGames)
    pointer2 = pointer2 / np.array(numGames)
    pointer3 = pointer3 / np.array(numGames)

    axs[0][i].bar(index, pointer1, width=0.4, label= '1-pointer')
    axs[0][i].bar(index, pointer2, width=0.4, bottom=pointer1, label= '2-pointer')
    axs[0][i].bar(index, pointer3, width=0.4, bottom=pointer2+pointer1, label= '3-pointer')
    if i < 2:
        axs[0][i].set_ylim(0, 121)
    else:
        axs[0][i].set_ylim(0, 251)
    axs[0][i].set_xticks(index)
    axs[0][i].set_xticklabels(xlabels, rotation=45)
    axs[0][i].legend(loc='upper left',  shadow=True)
    
    summ = pointer1 + pointer2 + pointer3
    percentage1 = pointer1 / summ
    percentage2 = pointer2 / summ
    percentage3 = pointer3 / summ
    print(percentage1, percentage2, percentage3)
    
    axs[1][i].bar(index, percentage1, width=0.4, label= '1-pointer')
    axs[1][i].bar(index, percentage2, width=0.4, bottom=percentage1, label= '2-pointer')
    axs[1][i].bar(index, percentage3, width=0.4, bottom=percentage1+percentage2, label= '3-pointer')
    axs[1][i].set_xticks(index)
    axs[1][i].set_xticklabels(xlabels, rotation=45)

# plt.savefig('9.tiff', dpi=300)
plt.show()































