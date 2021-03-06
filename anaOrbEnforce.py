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
count_games_all = {}  # 总比赛数
count_item_all = {}  # 总次数
count_time_all = {}    # 首次前板直至下一次球权转换间隔总时间
average_time_all = {}    # 首次前板直至下一次球权转换间隔平均时间
count_score_all = {}  # 球队在球权转换前创造的总得分
average_score_all = {}  # 球队在球权转换前创造的平均得分
# key: value
# ——>
# 'player name': [[0总次数, 1平均间隔时间, 2为球队创造总得分, 3{'TOV': [0球队失误, 1球员失误]}（抢断/失误发生后球队失误率）, 4球员通过抢断/失误得分,
#                  5[0球队罚球进, 1球队罚球出手, 2球队两分进, 3球队两分出手, 4球队三分进, 5球队三分出手],
#                  6[0球员罚球进, 1球员罚球出手, 2球员两分进, 3球员两分出手, 4球员三分进, 5球员三分出手],
#                  {赛季: [总次数, 平均间隔时间, 为球队创造总得分, {'TOV': [球队失误, 球员失误]}（抢断/失误发生后球队失误率）, 球员通过抢断/失误得分]}]]
plyrs = {}
exchange_plays = []
MSerror = 0
tar_item = 0  # 0前板
tartext = ['OffReb']
sentence = "'ORB' in rec and rec['ORB'] != 'Team'"


def new_player(pm, ss):
    if pm not in plyrs:  # 新建球员统计
        plyrs[pm] = [[0, MPTime('0:00.0'), 0, {'TOV': [0, 0]}, 0, [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], {}],
                     [0, MPTime('0:00.0'), 0, {'TOV': [0, 0]}, 0, [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], {}]]
    if ss not in plyrs[pm][i][-1]:  # 新建球员赛季统计
        plyrs[pm][i][-1][ss] = [0, MPTime('0:00.0'), 0, {'TOV': [0, 0]}, 0, [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]


for season in range(1996, 2020):
    count_games = [0, 0]  # 0reg1plf
    count_item = np.zeros((2, 3, 9))  # 0reg1plf    0客场球队1主场球队2总    0总1第一节2第二节3第三节4第四节5f加时6s加时7t加时8f加时
    count_time = [
        [[MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0'), MPTime('0:00.0')],
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
    for i in range(2):  # 分别统计常规赛、季后赛
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gm in tqdm(gms):
            count_games[i] += 1
            tmpms = {}
            pts = [[0, 0, 0], [0, 0, 0]]  # 记录球员抢到进攻篮板后球队得分 0投失1投中    0罚球1两分2三分
            plyr_pts = {}    # 记录球队抢到进攻篮板后球员得分
            flag = 0
            # print('\t\t\t' + gm)
            game = Game(gm[:-7], regularOrPlayoffs[i])
            gameplyrs = game.teamplyrs()
            record = LoadPickle(gameMarkToDir(gm[:-7], regularOrPlayoffs[i], tp=3))
            # _, _, _, record = game.game_scanner(gm[:-7])
            zoom = 0
            bp = -1
            pm = ''
            for rec in record:
                if zoom:  # 处于前板观察期内
                    # 出现得失分
                    if 'MK' in rec or 'MS' in rec:
                        GoM = 1 if 'MK' in rec else 0
                        KoS = 'MK' if GoM else 'MS'
                        plyr_side = 0 if pm in gameplyrs[0] else 1
                        sp = rec[KoS][0]
                        if sp in gameplyrs[plyr_side]:
                            # 球队得失分
                            s = rec[KoS][1]
                            if sp in tmpms:
                                pts[GoM][s - 1] += 1
                            # 球员得失分
                            if sp not in plyr_pts:
                                plyr_pts[sp] = [[0, 0, 0], [0, 0, 0]]
                            plyr_pts[sp][GoM][s - 1] += 1
                    if eval(sentence):    # zoom域内出现前板->同一次进攻连续抢到前场篮板
                        pm = rec['ORB']
                        if pm in tmpms:
                            tmpms[pm][0] += 1
                        else:
                            tmpms[pm] = [1, MPTime(rec['T'])]
                # 球权转换，统计球权间隔时间、球权转换方式，zoom置为0，bp置为-1
                if bp != -1 and rec['BP'] != bp:
                    zoom = 0
                    # ['PVL', 'MK', 'ORB', 'TOV', 'DRB', 'TVL', 'D3S', 'JB', 'FF1', 'FF2', 'PF']
                    if 'MS' in rec or 'TF' in rec or 'D3S' in rec or 'ORB' in rec:
                        print('MS TF D3S ORB')
                        MSerror += 1
                        print(ss, gm, rec)
                        flag = 1
                        qtr = int(rec['Q']) + 1
                        now = MPTime(rec['T'])
                        qtr_end = '%d:00.0' % (qtr * 12)
                        now = MPTime(qtr_end) - now
                        playbyplay_editor_window = GameDetailEditor(gm=gm[:-7], title='第%d节 剩余%s    %s' % (qtr, now, str(rec)))
                        playbyplay_editor_window.loop()
                    if 'TOV' in rec:
                        flag = 1
                        pmtov = rec['plyr']
                        if pmtov not in ['Team', '']:
                            new_player(pmtov, ss)

                    for pm in tmpms:
                        # 记录前板
                        if pm in ['Team', '']:
                            print(pm, gm, tmpms[pm])
                        new_player(pm, ss)
                        count_item[i, 2, 0] += tmpms[pm][0]
                        count_item[i, rec['BP'], 0] += tmpms[pm][0]  # 主客场
                        count_item[i, 2, rec['Q'] + 1] += tmpms[pm][0]
                        count_item[i, rec['BP'], rec['Q'] + 1] += tmpms[pm][0]  # 节次
                        plyrs[pm][i][0] += tmpms[pm][0]
                        plyrs[pm][i][-1][ss][0] += tmpms[pm][0]
                        # 记录间隔时间
                        interval = MPTime(rec['T']) - tmpms[pm][1]
                        if not interval:
                            interval = MPTime('0:00.0')
                        count_time[i][2][0] += interval
                        count_time[i][rec['BP']][0] += interval
                        count_time[i][2][rec['Q'] + 1] += interval
                        count_time[i][rec['BP']][rec['Q'] + 1] += interval
                        plyrs[pm][i][1] += interval
                        plyrs[pm][i][-1][ss][1] += interval
                        # 记录失误
                        if flag:
                            plyrs[pm][i][3]['TOV'][0] += 1
                            plyrs[pm][i][-1][ss][3]['TOV'][0] += 1
                            if pmtov not in ['Team', '']:
                                plyrs[pmtov][i][3]['TOV'][1] += 1
                                plyrs[pmtov][i][-1][ss][3]['TOV'][1] += 1
                    # 记录得失分
                    for pm in plyr_pts:
                        if pm in ['Team', '']:
                            print(pm, gm, pts, plyr_pts[pm], tmpms)
                        new_player(pm, ss)
                        for GoM in range(2):
                            for s in range(3):
                                # 记录球队得失分
                                if GoM:
                                    count_score[i][2][0] += pts[GoM][s] * (s + 1)
                                    count_score[i][rec['BP']][0] += pts[GoM][s] * (s + 1)
                                    count_score[i][2][rec['Q'] + 1] += pts[GoM][s] * (s + 1)
                                    count_score[i][rec['BP']][rec['Q'] + 1] += pts[GoM][s] * (s + 1)
                                    plyrs[pm][i][2] += pts[GoM][s] * (s + 1)
                                    plyrs[pm][i][-1][ss][2] += pts[GoM][s] * (s + 1)
                                    plyrs[pm][i][5][s * 2] += pts[GoM][s]
                                    plyrs[pm][i][-1][ss][5][s * 2] += pts[GoM][s]
                                plyrs[pm][i][5][s * 2 + 1] += pts[GoM][s]
                                plyrs[pm][i][-1][ss][5][s * 2 + 1] += pts[GoM][s]
                                # 记录球员得失分
                                plyrs[pm][i][6][s * 2 + 1] += plyr_pts[pm][GoM][s]
                                plyrs[pm][i][-1][ss][6][s * 2 + 1] += plyr_pts[pm][GoM][s]
                                if GoM:
                                    plyrs[pm][i][4] += plyr_pts[pm][GoM][s] * (s + 1)
                                    plyrs[pm][i][-1][ss][4] += plyr_pts[pm][GoM][s] * (s + 1)
                                    plyrs[pm][i][6][s * 2] += plyr_pts[pm][GoM][s]
                                    plyrs[pm][i][-1][ss][6][s * 2] += plyr_pts[pm][GoM][s]

                    bp = -1
                    exchange_plays = list(set(exchange_plays + list(rec.keys())))
                    tmpms = {}
                    pts = [[0, 0, 0], [0, 0, 0]]
                    plyr_pts = {}
                    flag = 0
                # 出现首次前板，zoom置为1，bp置为当前球权方
                if eval(sentence) and not zoom:
                    zoom = 1
                    bp = rec['BP']
                    # 分球员记录
                    pm = rec['ORB']
                    if tmpms:
                        print(gm, rec, tmpms)
                    tmpms[pm] = [1, MPTime(rec['T'])]
                    flag = 0
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

# %%
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
            plyrs[pm][i][3]['TOV'][0] /= plyrs[pm][i][0]
        for ss in plyrs[pm][i][-1]:
            if plyrs[pm][i][-1][ss][0]:
                plyrs[pm][i][-1][ss][1] = plyrs[pm][i][-1][ss][1].average_acc(plyrs[pm][i][-1][ss][0])
                # plyrs[pm][i][-1][ss][2] /= plyrs[pm][i][-1][ss][0]
                plyrs[pm][i][-1][ss][3]['TOV'][0] /= plyrs[pm][i][-1][ss][0]

print('共%d名球员' % len(plyrs))
# for pm in plyrs:
#     print(pm, plyrs[pm])

print(exchange_plays)
print(MSerror)
writeToPickle('./data/Enforce/player%sEnforce.pickle' % tartext[tar_item], plyrs)
writeToPickle('./data/Enforce/season%sEnforceRecord.pickle' % tartext[tar_item], [count_games_all, count_item_all, count_time_all,
                                                                                  average_time_all, count_score_all, average_score_all])
