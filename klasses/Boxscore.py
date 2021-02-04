#!/usr/bin/python
# -*- coding:utf8 -*-
import numpy as np
from klasses.miscellaneous import MPTime


class Boxscore(object):
    def __init__(self, gm, plyrs_oncourt, plyrs):
        self.num_items = 21
        self.gm = gm
        self.plyrs_oncourt = plyrs_oncourt    # 实时跟进上场球员
        self.plyrs = plyrs    # 两队阵中球员名单
        self.qtr_stats = [{}, {}]    # 实时跟进单节上场球员技术统计
        self.default_qtr()
        self.plyrs_mp = {}
        self.default_mp('0:00.0')
        # 0客队1主队    0全场 1Q1 2Q2 3Q3 4Q4 5OT1 6OT2 7OT3 8OT4 9H1 10H2
        self.tdbxs = [[{'team': np.zeros((self.num_items,))}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
                      [{'team': np.zeros((self.num_items,))}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}]]    # traditional
        self.adbxs = [[{'team': np.zeros((self.num_items,))}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
                      [{'team': np.zeros((self.num_items,))}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}]]    # advanced
        # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS 18BP 19MP 20+/-

    def default_qtr(self):
        for tm in range(2):
            self.qtr_stats[tm]['team'] = np.zeros((self.num_items,))    # 球队技术统计初始化
            for pm in self.plyrs_oncourt[tm]:
                # 单节上场球员技术统计初始化  [球员单节个人数据, [球员单节在场期间本队数据, 球员单节在场期间敌队数据]]
                self.qtr_stats[tm][pm] = [np.zeros((self.num_items,)), [np.zeros((self.num_items,)), np.zeros((self.num_items,))]]

    def default_mp(self, now):
        for tm in range(2):
            for pm in self.plyrs_oncourt[tm]:
                self.plyrs_mp[pm] = MPTime(now)

    def update_basic(self, pms, rec, r):
        for pm_stat in pms:
            pm_tm = 0 if pm_stat in self.plyrs[0] else 1
            for it in pms[pm_stat]:
                if pm_stat not in self.qtr_stats[pm_tm]:
                    # print(self.gm, rec, r)
                    # self.plyrs_oncourt = r['R']
                    # self.plyrs_mp[lst[0]] = MPTime(rec['T'])
                    assert rec['T'] == r['T'] or ('plyr' in rec and rec['plyr'] == 'barrybr01')
                    self.qtr_stats[pm_tm][pm_stat] = [np.zeros((self.num_items,)), [np.zeros((self.num_items,)), np.zeros((self.num_items,))]]
                self.qtr_stats[pm_tm][pm_stat][0][it] += 1    # 更新球员本人数据
                self.qtr_stats[pm_tm]['team'][it] += 1
                for tm in range(2):
                    for pm in self.plyrs_oncourt[tm]:
                        self.qtr_stats[tm][pm][1][0 if tm == pm_tm else 1][it] += 1    # 更新球员本队/敌队数据

    def update_pace(self, bp):    # 更新pace数据
        ix = 18
        delta = 0.5
        for tm in range(2):
            self.qtr_stats[tm]['team'][ix] += delta
            for pm in self.plyrs_oncourt[tm]:
                self.qtr_stats[tm][pm][0][ix] += delta
                self.qtr_stats[tm][pm][1][0][ix] += delta
                self.qtr_stats[tm][pm][1][1][ix] += delta

    def update_pts(self, lst, rec, r):    # 更新得分类数据
        pt = lst[1]
        ix = 17
        if lst[0] not in self.qtr_stats[lst[2]] or lst[0] not in self.plyrs_oncourt[lst[2]]:    # 若球员不在场，则此时刻所有得分同时作用于下场和上场球员（下场球员的遗留影响、上场球员已在场上）
            # print(self.gm, rec, r)
            if lst[0] not in self.plyrs_mp:
                self.plyrs_mp[lst[0]] = MPTime(rec['T'])
            assert rec['T'] == r['T']
            if lst[0] not in self.qtr_stats[lst[2]]:
                self.qtr_stats[lst[2]][lst[0]] = [np.zeros((self.num_items,)), [np.zeros((self.num_items,)), np.zeros((self.num_items,))]]
            self.qtr_stats[lst[2]][lst[0]][1][0][ix] += pt
        self.qtr_stats[lst[2]][lst[0]][0][ix] += pt
        self.qtr_stats[lst[2]]['team'][ix] += pt
        for tm in range(2):
            for pm in self.plyrs_oncourt[tm]:
                self.qtr_stats[tm][pm][1][0 if tm == lst[2] else 1][ix] += pt

    def swt(self, new, t=0):    # 节内发生换人，初始化新上场球员数据，更新场上阵容    t = 0 节中换人  1 节中换人且最后一条记录未转换球权（202012220BRK {'Q': 2, 'T': '28:03.0', 'MS': ['jordade01', 1, 1], 'D': [2, 2], 'M': '', 'BP': 1, 'S': [49, 77]}）
        ix = 19
        for tm in range(2):
            on_pms = set(new['R'][tm]) - set(self.plyrs_oncourt[tm])
            off_pms = set(self.plyrs_oncourt[tm]) - set(new['R'][tm])
            # 上场球员：记录上场时刻，初始化数据统计格式
            for on_pm in on_pms:
                if on_pm not in self.plyrs_mp:
                    self.plyrs_mp[on_pm] = MPTime(new['T'])
                if on_pm not in self.qtr_stats[tm]:
                    self.qtr_stats[tm][on_pm] = [np.zeros((self.num_items,)), [np.zeros((self.num_items,)), np.zeros((self.num_items,))]]
                # if t:    # 节中换上场球员pace修正
                self.qtr_stats[tm][on_pm][0][18] += 0.5
                self.qtr_stats[tm][on_pm][1][0][18] += 0.5
                self.qtr_stats[tm][on_pm][1][1][18] += 0.5
            # 下场球员：累计上场时间
            for off_pm in off_pms:
                assert off_pm in self.plyrs_mp
                self.qtr_stats[tm][off_pm][0][ix] += (MPTime(new['T']) - self.plyrs_mp[off_pm]).secs()
                self.plyrs_mp.pop(off_pm)
                # if off_pm == 'wiggian01':
                #     print(self.qtr_stats[0]['wiggian01'])
                if t:    # 节中换下场球员pace修正
                    self.qtr_stats[tm][off_pm][0][18] -= 0.5
                    self.qtr_stats[tm][off_pm][1][0][18] -= 0.5
                    self.qtr_stats[tm][off_pm][1][1][18] -= 0.5
                    # print(off_pm, self.qtr_stats[tm][off_pm][0][18])
        self.plyrs_oncourt = new['R']

    def qtr_end_pm(self, n, tar, pmlst):    # 一节结束，更新球员本节数据到self.tdbxs的对应时间段
        for tm in range(2):
            if 'team' not in tar[tm][n]:
                tar[tm][n]['team'] = np.zeros((self.num_items,))
            tar[tm][n]['team'] += pmlst[tm]['team']
            for pm in pmlst[tm]:
                if pm != 'team':
                    if pm not in tar[tm][n]:
                        tar[tm][n][pm] = [np.zeros((self.num_items,)), [np.zeros((self.num_items,)), np.zeros((self.num_items,))]]
                    pmlst[tm][pm][0][20] = pmlst[tm][pm][1][0][17] - pmlst[tm][pm][1][1][17]
                    tar[tm][n][pm][0] += pmlst[tm][pm][0]
                    tar[tm][n][pm][1][0] += pmlst[tm][pm][1][0]
                    tar[tm][n][pm][1][1] += pmlst[tm][pm][1][1]

    def cal_perc(self, tar, accurate=0):
        for i in range(3):
            ix = i * 3 + 2
            if not accurate:
                tar[ix] = float('%.3f' % (tar[ix - 2] / tar[ix - 1])) if tar[ix - 1] else float('nan')
            else:
                tar[ix] = tar[ix - 2] / tar[ix - 1] if tar[ix - 1] else float('nan')

    def qtr_end(self, qtr, new, end=0):    # 一节结束，整理本节数据（更新所有上过场球员的数据，包括基础和进阶）
        # 更新打至节末的球员的上场时间
        endt = MPTime(new['T']) if qtr < 4 else MPTime('%d:00.0' % (48 if qtr == 4 else 48 + 5 * (qtr - 4)))
        for tm in range(2):
            for off_pm in self.plyrs_oncourt[tm]:
                # print(qtr, off_pm)
                # print(new)
                assert off_pm in self.plyrs_mp
                self.qtr_stats[tm][off_pm][0][19] += (endt - self.plyrs_mp[off_pm]).secs()
        # 更新本节出场球员其它数据
        periods = [0, qtr]
        if qtr < 5:
            periods.append(9 if qtr < 3 else 10)
        for n in periods:
            self.qtr_end_pm(n, self.tdbxs, self.qtr_stats)
        # 待完成：更新单节进阶数据

        if not end:
            # 更新新的一节上场球员及上场时间点
            self.plyrs_oncourt = new['R']
            self.qtr_stats = [{}, {}]
            self.default_qtr()
            self.plyrs_mp = {}
            self.default_mp(new['T'])
        if end:
            # 计算各项命中率
            for tm in range(2):
                for qtr in range(11):
                    for pm in self.tdbxs[tm][qtr]:
                        if pm == 'team':
                            self.cal_perc(self.tdbxs[tm][qtr][pm])
                        else:
                            self.cal_perc(self.tdbxs[tm][qtr][pm][0])
                            self.cal_perc(self.tdbxs[tm][qtr][pm][1][0])
                            self.cal_perc(self.tdbxs[tm][qtr][pm][1][1])
        if end and 0:
            print('客队')
            for i in self.tdbxs[0][0]:
                if i == 'team':
                    print(i, list(self.tdbxs[0][0][i]))
                else:
                    print(i, list(self.tdbxs[0][0][i][0]))
            print('主队')
            for i in self.tdbxs[1][0]:
                if i == 'team':
                    print(i, list(self.tdbxs[1][0][i]))
                else:
                    print(i, list(self.tdbxs[1][0][i][0]))
            print(self.tdbxs[0][0]['team'])
            print(self.tdbxs[1][0]['team'])
            # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS 18BP 19MP 20+/-
            for pm in self.tdbxs[0][0]:
                if pm != 'team':
                    pmself = self.tdbxs[0][0][pm][0]    # 球员自身数据
                    pmtm = self.tdbxs[0][0][pm][1][0]    # 球员在场期间本队数据
                    pmop = self.tdbxs[0][0][pm][1][1]    # 球员在场期间敌队数据
                    astp = pmself[12] / (pmtm[0] - pmself[0]) if pmtm[0] - pmself[0] else float('nan')    # 助攻率
                    ast2to = pmself[12] / pmself[15] if pmself[15] else float('nan')    # 助攻失误比
                    drbp = pmself[10] / (pmtm[10] + pmop[9]) if pmtm[10] + pmop[9] else float('nan')    # 防守篮板率
                    orbp = pmself[9] / (pmtm[9] + pmop[10]) if pmtm[9] + pmop[10] else float('nan')    # 进攻篮板率
                    trbp = (pmself[9] + pmself[10]) / (pmtm[10] + pmop[9] + pmtm[9] + pmop[10]) if pmtm[10] + pmop[9] + pmtm[9] + pmop[10] else float('nan')    # 总篮板率
                    print(pm, astp, ast2to, orbp, drbp, trbp)
