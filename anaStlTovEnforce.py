from klasses.Game import Game
from klasses.miscellaneous import MPTime
from windows.tools import GameDetailEditor
from util import writeToPickle, gameMarkToDir, LoadPickle
from tqdm import tqdm
import os
import time
import numpy as np
np.set_printoptions(suppress=True)

regularOrPlayoffs = ['regular', 'playoffs']
# 分赛季统计变量
count_games_all = {}    # 总比赛数
count_item_all = {}    # 总次数
count_time_all = {}    # 抢断/失误发生后直至下一次球权转换间隔总时间
average_time_all = {}    # 抢断/失误发生后直至下一次球权转换间隔平均时间
count_score_all = {}    # 球队在球权转换前创造的总得分
average_score_all = {}    # 球队在球权转换前创造的平均得分
# key: value
# ——>
# 'player name': [[0总次数, 1平均间隔时间, 2创造总得分, 3{'TOV': 0}（抢断/失误发生后球队失误率）, 4通过抢断/失误得分,
#                  5[0球队罚球进, 1球队罚球出手, 2球队两分进, 3球队两分出手, 4球队三分进, 5球队三分出手],
#                  6[0球员罚球进, 1球员罚球出手, 2球员两分进, 3球员两分出手, 4球员三分进, 5球员三分出手],
#                  {赛季: [总次数, 平均间隔时间, 创造总得分, {'TOV': 0}（抢断/失误发生后球队失误率）, 通过抢断/失误得分]}]]
plyrs = {}
exchange_plays = []
MSerror = 0
tar_item = 0    # 0抢断1失误
tartext = ['Steal', 'Turnover']
sentence = "'TOV' in rec and rec['plyr'] != 'Team' and rec['plyr'] != ''" if tar_item else "'TOV' in rec and 'STL' in rec"


def new_player(pm, ss):
    if pm not in plyrs:  # 新建球员统计
        plyrs[pm] = [[0, MPTime('0:00.0'), 0, {'TOV': 0}, 0, [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], {}],
                     [0, MPTime('0:00.0'), 0, {'TOV': 0}, 0, [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], {}]]
    if ss not in plyrs[pm][i][-1]:  # 新建球员赛季统计
        plyrs[pm][i][-1][ss] = [0, MPTime('0:00.0'), 0, {'TOV': 0}, 0, [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]


for season in range(1996, 2020):
    count_games = [0, 0]  # 0reg1plf
    count_item = np.zeros((2, 3, 9))  # 0reg1plf    0客场球队1主场球队2总    0总1第一节2第二节3第三节4第四节5f加时6s加时7t加时8f加时
    count_time = [[[MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')],
                   [MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')],
                   [MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')]],
                  [[MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')],
                   [MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')],
                   [MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')]]]
    average_time = [[['', '', '', '', '', '', '', '', ''], ['', '', '', '', '', '', '', '', ''], ['', '', '', '', '', '', '', '', '']],
                    [['', '', '', '', '', '', '', '', ''], ['', '', '', '', '', '', '', '', ''], ['', '', '', '', '', '', '', '', '']]]
    count_score = np.zeros((2, 3, 9))
    ss = '%d_%d' % (season, season + 1)
    # print(ss)
    for i in range(2):    # 分别统计常规赛、季后赛
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gm in tqdm(gms):
            count_games[i] += 1
            # print('\t\t\t' + gm)
            game = Game(gm[:-7], regularOrPlayoffs[i])
            gameplyrs = game.teamplyrs()
            record = LoadPickle(gameMarkToDir(gm[:-7], regularOrPlayoffs[i], tp=3))
            # _, _, _, record = game.game_scanner(gm[:-7])
            zoom = 0
            bp = -1
            pm = ''
            for rec in record:
                if zoom:    # 处于抢断/失误观察期内
                    # 出现得失分
                    if 'MK' in rec or 'MS' in rec:
                        GoM = 1 if 'MK' in rec else 0
                        KoS = 'MK' if GoM else 'MS'
                        # 球队得失分
                        plyr_side = 0 if pm in gameplyrs[0] else 1
                        if tar_item:
                            plyr_side = 0 if plyr_side else 1
                        s = rec[KoS][1]
                        plyrs[pm][i][5][(s - 1) * 2 + 1] += 1
                        plyrs[pm][i][-1][ss][5][(s - 1) * 2 + 1] += 1
                        if GoM:
                            count_score[i][2][0] += s
                            count_score[i][rec['BP']][0] += s
                            count_score[i][2][rec['Q'] + 1] += s
                            count_score[i][rec['BP']][rec['Q'] + 1] += s
                            plyrs[pm][i][2] += s
                            plyrs[pm][i][-1][ss][2] += s
                            plyrs[pm][i][5][(s - 1) * 2] += 1
                            plyrs[pm][i][-1][ss][5][(s - 1) * 2] += 1
                        # 球员得失分
                        sp = rec[KoS][0]
                        if sp in gameplyrs[plyr_side]:
                            new_player(sp, ss)
                            plyrs[sp][i][6][(s - 1) * 2 + 1] += 1
                            plyrs[sp][i][-1][ss][6][(s - 1) * 2 + 1] += 1
                            if GoM:
                                plyrs[sp][i][4] += s
                                plyrs[sp][i][-1][ss][4] += s
                                plyrs[sp][i][6][(s - 1) * 2] += 1
                                plyrs[sp][i][-1][ss][6][(s - 1) * 2] += 1
                # 球权转换，统计球权间隔时间、球权转换方式，zoom置为0，bp置为-1
                if bp != -1 and rec['BP'] != bp:
                    zoom = 0
                    interval = MPTime(rec['T']) - happen_time
                    # print(rec['T'], happen_time, interval, gm)
                    # ['PVL', 'MK', 'ORB', 'TOV', 'DRB', 'TVL', 'D3S', 'JB', 'FF1', 'FF2', 'PF']
                    if 'MS' in rec or 'TF' in rec or 'D3S' in rec or 'ORB' in rec:
                        print('MS TF D3S ORB')
                        MSerror += 1
                        print(ss, gm, rec)
                        # qtr = int(rec['Q']) + 1
                        # now = MPTime(rec['T'])
                        # qtr_end = '%d:00.0' % (qtr * 12)
                        # now = MPTime(qtr_end) - now
                        # playbyplay_editor_window = GameDetailEditor(gm=gm[:-7],
                        #                                             title='第%d节 剩余%s    %s' % (qtr, now, str(rec)))
                        # playbyplay_editor_window.loop()
                        interval = MPTime('0:00.0')
                        plyrs[pm][i][3]['TOV'] += 1
                        plyrs[pm][i][-1][ss][3]['TOV'] += 1
                    count_time[i][2][0] += interval
                    count_time[i][rec['BP']][0] += interval
                    count_time[i][2][rec['Q'] + 1] += interval
                    count_time[i][rec['BP']][rec['Q'] + 1] += interval
                    plyrs[pm][i][1] += interval
                    plyrs[pm][i][-1][ss][1] += interval
                    if 'TOV' in rec:
                        plyrs[pm][i][3]['TOV'] += 1
                        plyrs[pm][i][-1][ss][3]['TOV'] += 1
                    bp = -1
                    pm = ''
                    exchange_plays = list(set(exchange_plays + list(rec.keys())))
                # 抢断/失误次数+1，zoom置为1，bp置为当前球权方
                if eval(sentence):
                    zoom = 1
                    happen_time = MPTime(rec['T'])
                    bp = rec['BP']
                    count_item[i, 2, 0] += 1
                    count_item[i, rec['BP'], 0] += 1    # 主客场
                    count_item[i, 2, rec['Q'] + 1] += 1
                    count_item[i, rec['BP'], rec['Q'] + 1] += 1    # 节次
                    # 分球员记录
                    pm = rec['plyr'] if tar_item else rec['STL']
                    if pm[-1] == ')':
                        print(gm, rec)
                    new_player(pm, ss)
                    plyrs[pm][i][0] += 1
                    plyrs[pm][i][-1][ss][0] += 1
                    # if pm == 'jamesle01':
                    #     print(rec)
    for i in range(2):    # 计算球权间隔时间均值
        for j in range(3):
            for k in range(9):
                if count_item[i][j][k] > 0:
                    average_time[i][j][k] = count_time[i][j][k].average_acc(count_item[i][j][k])
    # 计算抢断/失误平均得分
    average_score = np.around(count_score / count_item, decimals=3)
    # time.sleep(2)
    # print(ss)
    # for i in range(2):
    #     print('季后赛' if i else '常规赛')
    #     print('总场次')
    #     print(count_games[i])
    #     for j in range(2):
    #         print('主场球队' if j else '客场球队')
    #         print('总抢断数')
    #         print(count_item[i][j])
    #         print('抢断后球权掌控总时间')
    #         print(count_time[i][j])
    #         print('抢断后球权掌控平均时间')
    #         print(average_time[i][j])
    #         print('抢断后得分')
    #         print(count_score[i][j])
    #         print('每次抢断后平均得分')
    #         print(average_score[i][j])
    #         print()

    count_games_all[ss] = count_games
    count_item_all[ss] = count_item
    count_time_all[ss] = count_time
    average_time_all[ss] = average_time
    count_score_all[ss] = count_score
    average_score_all[ss] = average_score

#%%
games = [0, 0]
items = [0, 0]
item_time = [MPTime('0:00.0'), MPTime('0:00.0')]
ave_item_time = ['', '']
score = [0, 0]
ave_score = [0, 0]
for s in count_games_all:
    for i in range(2):
        games[i] += count_games_all[s][i]
        items[i] += (count_item_all[s][i][0][0] + count_item_all[s][i][1][0])
        item_time[i] += (count_time_all[s][i][0][0] + count_time_all[s][i][1][0])
        score[i] += (count_score_all[s][i][0][0] + count_score_all[s][i][1][0])
for i in range(2):
    ave_item_time[i] = item_time[i].average_acc(items[i])
    ave_score[i] = score[i] / items[i]
    
print(games)
print(items)
print(item_time)
print(ave_item_time)
print(score)
print(ave_score)

# [28317, 1933]
# [435372.0, 27686.0]
# [68541:22.2, 4634:40.1]
# ['0:9.4', '0:10.0']
# [538495.0, 33785.0]
# [1.2368618101301876, 1.2202918442534132]

for pm in plyrs:
    for i in range(2):
        if plyrs[pm][i][0]:
            plyrs[pm][i][1] = plyrs[pm][i][1].average_acc(plyrs[pm][i][0])
            # plyrs[pm][i][2] /= plyrs[pm][i][0]
            plyrs[pm][i][3]['TOV'] /= plyrs[pm][i][0]
        for ss in plyrs[pm][i][-1]:
            if plyrs[pm][i][-1][ss][0]:
                plyrs[pm][i][-1][ss][1] = plyrs[pm][i][-1][ss][1].average_acc(plyrs[pm][i][-1][ss][0])
                # plyrs[pm][i][-1][ss][2] /= plyrs[pm][i][-1][ss][0]
                plyrs[pm][i][-1][ss][3]['TOV'] /= plyrs[pm][i][-1][ss][0]

print('共%d名球员' % len(plyrs))
# for pm in plyrs:
#     print(pm, plyrs[pm])

print(exchange_plays)
print(MSerror)
writeToPickle('./data/Enforce/player%sEnforce.pickle' % tartext[tar_item], plyrs)
writeToPickle('./data/Enforce/season%sEnforceRecord.pickle' % tartext[tar_item], [count_games_all, count_item_all, count_time_all,
                                                                                  average_time_all, count_score_all, average_score_all])
