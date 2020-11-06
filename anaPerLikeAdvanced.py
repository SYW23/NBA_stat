#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
sys.path.append('../')
from util import LoadPickle, playerMarkToDir
from klasses.miscellaneous import MPTime
from klasses.Player import Player
from klasses.Game import Game
import pandas as pd
import numpy as np
from tqdm import tqdm
pd.options.display.expand_frame_repr = False
pd.options.display.width = 50

RoF = ['regular', 'playoff']
pm2pn = LoadPickle('./data/playermark2playername.pickle')
plyr_ss = LoadPickle('./data/playerSeasonAverage.pickle')    # 球员所在球队及对手球队赛季场均数据
lg_ss = LoadPickle('./data/leagueSeasonAverage.pickle')    # 联盟球队赛季场均数据
games_td = [30, 5]
tartext = ['Steal', 'Turnover', 'Block', 'Assist', 'OffReb']
enforce = {}    # 球员生涯/赛季数据影响力因子均值（抢断失误盖帽助攻前板）
lg_season = {}    # 联盟生涯/赛季数据影响力因子均值（抢断失误盖帽助攻前板）
for tar_item in range(len(tartext)):    # 0抢断1失误2盖帽3助攻4前板
    enforce[tartext[tar_item]] = LoadPickle('./data/Enforce/player%sEnforce.pickle' % tartext[tar_item])
    lg_season[tartext[tar_item]] = LoadPickle('./data/Enforce/season%sEnforceRecord.pickle' % tartext[tar_item])

# for tar_item in range(len(tartext)):
#     print(tartext[tar_item], len(enforce[tartext[tar_item]]))
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
        # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS 18PACE
        lg_stats, lg_games, lg_gametime = lg_ss[ss][i][-1][2][6], lg_ss[ss][i][0], lg_ss[ss][i][1] / lg_ss[ss][i][0]
        # (Tm FGA + 0.4 * Tm FTA - 1.07 * (Tm ORB / (Tm ORB + Opp DRB)) * (Tm FGA - Tm FG) + Tm TOV)
        lg_poss = (lg_stats[1] + 0.4 * lg_stats[7] - 1.07 * (lg_stats[9] / lg_stats[11]) * (lg_stats[1] - lg_stats[0]) + lg_stats[15]) / lg_games / 2
        lg_pace = lg_poss * 48 / lg_gametime
        # VOP    = lg_PTS / (lg_FGA - lg_ORB + lg_TOV + 0.44 * lg_FTA)
        lg_vop = lg_stats[17] / (lg_stats[1] - lg_stats[9] + lg_stats[15] + 0.44 * lg_stats[7])
        # DRB%   = (lg_TRB - lg_ORB) / lg_TRB
        lg_drbp = (lg_stats[11] - lg_stats[9]) / lg_stats[11]
        # factor = (2 / 3) - (0.5 * (lg_AST / lg_FG)) / (2 * (lg_FG / lg_FT))
        lg_factor = 2 / 3 - (0.5 * lg_stats[12] / lg_stats[0]) / (2 * lg_stats[0] / lg_stats[6])
        print(lg_vop, lg_drbp, lg_factor)
        print(lg_pace, (lg_stats[1] - lg_stats[9] + lg_stats[15] + 0.44 * lg_stats[7]) / lg_games / 2)
        lgsum, lgames, lgmax, lgmin = 0, 0, [0, []], [30, []]
        for pm in tqdm(pms):
            if ss in enforce['Turnover'][pm][i][-1]:
                pmdir = playerMarkToDir(pm, RoF[i])
                if pmdir:
                    plyr = Player(pm, RoF[i])
                    ssgms = plyr.getSeason(ss)
                    num_games = ssgms.shape[0]
                    if num_games >= games_td[i]:
                        mpsum, scoresum = MPTime('0:00'), 0
                        for g in range(num_games):
                            sgm = ssgms[g:g+1]
                            mp = MPTime(sgm['MP'].values[0])
                            if mp.mf() != 0:
                                # ================ 球员单场数据准备 ================
                                mpsum += mp
                                pts = float(sgm['PTS'])
                                fta, ft, fga, fg, tpa, tp = float(sgm['FTA']), float(sgm['FT']), float(sgm['FGA']), float(sgm['FG']), float(sgm['3PA']), float(sgm['3P'])
                                drb, orb, trb = float(sgm['DRB']), float(sgm['ORB']), float(sgm['TRB'])
                                ast, stl, blk, tov, pf = float(sgm['AST']), float(sgm['STL']), float(sgm['BLK']), float(sgm['TOV']), float(sgm['PF'])
                                # ================ 球员本队数据准备 ================
                                gm = sgm['Playoffs' if i else 'Date'].values[0]
                                game = Game(gm, RoF[i])
                                tm_gametime = 48 if game.quarters == 4 else 48 + 5 * (game.quarters - 4)
                                plyrs = game.teamplyrs()
                                ts = 0 if pm in plyrs[0] else 1
                                os = 0 if ts else 1
                                ttl = [game.bxscr[1][0][-1], game.bxscr[1][1][-1]]
                                tm_ast, tm_fg = int(ttl[ts][14]), int(ttl[ts][2])
                                # 0.5 * ((Tm FGA + 0.4 * Tm FTA - 1.07 * (Tm ORB / (Tm ORB + Opp DRB)) * (Tm FGA - Tm FG) + Tm TOV) +
                                #        (Opp FGA + 0.4 * Opp FTA - 1.07 * (Opp ORB / (Opp ORB + Tm DRB)) * (Opp FGA - Opp FG) + Opp TOV))
                                tm_poss = int(ttl[ts][3]) + 0.4 * int(ttl[ts][9]) - 1.07 * (int(ttl[ts][11]) / (int(ttl[ts][11]) + int(ttl[os][12]))) * (int(ttl[ts][3]) - int(ttl[ts][2])) + int(ttl[ts][17])
                                op_poss = int(ttl[os][3]) + 0.4 * int(ttl[os][9]) - 1.07 * (int(ttl[os][11]) / (int(ttl[os][11]) + int(ttl[ts][12]))) * (int(ttl[os][3]) - int(ttl[os][2])) + int(ttl[os][17])
                                poss = (tm_poss + op_poss) / 2
                                # 48 * ((Tm Poss + Opp Poss) / (2 * (Tm MP / 5)))
                                tm_pace = poss * 48 / tm_gametime
                                # print(tm_pace)
                                # tm_pace = tm_stats[-1] / plyr_ss[pm][ss][0][i][0]  # 本队回合数
                                # ================ per分项计算 ================
                                # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS 18PACE
                                s1 = tp    # 3P
                                s2 = 2 / 3 * ast    # (2/3) * AST
                                s3 = (2 - lg_factor * (tm_ast / tm_fg)) * fg    # (2 - factor * (team_AST / team_FG)) * FG
                                s4 = ft * (1 - tm_ast / tm_fg / 6)    # (FT * 0.5 * (1 + (1 - (team_AST / team_FG)) + (2/3) * (team_AST / team_FG)))
                                s5 = - lg_vop * tov    # - VOP * TOV
                                s6 = - lg_vop * lg_drbp * (fga - fg)    # - VOP * DRB% * (FGA - FG)
                                s7 = - lg_vop * 0.44 * (0.44 + (0.56 * lg_drbp)) * (fta - ft)    # - VOP * 0.44 * (0.44 + (0.56 * DRB%)) * (FTA - FT)
                                s8 = lg_vop * (1 - lg_drbp) * (trb - orb)    # VOP * (1 - DRB%) * (TRB - ORB)
                                s9 = lg_vop * lg_drbp * orb    # VOP * DRB% * ORB
                                s10 = lg_vop * stl    # VOP * STL
                                s11 = lg_vop * lg_drbp * blk    # VOP * DRB% * BLK
                                s12 = - (pf * ((lg_stats[6] / lg_stats[16]) - 0.44 * (lg_stats[7] / lg_stats[16]) * lg_vop))    # - PF * ((lg_FT / lg_PF) - 0.44 * (lg_FTA / lg_PF) * VOP) ]
                                # ================ 综合数据值 ================
                                score = s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + s9 + s10 + s11 + s12
                                score = score / mp.mf()
                                score *= (lg_pace / tm_pace)
                                # print(pm, num_games, score)
                                scoresum += score
                                lgsum += score
                                lgames += 1
                                if mp.mf() > 15:
                                    if score > lgmax[0]:
                                        lgmax[0] = score
                                        lgmax[1] = [pm2pn[pm], sgm['Playoffs' if i else 'Date'].values[0]]
                                    if score < lgmin[0]:
                                        lgmin[0] = score
                                        lgmin[1] = [pm2pn[pm], sgm['Playoffs' if i else 'Date'].values[0]]
                        tmp[pm] = scoresum / num_games / 1.105
        # print(tmp)
        lg_ascore = lgsum / lgames
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


for i in range(2):
    res_all_sorted = {}
    for k in sorted(res_all[i], key=res_all[i].__getitem__, reverse=True):
        res_all_sorted[k] = res_all[i][k]
    top10 = list(res_all_sorted.keys())[:50]
    for r in range(len(top10)):
        print(RoF[i], r + 1, top10[r], res_all_sorted[top10[r]])
    print()
