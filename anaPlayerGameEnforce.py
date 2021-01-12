#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
sys.path.append('../')
from util import LoadPickle, playerMarkToDir
from klasses.miscellaneous import MPTime
import pandas as pd
import numpy as np
pd.options.display.expand_frame_repr = False
pd.options.display.width = 50

RoF = ['regular', 'playoff']
pm2pn = LoadPickle('./data/playermark2playername.pickle')
plyr_ss = LoadPickle('./data/playerSeasonAverage.pickle')    # 球员所在球队及对手球队赛季场均数据
lg_ss = LoadPickle('./data/leagueSeasonAverage.pickle')    # 联盟球队赛季场均数据
games_td = [58, 5]
tartext = ['Steal', 'Turnover', 'Block', 'Assist', 'OffReb']
enforce = {}    # 球员生涯/赛季数据影响力因子均值（抢断失误盖帽助攻前板）
lg_season = {}    # 联盟生涯/赛季数据影响力因子均值（抢断失误盖帽助攻前板）
for tar_item in range(len(tartext)):    # 0抢断1失误2盖帽3助攻4前板
    enforce[tartext[tar_item]] = LoadPickle('./data/Enforce/player%sEnforce.pickle' % tartext[tar_item])
    lg_season[tartext[tar_item]] = LoadPickle('./data/Enforce/season%sEnforceRecord.pickle' % tartext[tar_item])

for tar_item in range(len(tartext)):
    print(tartext[tar_item], len(enforce[tartext[tar_item]]))
pms = list(enforce['Turnover'].keys())
print()

res_all = [{}, {}]
for season in range(2019, 2020):
    ss = '%d_%d' % (season, season + 1)
    print(ss)
    for i in range(2):
        tmp = {}
        lg_plus_minus = [0, 0, 0, 0, 0]
        for ix, tar in enumerate(tartext):
            lg_plus_minus[ix] = lg_season[tar][-1][ss][i][2][0]
        # ================ 联盟数据准备 ================
        lg_stats = lg_ss[ss][i][-1][2][6]
        lg_pace = lg_stats[-1] / lg_ss[ss][i][0] / 2
        lg_vop = lg_stats[-2] / lg_stats[-1]    # 得分/回合数
        lg_drbp = (lg_stats[11] - lg_stats[9]) / lg_stats[11]    # DRB/TRB
        lg_factor = (2 / 3) - (0.5 * (lg_stats[12] / lg_stats[0])) / (2 * (lg_stats[0] / lg_stats[6]))
        print('联盟进攻效率（分/回合）', lg_vop)
        print('防守篮板/总篮板占比', lg_drbp)
        print('联盟运动战单打能力', lg_factor)
        lgsum, lgames, lgmax, lgmin = 0, 0, [0, []], [30, []]
        for pm in pms:
            pmdir = playerMarkToDir(pm, RoF[i], tp=1)
            if pmdir:
                cr = LoadPickle(pmdir)
                if ss in cr['Season'].values and ss in plyr_ss[pm]:
                    cr_a = cr[cr['Season'] == ss][:1]
                    cr_s = cr[cr['Season'] == ss][1:]
                    num_games = cr_a['G']
                    num_games = int(num_games.values[0][:-3])
                    if num_games >= games_td[i] or int(cr_s['MP'].values[0].split(':')[0]) > 1600:
                        mp = MPTime(cr_a['MP'].values[0])
                        pts = float(cr_a['PTS'])
                        fta = float(cr_a['FTA'])
                        ft = float(cr_a['FT'])
                        fga = float(cr_a['FGA'])
                        fg = float(cr_a['FG'])
                        tpa = float(cr_a['3PA'])
                        tp = float(cr_a['3P'])
                        bga = fga - tpa
                        bg = fg - tp
                        fmiss = fta - ft
                        tmiss = tpa - tp
                        bmiss = bga - bg
                        drb = float(cr_a['DRB'])
                        orb = float(cr_a['ORB'])
                        trb = float(cr_a['TRB'])
                        ast = float(cr_a['AST'])
                        stl = float(cr_a['STL'])
                        blk = float(cr_a['BLK'])
                        tov = float(cr_a['TOV'])
                        pf = float(cr_a['PF'])
                        # 球员除得分外的数据帮助球队的得分期望
                        plus_minus = [0, 0, 0, 0, 0]    # 0Steal, 1Turnover, 2Block, 3Assist, 4OffReb
                        for ix, tar in enumerate(tartext):
                            if pm in enforce[tar] and ss in enforce[tar][pm][i][-1]:
                                ix_all = 1 if tar in ['Assist', 'Block'] else 2
                                plus_minus[ix] = enforce[tar][pm][i][-1][ss][ix_all] / enforce[tar][pm][i][-1][ss][0] if enforce[tar][pm][i][-1][ss][0] else 0
                                plus_minus[ix] /= lg_plus_minus[ix]
                        # 球员出手期望？
                        # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS 18PACE
                        # ================ 球员对手球队数据准备 ================
                        op_stats = plyr_ss[pm][ss][1][i][-1][2][6]
                        op_pace = op_stats[-1] / plyr_ss[pm][ss][1][i][0]    # 对手回合数
                        op_vop = op_stats[-2] / op_stats[-1]    # 对手得分/回合
                        op_drbp = (op_stats[11] - op_stats[9]) / op_stats[11]    # 对手DRB/TRB
                        op_sp = (op_stats[17] - op_stats[6]) / (op_stats[0] * 2 + op_stats[3])    # 对手运动战得分率（运动战实际得分/运动战出手理论最大得分）
                        op_ftp = op_stats[8]
                        # ================ 球员本队数据准备 ================
                        tm_stats = plyr_ss[pm][ss][0][i][-1][2][6]
                        tm_pace = tm_stats[-1] / plyr_ss[pm][ss][0][i][0]  # 本队回合数
                        tm_vop = tm_stats[-2] / tm_stats[-1]
                        tm_drbp = (tm_stats[11] - tm_stats[9]) / tm_stats[11]
                        # ================ 分项计算 ================
                        pts_ = pts
                        orb_ = orb * plus_minus[4]
                        drb_ = drb * (1 - op_drbp) * op_vop
                        ast_ = ast * plus_minus[3]
                        stl_ = stl * plus_minus[0]
                        blk_ = blk * plus_minus[2] * op_sp
                        tov_ = - tov * plus_minus[1]
                        # pf_ = - pf * op_stats[6] / tm_stats[16]
                        # bmiss_ = - tm_vop * tm_drbp * bmiss
                        # ================ 综合数据值 ================ 改进：1 投篮效率完全没有考虑！！！  2 盖帽需考虑对手命中率
                        # score = pts_ + drb * 0.45 + orb * plus_minus[4] + ast_ + stl * plus_minus[0] + blk * plus_minus[2] * 0.4 - tov * plus_minus[1] - pf * 1.2 - \
                        #         fmiss * 0.6 - 2 * bmiss * 0.36 - 3 * tmiss * 0.25
                        score = pts_ + drb_ + orb_ + ast_ + stl_ + blk_ + tov_
                        # score = pts + orb * orb_plus + ast * ast_plus + stl * stl_plus + blk * blk_plus - tov * tov_minus - pf * 2 - fmiss - 2 * bmiss - 3 * tmiss
                        score = score / mp.mf()
                        score *= (lg_pace / tm_pace)
                        lgsum += score
                        lgames += 1
                        if mp.mf() > 15:
                            if score > lgmax[0]:
                                lgmax[0] = score
                                lgmax[1] = [pm2pn[pm], ss]
                            if score < lgmin[0]:
                                lgmin[0] = score
                                lgmin[1] = [pm2pn[pm], ss]
                        # print(pm, num_games, score)
                        tmp[pm] = score
        # print(tmp)
        lg_ascore = np.mean(np.array(list(tmp.values())))
        print('联盟平均：', lg_ascore)
        print('单场最高：', lgmax)
        print('单场最低：', lgmin)
        for k in tmp:
            tmp[k] *= (15 / lg_ascore)
        res = {}
        for k in sorted(tmp, key=tmp.__getitem__, reverse=True):
            res['%s %s' % (pm2pn[k], ss)] = tmp[k]
        top10 = list(res.keys())[:20]
        for r in range(20):
            print(RoF[i], r + 1, top10[r], res[top10[r]])
        print()

        res_all[i] = {**res_all[i], **res}


# for i in range(2):
#     res_all_sorted = {}
#     for k in sorted(res_all[i], key=res_all[i].__getitem__, reverse=True):
#         res_all_sorted[k] = res_all[i][k]
#     top10 = list(res_all_sorted.keys())[:50]
#     for r in range(len(top10)):
#         print(RoF[i], r + 1, top10[r], res_all_sorted[top10[r]])
#     print()
