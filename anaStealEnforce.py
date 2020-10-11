from klasses.Game import Game
from klasses.miscellaneous import MPTime
from tqdm import tqdm
import os
import time
import numpy as np
np.set_printoptions(suppress=True)


regularOrPlayoffs = ['regular', 'playoffs']
count_games_all = {}
count_stls_all = {}
count_stl_time_all = {}
average_stl_time_all = {}
count_score_all = {}
average_score_all = {}
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
    for i in range(2):
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gm in tqdm(gms):
            count_games[i] += 1
            # print('\t\t\t' + gm)
            game = Game(gm[:-7], regularOrPlayoffs[i])
            _, _, _, record = game.game_scanner(gm[:-7])
            zoom = 0
            bp = -1
            for rec in record:
                if zoom:
                    if 'MK' in rec:
                        count_score[i][rec['BP']][0] += rec['MK'][1]
                        count_score[i][rec['BP']][rec['Q'] + 1] += rec['MK'][1]
                if bp != -1 and rec['BP'] != bp:
                    zoom = 0
                    interval = MPTime(rec['T']) - stl_time
                    # print(rec['T'], stl_time, interval, gm)
                    count_stl_time[i][rec['BP']][0] += interval
                    count_stl_time[i][rec['BP']][rec['Q'] + 1] += interval
                    bp = -1
                if 'TOV' in rec and 'STL' in rec:
                    zoom = 1
                    stl_time = MPTime(rec['T'])
                    bp = rec['BP']
                    count_stls[i, rec['BP'], 0] += 1    # 主客场
                    count_stls[i, rec['BP'], rec['Q'] + 1] += 1    # 节次

    for i in range(2):
        for j in range(2):
            for k in range(9):
                if count_stls[i][j][k] > 0:
                    average_stl_time[i][j][k] = count_stl_time[i][j][k].average_acc(count_stls[i][j][k])

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

# [28317, 1932]
# [435372.0, 27677.0]
# [68530:36.9, 4631:52.9]
# ['0:9.4', '0:10.0']
# [538397.0, 33743.0]
# [1.2366367152687816, 1.2191711529428768]




# gm = '202009300LAL'
# game = Game(gm, 'playoffs')
# _, _, _, record = game.game_scanner(gm)
# for i in record:
#     print(i)
# game.game_analyser(gm, record)
# game.pace(gm, record)
