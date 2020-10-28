from klasses.Game import Game
from klasses.miscellaneous import MPTime
from windows.tools import GameDetailEditor
from util import writeToPickle
from tqdm import tqdm
import os
import time
import numpy as np
np.set_printoptions(suppress=True)

regularOrPlayoffs = ['regular', 'playoffs']
# 分赛季统计变量
count_games_all = {}    # 总比赛数
count_stls_all = {}    # 总抢断数
count_stl_time_all = {}    # 抢断后直至下一次球权转换间隔总时间
average_stl_time_all = {}    # 抢断后直至下一次球权转换间隔平均时间
count_score_all = {}    # 球权间隔时间内创造的总得分
average_score_all = {}    # 球权间隔时间内创造的平均得分
# key: value
# ——>
# 'player name': [[0总抢断数, 1平均间隔时间, 2创造总得分, 3{'TOV': 0}（抢断后球队失误率）, 4通过抢断得分,
#                  5[0球队两分进, 1球队两分出手, 2球队三分进, 3球队三分出手],
#                  6[0球员两分进, 1球员两分出手, 2球员三分进, 3球员三分出手],
#                  {赛季: [总抢断数, 平均间隔时间, 创造总得分, {'TOV': 0}（抢断后球队失误率）, 通过抢断得分]}]]
plyrs = {}
exchange_plays = []
MSerror = 0


def new_player(pm, ss):
    if pm not in plyrs:  # 新建球员统计
        plyrs[pm] = [[0, MPTime('0:00.0'), 0, {'TOV': 0}, 0, [0, 0, 0, 0], [0, 0, 0, 0], {}],
                     [0, MPTime('0:00.0'), 0, {'TOV': 0}, 0, [0, 0, 0, 0], [0, 0, 0, 0], {}]]
    if ss not in plyrs[pm][i][-1]:  # 新建球员赛季统计
        plyrs[pm][i][-1][ss] = [0, MPTime('0:00.0'), 0, {'TOV': 0}, 0, [0, 0, 0, 0], [0, 0, 0, 0]]


for season in range(1996, 2020):
    count_games = [0, 0]  # 0reg1plf
    count_stls = np.zeros((2, 2, 9))  # 0reg1plf    0客场球队1主场球队    0总1第一节2第二节3第三节4第四节5678
    count_stl_time = [[[MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'),
                        MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')],
                       [MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'),
                        MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')]],
                      [[MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'),
                        MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')],
                       [MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'),
                        MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')]]]
    average_stl_time = [[['', '', '', '', '', '', '', '', ''],
                         ['', '', '', '', '', '', '', '', '']],
                        [['', '', '', '', '', '', '', '', ''],
                         ['', '', '', '', '', '', '', '', '']]]
    count_score = np.zeros((2, 2, 9))
    ss = '%d_%d' % (season, season + 1)
    # print(ss)
    for i in range(2):    # 分别统计常规赛、季后赛
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gm in tqdm(gms):
            count_games[i] += 1
            # print('\t\t\t' + gm)
            game = Game(gm[:-7], regularOrPlayoffs[i])
            gameplyrs = game.teamplyrs()
            _, _, _, record = game.game_scanner(gm[:-7])
            zoom = 0
            bp = -1
            pm = ''
            for rec in record:
                if zoom:    # 处于抢断观察期内
                    if 'MK' in rec:    # 统计创造得分
                        # 球队得分
                        plyr_side = 0 if pm in gameplyrs[0] else 1
                        count_score[i][rec['BP']][0] += rec['MK'][1]
                        count_score[i][rec['BP']][rec['Q'] + 1] += rec['MK'][1]
                        plyrs[pm][i][2] += rec['MK'][1]
                        plyrs[pm][i][-1][ss][2] += rec['MK'][1]
                        if rec['MK'][1] == 2:
                            plyrs[pm][i][5][0] += 1
                            plyrs[pm][i][5][1] += 1
                            plyrs[pm][i][-1][ss][5][0] += 1
                            plyrs[pm][i][-1][ss][5][1] += 1
                        elif rec['MK'][1] == 3:
                            plyrs[pm][i][5][2] += 1
                            plyrs[pm][i][5][3] += 1
                            plyrs[pm][i][-1][ss][5][2] += 1
                            plyrs[pm][i][-1][ss][5][3] += 1
                        # 球员得分
                        sp = rec['MK'][0]
                        if sp in gameplyrs[plyr_side]:
                            new_player(sp, ss)
                            plyrs[sp][i][4] += rec['MK'][1]
                            plyrs[sp][i][-1][ss][4] += rec['MK'][1]
                            if rec['MK'][1] == 2:
                                plyrs[sp][i][6][0] += 1
                                plyrs[sp][i][6][1] += 1
                                plyrs[sp][i][-1][ss][6][0] += 1
                                plyrs[sp][i][-1][ss][6][1] += 1
                            elif rec['MK'][1] == 3:
                                plyrs[sp][i][6][2] += 1
                                plyrs[sp][i][6][3] += 1
                                plyrs[sp][i][-1][ss][6][2] += 1
                                plyrs[sp][i][-1][ss][6][3] += 1
                    elif 'MS' in rec:
                        # 球队投失
                        plyr_side = 0 if pm in gameplyrs[0] else 1
                        if rec['MS'][1] == 2:
                            plyrs[pm][i][5][1] += 1
                            plyrs[pm][i][-1][ss][5][1] += 1
                        elif rec['MS'][1] == 3:
                            plyrs[pm][i][5][3] += 1
                            plyrs[pm][i][-1][ss][5][3] += 1
                        # 球员投失
                        sp = rec['MS'][0]
                        if sp in gameplyrs[plyr_side]:
                            new_player(sp, ss)
                            if rec['MS'][1] == 2:
                                plyrs[sp][i][6][1] += 1
                                plyrs[sp][i][-1][ss][6][1] += 1
                            elif rec['MS'][1] == 3:
                                plyrs[sp][i][6][3] += 1
                                plyrs[sp][i][-1][ss][6][3] += 1
                if bp != -1 and rec['BP'] != bp:    # 球权转换，统计球权间隔时间、球权转换方式，zoom置为0，bp置为-1
                    zoom = 0
                    interval = MPTime(rec['T']) - stl_time
                    # print(rec['T'], stl_time, interval, gm)
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
                    count_stl_time[i][rec['BP']][0] += interval
                    count_stl_time[i][rec['BP']][rec['Q'] + 1] += interval
                    plyrs[pm][i][1] += interval
                    plyrs[pm][i][-1][ss][1] += interval
                    if 'TOV' in rec:
                        plyrs[pm][i][3]['TOV'] += 1
                        plyrs[pm][i][-1][ss][3]['TOV'] += 1
                    bp = -1
                    pm = ''
                    exchange_plays = list(set(exchange_plays + list(rec.keys())))

                if 'TOV' in rec and 'STL' in rec:    # 抢断次数+1，zoom置为1，bp置为当前球权方
                    zoom = 1
                    stl_time = MPTime(rec['T'])
                    bp = rec['BP']
                    count_stls[i, rec['BP'], 0] += 1    # 主客场
                    count_stls[i, rec['BP'], rec['Q'] + 1] += 1    # 节次
                    # 分球员记录
                    pm = rec['STL']
                    new_player(pm, ss)
                    plyrs[pm][i][0] += 1
                    plyrs[pm][i][-1][ss][0] += 1
                    # if pm == 'jamesle01':
                    #     print(rec)

    for i in range(2):    # 计算球权间隔时间均值
        for j in range(2):
            for k in range(9):
                if count_stls[i][j][k] > 0:
                    average_stl_time[i][j][k] = count_stl_time[i][j][k].average_acc(count_stls[i][j][k])
    # 计算抢断平均得分
    average_score = np.around(count_score / count_stls, decimals=3)
    # time.sleep(2)
    # print(ss)
    # for i in range(2):
    #     print('季后赛' if i else '常规赛')
    #     print('总场次')
    #     print(count_games[i])
    #     for j in range(2):
    #         print('主场球队' if j else '客场球队')
    #         print('总抢断数')
    #         print(count_stls[i][j])
    #         print('抢断后球权掌控总时间')
    #         print(count_stl_time[i][j])
    #         print('抢断后球权掌控平均时间')
    #         print(average_stl_time[i][j])
    #         print('抢断后得分')
    #         print(count_score[i][j])
    #         print('每次抢断后平均得分')
    #         print(average_score[i][j])
    #         print()

    count_games_all[ss] = count_games
    count_stls_all[ss] = count_stls
    count_stl_time_all[ss] = count_stl_time
    average_stl_time_all[ss] = average_stl_time
    count_score_all[ss] = count_score
    average_score_all[ss] = average_score

#%%
games = [0, 0]
stls = [0, 0]
stl_time = [MPTime('0:00.0'), MPTime('0:00.0')]
ave_stl_time = ['', '']
score = [0, 0]
ave_score = [0, 0]
for s in count_games_all:
    for i in range(2):
        games[i] += count_games_all[s][i]
        stls[i] += (count_stls_all[s][i][0][0] + count_stls_all[s][i][1][0])
        stl_time[i] += (count_stl_time_all[s][i][0][0] + count_stl_time_all[s][i][1][0])
        score[i] += (count_score_all[s][i][0][0] + count_score_all[s][i][1][0])
for i in range(2):
    ave_stl_time[i] = stl_time[i].average_acc(stls[i])
    ave_score[i] = score[i] / stls[i]
    
print(games)
print(stls)
print(stl_time)
print(ave_stl_time)
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
writeToPickle('./data/playerStealEnforce.pickle', plyrs)
