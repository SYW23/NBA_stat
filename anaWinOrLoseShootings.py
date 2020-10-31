import pickle
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from klasses.miscellaneous import MPTime
from klasses.Game import Game
from util import gameMarkToDir, LoadPickle
import copy


def diffBeforeScore(rec, GoM, KoS):    # 计算球员得分/投失前的分差
    s = copy.copy(rec['S'])
    if GoM:
        s[rec['MK'][2]] -= rec['MK'][1]
    if rec[KoS][2]:
        return s[1] - s[0]
    else:
        return s[0] - s[1]


f = open('./data/playermark2playername.pickle', 'rb')
pm2pn = pickle.load(f)
f.close()
regularOrPlayoffs = ['regular', 'playoffs']
regularOrPlayoff = 0
num_items = 19
lastSecs = '0:24.0'
cmp1 = 1    # 0->出手前落后（不包括平局） 1->出手前落后或平局
cmp2 = 1    # 0->若命中则反超（不包括追平） 1->若命中则追平或反超

for i in range(0, 2):
    count_games, count_cgames = 0, []
    plyrs = {}  # plyrs = {'playerMark': [np.zeros((1, 19)), [[出手场次], [关键场次]]]}
    # 0命中率1投中2出手3罚球命中率4罚球投中5罚球出手6两分命中率7两分投中8两分出手9三分命中率10三分投中11三分出手
    # 12助攻两分13助攻三分14盖帽15总得分16负责得分17eFG%18TS%
    for season in tqdm(range(1996, 2020)):
        ss = '%d_%d' % (season, season + 1)
        # print('starting to analysing season %s:' % ss)
        gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
        for gm in gms:
            count_games += 1
            game = Game(gm[:-7], regularOrPlayoffs[i])
            record = LoadPickle(gameMarkToDir(gm[:-7], regularOrPlayoffs[i], tp=3))
            # _, _, _, record = game.game_scanner(gm[:-7])
            lastqtr = record[-1]['Q']    # 最后一节节次
            assert lastqtr > 2
            lastsec = MPTime('%d:00.0' % (48 + 5 * (lastqtr - 3)))    # 本场最后时刻
            ix = -1    # 从后往前遍历比赛过程
            for qtr in range(lastqtr - 2):    # 从最后时刻开始统计（若有加时则依次从后往前统计每节次最后时刻至第四节为止）
                if qtr > 0:
                    lastsec = lastsec - MPTime('5:00.0')    # 本节最后时刻
                timetd = lastsec - MPTime(lastSecs)    # 统计时间范围
                while record[ix]['Q'] > lastqtr - qtr:
                    ix -= 1
                ft = [-1, -1, -1]
                ftt = [-1, -1]
                ftplus = [-1, -1, -1, -1, '']    # 第4个元素用于判断罚球方与运动战投篮出手方是否一致，第5个元素用于记录罚球人
                while MPTime(record[ix]['T']) >= timetd and record[ix]['Q'] == lastqtr - qtr:
                    tmp = record[ix]
                    if 'MK' in tmp or 'MS' in tmp:
                        GoM = 1 if 'MK' in tmp else 0
                        KoS = 'MK' if GoM else 'MS'
                        s = tmp[KoS][1]    # （潜在）得分
                        diff = diffBeforeScore(tmp, GoM, KoS)    # 出手前分差
                        # 处理罚球情况
                        if s == 1:
                            if ftplus[2] == 0:
                                # print('非+1罚球情况', gm, tmp, GoM, KoS, s, diff, lastsec, lastqtr, timetd, ix)
                                ftplus = [-1, -1, -1, -1, '']
                            if tmp['D'][1] > 1:    # 非+1罚球，多罚球
                                if ft == [-1, -1, -1]:
                                    ft = [0, 1, 0]
                                else:
                                    ft[1] += 1
                                if GoM:
                                    ft[0] += 1
                                if tmp['D'][0] == 1:
                                    ft[2] = 1
                            else:
                                if tmp['M'] != '':    # 非+1罚球，单罚球
                                    ftt = [0, 1]
                                    if GoM:
                                        ftt[0] += 1
                                else:    # +1罚球
                                    if gm != '201710200MIN.pickle' and not \
                                            ('PF' in record[ix - 1] and record[ix - 1]['PF'] in ['Away from play foul', 'Inbound foul']):
                                        ftplus = [0, 1, 0, tmp[KoS][2], tmp[KoS][0]]
                                        if gm == '201611160DEN.pickle':
                                            ftplus[4] = 'bookede01'
                                        if gm == '200112210GSW.pickle':
                                            ftplus = [-1, -1, -1, -1, '']
                                        if GoM:
                                            ftplus[0] += 1
                                    else:
                                        # print('Away from play', gm, tmp, GoM, KoS, s, diff, lastsec, lastqtr, timetd, ix)
                                        ftt = [0, 1]
                                        if GoM:
                                            ftt[0] += 1
                        else:
                            if ftplus[2] == 0:    # 此次2/3分投篮后有+1罚球
                                if ftplus[3] == tmp[KoS][2] and tmp['BP'] == ftplus[3]:
                                    # print(gm, tmp, GoM, KoS, s, diff, lastsec, lastqtr, timetd, ix)
                                    assert 'FF1' in record[ix + 1] or 'PF' in record[ix + 1] and \
                                           (record[ix + 1]['PF'] == 'Shooting foul' or record[ix + 1]['PF'] == 'Shooting block foul') and \
                                           tmp[KoS][0] == ftplus[4]    # 投篮犯规且投篮与罚球人一致
                                    ftplus[2] = 1
                                else:
                                    # print('不一致', gm, tmp, GoM, KoS, s, diff, lastsec, lastqtr, timetd, ix)
                                    ftplus = [-1, -1, -1, -1, '']
                        if ft[2] == 1:    # 有多个罚球且统计完整
                            if s == 1 and tmp['D'][1] != ft[1]:
                                if not (('TOV'in record[ix + 1] and record[ix + 1]['TOV'] in ['offensive goaltending', 'turnover', 'lane violation', 'lane violation.'] and record[ix + 1]['BP'] != tmp['BP']) or
                                        ('TOV' in record[ix + 2] and record[ix + 2]['TOV'] in ['lane violation.', 'lane', 'turnover', 'offensive goaltending'] and record[ix + 2]['BP'] != tmp['BP']) or
                                        ('PVL' in record[ix + 1] and record[ix + 1]['PVL'] == 'double lane') or
                                        ('PVL' in record[ix + 2] and record[ix + 2]['PVL'] == 'lane') or
                                        'JB'in record[ix + 1]):
                                    print(gm, tmp, ft)
                            s = ft[1]    # 将s暂时改为此次罚球总数
                        if ftplus[2] == 1:
                            s += 1
                        # if gm == '201305060SAS.pickle':
                        #     print(tmp, GoM, KoS, s, diff, lastsec, lastqtr, timetd)
                        sentence = '0 %s %d + %d %s %d' % (('<=' if cmp2 else '<'), diff, s, ('<=' if cmp1 else '<'), s)
                        judge = eval(sentence)
                        if ft[2] == 1:    # s改回1
                            s = 1
                        elif ftplus[2] == 1:    # s改回
                            s -= 1
                        if judge:    # 认定为关键出手：出手前落后或平局，进球则追平或反超
                            # 统计关键比赛数量
                            if gm not in count_cgames:
                                count_cgames.append(gm)
                            # 参赛人员记录关键场次
                            aps = game.teamplyrs()
                            for rh in range(2):
                                for ap in aps[rh]:
                                    if ap not in plyrs:
                                        plyrs[ap] = [np.zeros((1, num_items)), [[], []]]
                                    if gm not in plyrs[ap][1][1]:
                                        plyrs[ap][1][1].append(gm)
                                    else:
                                        break
                            # 统计出手情况
                            if tmp[KoS][1] == 1:
                                if ft[2] == 1:
                                    # print(gm, tmp, ft)
                                    pm = tmp[KoS][0]
                                    if pm not in plyrs:
                                        plyrs[pm] = [np.zeros((1, num_items)), [[], []]]
                                    plyrs[pm][0][0, 4] += ft[0]
                                    plyrs[pm][0][0, 5] += ft[1]
                                    ft = [-1, -1, -1]
                                elif ftt[1] == 1:
                                    pm = tmp[KoS][0]
                                    if pm not in plyrs:
                                        plyrs[pm] = [np.zeros((1, num_items)), [[], []]]
                                    plyrs[pm][0][0, 4] += ftt[0]
                                    plyrs[pm][0][0, 5] += ftt[1]
                                    ftt = [-1, -1]
                            else:
                                pm = tmp[KoS][0]
                                # if pm == 'curryst01':
                                #     print(gm)
                                if pm not in plyrs:
                                    plyrs[pm] = [np.zeros((1, num_items)), [[], []]]
                                plyrs[pm][0][0, 2] += 1
                                plyrs[pm][0][0, tmp[KoS][1] * 3 + 2] += 1
                                if GoM:
                                    plyrs[pm][0][0, 1] += 1
                                    plyrs[pm][0][0, tmp[KoS][1] * 3 + 1] += 1
                                if ftplus[2] == 1:
                                    # print('成立', gm, tmp, GoM, KoS, s, diff, lastsec, lastqtr, timetd, ix)
                                    plyrs[pm][0][0, 4] += ftplus[0]
                                    plyrs[pm][0][0, 5] += ftplus[1]
                                    ftplus = [-1, -1, -1, -1, '']
                                # 出手球员记录关键出手场次
                                if gm not in plyrs[pm][1][0]:
                                    plyrs[pm][1][0].append(gm)
                            if GoM and 'AST' in tmp:
                                pm = tmp['AST']
                                if pm not in plyrs:
                                    plyrs[pm] = [np.zeros((1, num_items)), [[], []]]
                                plyrs[pm][0][0, 10 + s] += 1
                            elif not GoM and 'BLK' in tmp:
                                pm = tmp['BLK']
                                if pm not in plyrs:
                                    plyrs[pm] = [np.zeros((1, num_items)), [[], []]]
                                plyrs[pm][0][0, 14] += 1
                        else:
                            if ft[2] == 1:
                                ft = [-1, -1, -1]
                            elif ftt[1] == 1:
                                ftt = [-1, -1]
                            elif ftplus[2] == 1:
                                ftplus = [-1, -1, -1, -1, '']
                    ix -= 1
    td = 5 if i else 10
    ks = list(plyrs.keys())
    for k in ks:
        if plyrs[k][0][0, 2] < td:
            plyrs.pop(k)

    resPlayer = []
    for k in plyrs:
        if plyrs[k][0][0, 2] >= td:
            resPlayer.append([pm2pn[k]] + list(plyrs[k][0][0]) + [len(plyrs[k][1][0]) / len(plyrs[k][1][1]), len(plyrs[k][1][0]), len(plyrs[k][1][1])])
    #%%
    df = pd.DataFrame(resPlayer, columns=['球员', '命中率', '投中', '出手', '罚球命中率', '罚球投中', '罚球出手',
                                          '两分命中率', '两分投中', '两分出手', '三分命中率', '三分投中', '三分出手',
                                          '助攻两分', '助攻三分', '盖帽', '总得分', '负责得分', 'eFG%', 'TS%',
                                          '关键出手率', '出手场次', '关键场次'], index=None)
    df['命中率'] = df['投中'] / df['出手']
    df['罚球命中率'] = df['罚球投中'] / df['罚球出手']
    df['两分命中率'] = df['两分投中'] / df['两分出手']
    df['三分命中率'] = df['三分投中'] / df['三分出手']
    df['总得分'] = df['罚球投中'] + 2 * df['两分投中'] + 3 * df['三分投中']
    df['负责得分'] = df['罚球投中'] + 2 * df['两分投中'] + 3 * df['三分投中'] + 2 * df['助攻两分'] + 3 * df['助攻三分']
    df['eFG%'] = (df['投中'] + 0.5 * df['三分投中']) / df['出手']
    df['TS%'] = df['总得分'] / (2 * (df['出手'] + 0.44 * df['罚球出手']))
    df['每场得分'] = df['总得分'] / df['关键场次']
    df['每场负责得分'] = df['负责得分'] / df['关键场次']
    df = df.sort_values(by='总得分', ascending=False)
    # print(df)
    df.to_csv('./win_or_lose/%s_最后%d秒winorloseshootings.csv' % (regularOrPlayoffs[i], MPTime(lastSecs).secs()), index=None)

    print('总场次:', count_games)
    print('关键场次:', len(count_cgames))

