#!/usr/bin/python
# -*- coding:utf8 -*-
import sys
sys.path.append('../')
import os
from tqdm import tqdm
import numpy as np
import pandas as pd
import math
from util import gameMarkToSeason, gameMarkToDir, LoadPickle, writeToPickle, read_nba_pbp
from klasses.Game import Game
from klasses.miscellaneous import MPTime
from windows.result_windows import ShowSingleGame
import matplotlib.pyplot as plt


class GameReviewer(object):
    def __init__(self, gm, RoP):
        self.game = Game(gm, RoP)
        record, rot, bxs = self.game.preprocess(load=1)
        self.record = record
        self.rot = rot
        self.bxs = bxs
        self.dist = ['      0~ 5ft 2PT', '      5~10ft 2PT', '     10~15ft 2PT', '     15~20ft 2PT', '       >20ft 2PT',
                     '      <=25ft 3PT', '     25~30ft 3PT', '     30~35ft 3PT', '     35~40ft 3PT', '       >40ft 3PT',
                     '     restricted(RA)', '     paint(Non-RA)', '     mid range', '     left corner 3', '     right corner 3', '     above the break 3']
        # for r in self.rot:
        #     print(r)
        #
        # print(list(bxs.tdbxs[0][0]['team']))
        # print(list(bxs.tdbxs[0][1]['team']))
        # print(list(bxs.tdbxs[0][2]['team']))
        # print(list(bxs.tdbxs[0][3]['team']))
        # print(list(bxs.tdbxs[0][4]['team']))
        # print()
        # print(list(bxs.tdbxs[1][0]['team']))
        # print(list(bxs.tdbxs[1][1]['team']))
        # print(list(bxs.tdbxs[1][2]['team']))
        # print(list(bxs.tdbxs[1][3]['team']))
        # print(list(bxs.tdbxs[1][4]['team']))
        # print()
        # for tm in range(2):
        #     for k in bxs.tdbxs[tm][0]:
        #         if k != 'team':
        #             print(k, 2880 / bxs.tdbxs[tm][0][k][0][-2] * bxs.tdbxs[tm][0][k][0][-3])
        #             print('all', list(bxs.tdbxs[tm][0][k][0]))
        #             if k in bxs.tdbxs[tm][1]:
        #                 print(1, list(bxs.tdbxs[tm][1][k][0])[-3], list(bxs.tdbxs[tm][1][k][0])[-3] * 2880 / list(bxs.tdbxs[tm][1][k][0])[-2], list(bxs.tdbxs[tm][1][k][0]))
        #             if k in bxs.tdbxs[tm][2]:
        #                 print(2, list(bxs.tdbxs[tm][2][k][0])[-3], list(bxs.tdbxs[tm][2][k][0])[-3] * 2880 / list(bxs.tdbxs[tm][2][k][0])[-2], list(bxs.tdbxs[tm][2][k][0]))
        #             if k in bxs.tdbxs[tm][3]:
        #                 print(3, list(bxs.tdbxs[tm][3][k][0])[-3], list(bxs.tdbxs[tm][3][k][0])[-3] * 2880 / list(bxs.tdbxs[tm][3][k][0])[-2], list(bxs.tdbxs[tm][3][k][0]))
        #             if k in bxs.tdbxs[tm][4]:
        #                 print(4, list(bxs.tdbxs[tm][4][k][0])[-3], list(bxs.tdbxs[tm][4][k][0])[-3] * 2880 / list(bxs.tdbxs[tm][4][k][0])[-2], list(bxs.tdbxs[tm][4][k][0]))
        #             print()
        #             print(list(bxs.tdbxs[0][0][k][1][0]))
        #             print(list(bxs.tdbxs[0][0][k][1][1]))
        #     print('\n')

    # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS 18BP 19MP 20+/-
    def eFGperc(self):    # 四要素之一：有效命中率
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = (bxsc[0] + 0.5 * bxsc[3]) / bxsc[1]
        return tmp

    def TOVperc(self):    # 四要素之一：失误率
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = bxsc[15] / bxsc[18]
        return tmp

    def ORBperc(self):    # 四要素之一：进攻篮板率
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = bxsc[9] / (bxsc[9] + self.bxs.tdbxs[i - 1][0]['team'][10])
        return tmp

    def FTr(self):    # 四要素之一：造罚球率
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = bxsc[6] / bxsc[1]
        return tmp

    def FTPtPTsperc(self):    # 罚球得分占比
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = bxsc[6] / bxsc[17]
        return tmp

    def FTprop(self):    # 罚球出手/运动战出手比
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = bxsc[7] / bxsc[1]
        return tmp

    def FTperc(self):    # 罚球命中率
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = bxsc[6] / bxsc[7]
        return tmp

    def twoPtperc(self):    # 两分球命中率
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = (bxsc[0] - bxsc[3]) / (bxsc[1] - bxsc[4])
        return tmp

    def twoPtprop(self):    # 两分球出手占比
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = (bxsc[1] - bxsc[4]) / bxsc[1]
        return tmp

    def twoPtPTsperc(self):    # 两分球得分占比
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = (bxsc[0] - bxsc[3]) * 2 / bxsc[17]
        return tmp

    def threePtperc(self):    # 三分球命中率
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = bxsc[3] / bxsc[4]
        return tmp

    def threePtprop(self):    # 三分球出手占比
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = bxsc[4] / bxsc[1]
        return tmp

    def threePtPTsperc(self):    # 三分球得分占比
        tmp = [0, 0]
        for i in range(2):
            bxsc = self.bxs.tdbxs[i][0]['team']
            tmp[i] = bxsc[3] * 3 / bxsc[17]
        return tmp

    def fourfactors(self):
        return pd.DataFrame([self.eFGperc(), self.TOVperc(), self.ORBperc(), self.FTr()],
                            index=['     eFG%', '     TOV%', '     ORB%', '     FT/FGA'], columns=list(self.game.bxscr[0]))

    def shooting(self):
        asts = [[0, 0], [0, 0]]
        for ix, rec in enumerate(self.game.gn.record):
            if 'MK' in rec and 'AST' in rec:
                asts[rec['MK'][1] - 2][rec['MK'][2]] += 1
        asts[0][0] = asts[0][0] / (self.bxs.tdbxs[0][0]['team'][0] - self.bxs.tdbxs[0][0]['team'][3])
        asts[0][1] = asts[0][1] / (self.bxs.tdbxs[1][0]['team'][0] - self.bxs.tdbxs[1][0]['team'][3])
        asts[1][0] = asts[1][0] / self.bxs.tdbxs[0][0]['team'][3] if self.bxs.tdbxs[0][0]['team'][3] else -1
        asts[1][1] = asts[1][1] / self.bxs.tdbxs[1][0]['team'][3] if self.bxs.tdbxs[1][0]['team'][3] else -1
        return pd.DataFrame([self.twoPtperc(), self.twoPtprop(), self.twoPtPTsperc(), asts[0],
                             self.threePtperc(), self.threePtprop(), self.threePtPTsperc(), asts[1],
                             self.FTperc(), self.FTprop(), self.FTPtPTsperc()],
                            index=['     2PT %', '     2PT FGA%', '     2PT PTS%', '     2PT ASTed%',
                                   '     3PT %', '     3PT FGA%', '     3PT PTS%', '     3PT ASTed%',
                                   '     FT %', '     FTA/FGA', '     FT PTS%'],
                            columns=list(self.game.bxscr[0]))

    def distance(self, rec):
        return math.sqrt(rec['C'][0] ** 2 + rec['C'][1] ** 2) / 10

    def game_counter(self):
        tovpts, orbpts, paintpts, leadmax, longestrun = [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]
        zoomtov, zoomorb, leaderchange, tie, run = 0, 0, 0, 0, 0
        bptov, bporb, leadtm, runningtm = -1, -1, -1, -1
        # ==================== 投篮分布数据 ====================
        # 0客队1主队 0失手1命中 0 0~5 1 5~10 2 10~15 3 15~20 4 20~3PT 5 ~25 6 25~30 7 30~35 8 35~40 9 >40 10 限制区 11 paint限制区外 12 mid range
        shots = np.zeros((2, 3, len(self.dist)))
        for ix, rec in enumerate(self.game.gn.record):
            if 'MK' in rec or 'MS' in rec:
                GoM = 0 if 'MS' in rec else 1
                item = 'MS' if 'MS' in rec else 'MK'
                if rec[item][1] > 1:
                    d = self.distance(rec)
                    # print(d, rec)
                    # ==================== paint得分 ====================
                    if rec[item][1] > 1 and -80 <= rec['C'][0] <= 80 and rec['C'][1] < 140:
                        if GoM:
                            paintpts[rec['MK'][2]] += rec['MK'][1]
                            # if rec['MK'][2] == 1:
                            #     print(rec)
                        if d <= 4:
                            xx = 10
                        else:
                            xx = 11
                        shots[rec[item][2], GoM, xx] += 1
                        if 'AST' in rec:
                            shots[rec[item][2], 2, xx] += 1
                    else:
                        if rec[item][1] < 3:
                            shots[rec[item][2], GoM, 12] += 1
                            if 'AST' in rec:
                                shots[rec[item][2], 2, 12] += 1
                        else:
                            if rec['C'][0] <= -200 and rec['C'][1] <= 100:    # left corner 3pt
                                xx = 13
                            elif rec['C'][0] >= 200 and rec['C'][1] <= 100:    # right corner 3pt
                                xx = 14
                            else:
                                xx = 15
                            shots[rec[item][2], GoM, xx] += 1
                            if 'AST' in rec:
                                shots[rec[item][2], 2, xx] += 1
                    # ==================== 按距离得分统计 ====================
                    if d <= 5:
                        xx = 0
                    elif d <= 10:
                        xx = 1
                    elif d <= 15:
                        xx = 2
                    elif d <= 20:
                        xx = 3
                    elif rec[item][1] < 3:
                        xx = 4
                    elif d <= 25:
                        xx = 5
                    elif d <= 30:
                        xx = 6
                    elif d <= 35:
                        xx = 7
                    elif d <= 40:
                        xx = 8
                    else:
                        xx = 9
                    shots[rec[item][2], GoM, xx] += 1
                    if 'AST' in rec:
                        shots[rec[item][2], 2, xx] += 1
        ads = [[], []]
        for i in range(len(self.dist)):
            for tm in range(2):
                pre = [shots[tm][1][i], shots[tm][0][i] + shots[tm][1][i]]    # FG/FGA
                tail = [shots[tm][1][i] / self.bxs.tdbxs[tm][0]['team'][0],
                        (shots[tm][0][i] + shots[tm][1][i]) / self.bxs.tdbxs[tm][0]['team'][1],
                        shots[tm][1][i] * (3 if 5 <= i <= 9 or i > 12 else 2) / self.bxs.tdbxs[tm][0]['team'][17]]    # 区域命中比例、出手比例、得分比例
                if shots[tm][1][i]:
                    ads[tm].append(pre + [shots[tm][1][i] / (shots[tm][0][i] + shots[tm][1][i]), shots[tm][2][i] / shots[tm][1][i]] + tail)
                else:
                    if shots[tm][0][i] + shots[tm][1][i]:
                        ads[tm].append(pre + [shots[tm][1][i] / (shots[tm][0][i] + shots[tm][1][i]), -1] + tail)
                    else:
                        ads[tm].append(pre + [-1, -1] + tail)
        ads = [pd.DataFrame(x, index=self.dist, columns=['FG', 'FGA', '%', 'ASTed%', 'FG%', 'FGA%', 'PTS%']) for x in ads]
        # ==================== 基础对比数据 ====================
        for ix, rec in enumerate(self.record):
            # ==================== 交替领先、平分、连续得分 ====================
            if 'MK' in rec:
                if rec['S'][0] != rec['S'][1]:
                    li = 0 if rec['S'][0] > rec['S'][1] else 1
                    if li != leadtm:
                        if leadtm != -1:
                            leaderchange += 1
                        leadtm = li
                else:
                    if self.record[ix - 1]['S'][0] != self.record[ix - 1]['S'][1]:
                        tie += 1
                li = rec['MK'][2]
                if li == runningtm:
                    run += rec['MK'][1]
                else:
                    if runningtm == -1:
                        runningtm = li
                        run += rec['MK'][1]
                    else:
                        if longestrun[li] < run:
                            longestrun[li] = run
                        runningtm = li
                        run = rec['MK'][1]
            # ==================== 最大领先 ====================
            li = 0 if rec['S'][0] > rec['S'][1] else 1
            if rec['S'][li] != rec['S'][li - 1] and rec['S'][li] - rec['S'][li - 1] > leadmax[li]:
                leadmax[li] = rec['S'][li] - rec['S'][li - 1]
            # ==================== 跨节 ====================
            if len(rec) == 4 or (ix > 0 and rec['Q'] != self.record[ix - 1]['Q']):
                zoomtov, zoomorb = 0, 0
                bptov, bporb = -1, -1
            # ==================== 利用失误得分 ====================
            if zoomtov:
                if 'MK' in rec and rec['M'] != 'technical':
                    if rec['MK'][-1] == bptov:
                        tovpts[bptov] += rec['MK'][1]
                        # print(rec)
                    else:
                        if rec['M'] != 'technical':
                            print('失误得分存疑', self.game.gm, rec)
                if rec['BP'] != bptov:
                    zoomtov = 0
                    bptov = -1
            if 'TOV' in rec:
                bptov = rec['BP']
                zoomtov = 1
            # ==================== 二次进攻 ====================
            if zoomorb:
                if 'MK' in rec:
                    if rec['MK'][-1] == bporb:
                        # print(rec)
                        orbpts[bporb] += rec['MK'][1]
                    else:
                        if rec['M'] != 'technical':
                            print('二次进攻得分存疑', self.game.gm, rec)
                if rec['BP'] != bporb:
                    zoomorb = 0
                    bporb = -1
            if 'ORB' in rec and (rec['ORB'] != 'Team' or ('MS' in self.record[ix - 1] and self.record[ix - 1]['MS'][1] > 1) or ('MS' in self.record[ix - 1] and self.record[ix - 1]['D'][1] == self.record[ix - 1]['D'][0])):
                bporb = rec['BP']
                zoomorb = 1

        # print(self.game.gm, tovpts[0], orbpts[0], paintpts[0], tovpts[1], orbpts[1], paintpts[1])
        # ==================== 汇总数据 ====================
        return pd.DataFrame([[self.bxs.tdbxs[0][0]['team'][-3], self.bxs.tdbxs[1][0]['team'][-3]],
                             tovpts, [tovpts[0] / self.bxs.tdbxs[0][0]['team'][-4], tovpts[1] / self.bxs.tdbxs[1][0]['team'][-4]],
                             orbpts, [orbpts[0] / self.bxs.tdbxs[0][0]['team'][-4], orbpts[1] / self.bxs.tdbxs[1][0]['team'][-4]],
                             paintpts, [paintpts[0] / self.bxs.tdbxs[0][0]['team'][-4], paintpts[1] / self.bxs.tdbxs[1][0]['team'][-4]],
                             leadmax, [leadmax[0] / self.bxs.tdbxs[0][0]['team'][-4], leadmax[1] / self.bxs.tdbxs[1][0]['team'][-4]],
                             longestrun, [longestrun[0] / self.bxs.tdbxs[0][0]['team'][-4], longestrun[1] / self.bxs.tdbxs[1][0]['team'][-4]],
                             [leaderchange, leaderchange], [tie, tie]],
                            index=['     pace',
                                   '     pts off tovs', '     pts% off tovs',
                                   '     2nd chance pts', '     2nd chance pts%',
                                   '     pts in the paint', '     pts% in the paint',
                                   '     biggest lead', '     biggest lead pts%',
                                   '     longest run', '     longest run pts%',
                                   '     lead changes', '     times tied'],
                            columns=list(self.game.bxscr[0])), ads


if __name__ == '__main__':
    regularOrPlayoffs = ['regular', 'playoff']
    items = set()
    for i in range(1):
        cmps_all, cmps_shts_area_all, basic_all, count_game = np.zeros((25,)), np.zeros((16, 7)), np.zeros((17, )), 0
        cmps_by_season, basic_by_season = {}, {}
        for season in range(2000, 2021):
            ss = '%d_%d' % (season, season + 1)
            cmps_season = np.zeros((25,))
            cmps_shts_area_season = np.zeros((16, 7))
            basic_season = np.zeros((17, ))
            count_game_season = 0
            gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
            for gm in tqdm(gms):
                cmps = pd.DataFrame()
                count_game += 1
                count_game_season += 1
                # print(gm)
                gr = GameReviewer(gm, regularOrPlayoffs[i])
                tms = list(gr.game.bxscr[0])
                scores = [gr.game.bxscr[0][x][0] for x in gr.game.bxscr[0]]
                winner = 1 if scores[0] < scores[1] else 0

                # 基础数据看胜率
                cmp = gr.bxs.tdbxs[winner][0]['team'][:-4] >= gr.bxs.tdbxs[winner - 1][0]['team'][:-4]
                cmp = cmp.astype(int)
                basic_all += cmp
                basic_season += cmp
                # print(basic_all)

                basic, ads = gr.game_counter()
                ffs = gr.fourfactors()
                shts = gr.shooting()
                # for tm in range(2):
                #     print('\t 主队 %s' % list(gr.game.bxscr[0])[1] if tm else '\t 客队 %s' % list(gr.game.bxscr[0])[0])
                #     print(ads[tm])
                #     print(ads[tm].shape)
                #     print()

                # 衍生数据看胜率
                cmps = cmps.append(basic[1:11])
                cmps = cmps.append(ffs)
                cmps = cmps.append(shts)
                cmp = cmps[tms[winner]] >= cmps[tms[winner - 1]]
                cmp = cmp.astype(int).values
                cmps_all += cmp
                cmps_season += cmp

                # 投篮分布看胜率
                cmp = ads[winner] >= ads[winner - 1]
                cmp = cmp.astype(int).values
                cmps_shts_area_all += cmp
                cmps_shts_area_season += cmp
            cmps_by_season[ss] = [cmps_season, cmps_shts_area_season, basic_season, count_game_season]
        print(count_game)
        items = ['     pts off tovs', '     pts% off tovs', '     2nd chance pts', '     2nd chance pts%',
                 '     pts in the paint', '     pts% in the paint', '     biggest lead', '     biggest lead pts%',
                 '     longest run', '     longest run pts%', '     eFG%', '     TOV%', '     ORB%', '     FT/FGA',
                 '     2PT %', '     2PT FGA%', '     2PT PTS%', '     2PT ASTed%',
                 '     3PT %', '     3PT FGA%', '     3PT PTS%', '     3PT ASTed%',
                 '     FT %', '     FTA/FGA', '     FT PTS%']
        cmps_all = list(cmps_all.T)
        cmps_all[11] = count_game - cmps_all[11]
        for ix, it in enumerate(cmps_all):
            cmps_all[ix] = [cmps_all[ix] / count_game, items[ix]]
        cmps_all.sort(reverse=True)
        for it in cmps_all:
            print(it)
        print()

        items = ['FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
        basic_all[15] = count_game - basic_all[15]
        basic_all /= count_game
        basic_all = list(basic_all)
        for ix, it in enumerate(basic_all):
            basic_all[ix] = [basic_all[ix], items[ix]]
        basic_all.sort(reverse=True)
        for it in basic_all:
            print(it)

        cmps_shts_area_all = pd.DataFrame(cmps_shts_area_all / count_game, index=list(ads[0].index), columns=ads[0].columns)
        print(cmps_shts_area_all)
        fig = plt.figure('Image', figsize=(10, 4))
        ax = fig.add_subplot(1, 1, 1)
        img = ax.imshow(cmps_shts_area_all.values)
        cols = list(cmps_shts_area_all.columns)
        ixs = list(cmps_shts_area_all.index)
        ax.set_xticks(np.arange(len(cols)))
        ax.set_xticklabels(cols)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
                 rotation_mode="anchor")
        ax.set_yticks(np.arange(len(ixs)))
        ax.set_yticklabels(ixs)

        for y in range(cmps_shts_area_all.shape[0]):
            for x in range(cmps_shts_area_all.shape[1]):
                text = ax.text(x, y, '%.2f' % cmps_shts_area_all[cols[x]][y],
                               ha="center", va="center", color="w")

        # h1 = plt.contourf(cmps_shts_area_all)
        fig.colorbar(img, ax=ax)
        plt.show()

    writeToPickle('D:/sunyiwu/stat/data/winning_point.pickle', [[cmps_all, cmps_shts_area_all, basic_all, count_game], cmps_by_season])

# 5048  2016-2021
# [0.8098256735340729, '     eFG%']
# [0.803486529318542, '     biggest lead']
# [0.7977416798732171, '     biggest lead pts%']
# [0.7022583201267829, '     3PT %']
# [0.6816561014263075, '     2PT %']
# [0.6024167987321711, '     TOV%']
# [0.5919175911251982, '     pts off tovs']
# [0.5845879556259905, '     FT/FGA']
# [0.5711172741679873, '     ORB%']
# [0.5673534072900158, '     FTA/FGA']
# [0.5635895404120443, '     3PT PTS%']
# [0.563391442155309, '     pts in the paint']
# [0.5427892234548336, '     FT %']
# [0.5382329635499208, '     2PT ASTed%']
# [0.5311014263074485, '     pts% off tovs']
# [0.5124801901743264, '     2nd chance pts']
# [0.5116877971473851, '     3PT FGA%']
# [0.4954437400950872, '     FT PTS%']
# [0.4857369255150555, '     2PT FGA%']
# [0.46414421553090335, '     2nd chance pts%']
# [0.43898573692551507, '     3PT ASTed%']
# [0.43561806656101426, '     2PT PTS%']
# [0.4348256735340729, '     pts% in the paint']
# [0.2539619651347068, '     longest run']
# [0.22404912836767035, '     longest run pts%']
