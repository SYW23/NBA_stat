import sys
sys.path.append('../')
from util import gameMarkToSeason, gameMarkToDir, LoadPickle, writeToPickle, read_nba_pbp
from klasses.miscellaneous import MPTime
from klasses.Boxscore import Boxscore
from klasses.gameTools import actionTrans
from klasses.Play import Play
from stats_nba.Game_nba import Game_nba
from windows.tools import GameDetailEditor
import os
from tqdm import tqdm
import numpy as np
import copy

pm2pn = LoadPickle('D:/sunyiwu/stat/data/playermark2playername.pickle')
b2n_dict = LoadPickle('D:/sunyiwu/stat/stats_nba/b2n_dict.pickle')
n2b_dict = LoadPickle('D:/sunyiwu/stat/stats_nba/n2b_dict.pickle')
error_index = {0: ['FG', 'MK'], 1: ['FGA', 'MS'], 2: ['3P', 'MK'], 3: ['3PA', 'MS'], 4: ['FT', 'MK'], 5: ['FTA', 'MS'], 6: ['ORB', 'ORB'],
               7: ['DRB', 'DRB'], 8: ['TRB'], 9: ['AST', 'AST'], 10: ['STL', 'STL'], 11: ['BLK', 'BLK'], 12: ['TOV', 'TOV'], 13: ['PF', 'PF']}
rot_error = 0


def edit_gm(qtr, now, gm, i, type='bbr', st=''):
    qtr += 1
    if type == 'bbr':
        qtr_end = '%d:00.0' % (qtr * 12 if qtr < 5 else 48 + 5 * (qtr - 4))
        now = MPTime(qtr_end) - now
    playbyplay_editor_window = GameDetailEditor(gm=gm, title='第%d节 剩余%s    %s' % (qtr, now, str(i)), st=st)
    playbyplay_editor_window.loop()


class Game(object):
    # 构造参数：比赛唯一识别号，球员本队，常规赛or季后赛，对手球队简写
    def __init__(self, gm, RoP, team=None, op=None, HomeOrAts=[[4, 5], [2, 1]]):
        self.gm = gm[:-7] if 'pickle' in gm else gm    # 比赛唯一识别号
        self.RoP = RoP
        self.ss = gameMarkToSeason(self.gm)
        self.gameflow = LoadPickle(gameMarkToDir(self.gm, RoP))  # 比赛过程详细记录
        if team:
            self.HOA = 1 if team == self.gm[-3:] else 0  # 0客1主
            self.hometeam = team if self.HOA else op
            self.roadteam = op if self.HOA else team
        self.quarters = len(self.gameflow)
        self.playFoulTime = []
        self.bxscr = LoadPickle(gameMarkToDir(self.gm, RoP, tp=2))
        self.sum_score_error = []
        self.shootings_error = []
        self.nba_file = self.match_bbr_with_nbapbpfile(self.ss)
        self.nba_actions = []
        self.nba_lastMins = []
        self.bx_dict = {0: 3, 1: 4, 2: 6, 3: 7, 4: 9, 5: 10, 6: 11, 7: 12}

    def yieldPlay(self, qtr):
        '''
        yield比赛每条记录
        :param qtr: 节次
        :return: play
        '''
        for p in self.gameflow[qtr]:
            yield p

    def teamplyrs(self):
        '''
        返回比赛双方上场球员(bbr)
        :return: [[客队球员], [主队球员]]
        '''
        plyrs = [[], []]
        for i, tm in enumerate(self.bxscr[1]):
            for p in tm[1:-1]:
                if len(p) > 2:
                    plyrs[i].append(p[0])
        if self.gm == '200203290LAL':    # 首发也能记错
            plyrs[1][4], plyrs[1][5] = plyrs[1][5], plyrs[1][4]
        elif self.gm == '200212220TOR':    # 首发也能记错
            plyrs[1][3], plyrs[1][5] = plyrs[1][5], plyrs[1][3]
        elif self.gm == '201611080SAC':    # 首发也能记错
            plyrs[1][3], plyrs[1][6] = plyrs[1][6], plyrs[1][3]
        elif self.gm == '200111100MIA':    # 首发也能记错
            plyrs[1][4], plyrs[1][5] = plyrs[1][5], plyrs[1][4]
        elif self.gm == '200111100UTA':    # 首发也能记错
            plyrs[1][3], plyrs[1][10] = plyrs[1][10], plyrs[1][3]
        elif self.gm == '200111280DET':    # 首发也能记错
            plyrs[1][9], plyrs[1][1] = plyrs[1][1], plyrs[1][9]
        elif self.gm == '200203170CLE':    # 首发也能记错
            plyrs[0][3], plyrs[0][5] = plyrs[0][5], plyrs[0][3]
            plyrs[0][4], plyrs[0][6] = plyrs[0][6], plyrs[0][4]
        elif self.gm == '200204050MIA':    # 首发也能记错
            plyrs[0][3], plyrs[0][7] = plyrs[0][7], plyrs[0][3]
        elif self.gm == '200204110MEM':    # 首发也能记错
            plyrs[0][4], plyrs[0][5] = plyrs[0][5], plyrs[0][4]
        elif self.gm == '200204170PHO':    # 首发也能记错
            plyrs[1][4], plyrs[1][5] = plyrs[1][5], plyrs[1][4]
        elif self.gm == '200211030LAC':    # 首发也能记错
            plyrs[1][4], plyrs[1][7] = plyrs[1][7], plyrs[1][4]
        elif self.gm == '200303090ORL':    # 首发也能记错
            plyrs[1][4], plyrs[1][6] = plyrs[1][6], plyrs[1][4]
        elif self.gm == '201611130POR':    # 首发也能记错
            plyrs[0][2], plyrs[0][5] = plyrs[0][5], plyrs[0][2]
        elif self.gm == '201704110SAC':    # 首发也能记错
            plyrs[1][2], plyrs[1][5] = plyrs[1][5], plyrs[1][2]
        return plyrs

    def teamplyrs_nba(self):
        '''
        返回比赛双方上场球员(nba)
        :return: [[客队球员], [主队球员]]
        '''
        pms = []
        plyrs = self.gn.stats['awayTeam']['players']
        pms.append([[x['personId'], x['firstName'], x['familyName']] for x in plyrs])
        plyrs = self.gn.stats['homeTeam']['players']
        pms.append([[x['personId'], x['firstName'], x['familyName']] for x in plyrs])
        return pms

    # ==================== 格式标准化 ====================
    def match_bbr_with_nbapbpfile(self, ss):
        '''
        利用gm匹配对应的nba比赛pbp文件
        :param ss: 赛季
        :return: 匹配到的nba比赛pbp文件路径
        '''
        season_dir = 'D:/sunyiwu/stat/data_nba/origin/%s/' % ss
        pbps = os.listdir(season_dir)
        tms = [x.lower() for x in list(self.bxscr[0])]
        if 'pho' in tms:
            tms[tms.index('pho')] = 'phx'
        if 'brk' in tms:
            tms[tms.index('brk')] = 'bkn'
        if 'cho' in tms:
            tms[tms.index('cho')] = 'cha'
        # if tms == ['pho', 'brk'] or tms == ['brk', 'pho']:
        #     tms = ['phx', 'bkn']
        date = '%s-%s-%s' % (self.gm[:4], self.gm[4:6], self.gm[6:8])
        for pbp in pbps:
            if date in pbp and (tms[0] in pbp or tms[1] in pbp):
                return season_dir + pbp

    def nba_pbp_lastMin(self):
        '''
        筛选出nba比赛pbp记录中每节最后一分钟的所有记录
        :return: 每节最后一分钟的所有记录
        '''
        actionType = []
        plyrNo = []
        lastMin = []
        for ac in self.nba_actions:
            if ac['actionType'] not in actionType:
                actionType.append(ac['actionType'])
            if 'playerName' in ac and ac['playerName'] and ac['personId'] not in plyrNo:
                plyrNo.append(ac['personId'])
                # print(d['personId'], d['playerName'])
            if ac['actionType'] != 'period':
                t = ac['clock'][2:-1]
                if int(t.split('M')[0]) < 1 or (int(t.split('M')[0]) == 1 and t.split('M')[1] == '00.00'):
                    lastMin.append(ac)
        self.nba_lastMins = lastMin

    def match_rec_with_action(self, rec, s):
        '''
        匹配bbr网站pbp单条记录与nba网站pbp记录action
        :param rec: bbr网站pbp单条记录rec
        :param s: 时刻
        :return: 匹配到的nba网站pbp记录action（未匹配到返回None）
        '''
        # print(rec)
        for ix, ac in enumerate(self.nba_lastMins):
            if rec['Q'] == ac['period'] - 1:
                if ac['actionType'] and ac['actionType'] != 'period':
                    qnow = float(ac['clock'][2:-1].split('M')[1])
                    qnow_ = int(qnow) if self.ss < '2013_2014' or self.ss > '2016_2017' else round(qnow)
                    if self.ss >= '2013_2014' and self.ss <= '2016_2017' and '.5' in str(qnow) and int(qnow) % 2 == 0:
                        qnow_ += 1
                    if ac['clock'] == 'PT01M00.00S':
                        qnow_ = 60
                    # print(qnow_, ac)
                    # print(s, rec)
                    items = [actionTrans[ac['actionType']]] if isinstance(actionTrans[ac['actionType']], str) else actionTrans[ac['actionType']]
                    pm_nba = ac['playerName'].replace('-', '').replace("'", '').replace(' ', '') if ac['playerName'] else ''
                    if pm_nba == 'WorldPeace':
                        pm_nba = 'artesron'
                    elif pm_nba == 'Yao':
                        pm_nba = 'mingyao'
                    elif pm_nba == 'Sun':
                        pm_nba = 'yuesun'
                    elif pm_nba == 'DrewII':
                        pm_nba = 'drew'
                    elif pm_nba == 'Kleber':
                        pm_nba = 'klebi'
                    elif pm_nba == 'WebbIII':
                        pm_nba = 'webb'
                    elif pm_nba == 'KnoxII':
                        pm_nba = 'Knox'
                    elif pm_nba == 'Vinicius' and ac['playerNameI'] == 'M. Vinicius':
                        pm_nba = 'vinci'
                    elif pm_nba == 'Ayres' and ac['playerNameI'] == 'J. Ayres':
                        pm_nba = 'pende'
                    elif pm_nba == 'Mac' and ac['playerNameI'] == 'S. Mac':
                        pm_nba = 'mcclesh'
                    for item in items:
                        if (qnow_ == s or (self.ss > '2016_2017' and abs(qnow_ - s) < 2)) and item in rec:
                            # print(rec, ac)
                            if 'MK' in rec:
                                if 'MISS' not in ac['description'] and ac['scoreAway'] and rec['S'][0] == int(ac['scoreAway']) and rec['S'][1] == int(ac['scoreHome']) and pm_nba[:5].lower() in rec['MK'][0]:
                                    # print(ac)
                                    return 60 - qnow
                                elif 'MISS' not in ac['description'] and rec['MK'][1] == 1 and pm_nba[:5].lower() in rec['MK'][0] and rec['S'][rec['MK'][2]] + 1 == int(ac['scoreHome' if rec['MK'][2] else 'scoreAway']) and rec['S'][rec['MK'][2] - 1] == int(ac['scoreHome' if not rec['MK'][2] else 'scoreAway']):
                                    return 60 - qnow    # nba pbp有时会在两罚全中所得的两分在第一罚就全部加上，第二罚比分不变
                                else:
                                    continue
                            elif 'MS' in rec or 'ORB' in rec or 'DRB' in rec:
                                # print(rec)
                                pm = rec['MS'][0] if 'MS' in rec else (rec['ORB'] if 'ORB' in rec else rec['DRB'])
                                if pm_nba and pm_nba[:5].lower() in pm:
                                    # print(ac)
                                    if 'MS' in rec:
                                        if (rec['MS'][1] == 2 and '3PT' not in ac['description']) or (rec['MS'][1] == 3 and '3PT' in ac['description']) or (rec['MS'][1] == 1 and 'Free Throw' in ac['description']):
                                            return 60 - qnow
                                        else:
                                            continue
                                    return 60 - qnow
                                elif pm == 'Team' and not ac['playerName'] and len(str(ac['personId'])) == 10:
                                    # print(ac)
                                    return 60 - qnow
                                else:
                                    continue
                            elif 'SWT' in rec:
                                if pm_nba and pm_nba[:5].lower() in rec['SWT'][1]:
                                    # print(ac)
                                    return 60 - qnow
                                else:
                                    continue
                            elif 'D3S' in rec:
                                if ac['subType'] == 'Defense 3 Second':
                                    # print(ac)
                                    return 60 - qnow
                                else:
                                    continue
                            elif 'PF' in rec or 'TF' in rec or 'FF1' in rec or 'FF2' in rec or 'DTF' in rec or 'ETO' in rec:
                                if 'DTF' not in rec and pm_nba and pm_nba[:5].lower() in rec['plyr']:
                                    # print(ac)
                                    return 60 - qnow
                                elif 'TVL' in rec and rec['TVL'] == 'delay of game':
                                    return 60 - qnow
                                elif 'DTF' in rec and pm_nba and (pm_nba[:5].lower() in rec['DTF'][0] or pm_nba[:5].lower() in rec['DTF'][1]):
                                    return 60 - qnow
                                elif 'ETO' in rec and ac['subType'] == 'Excess Timeout Technical':
                                    return 60 - qnow
                                elif 'plyr' in rec and rec['plyr'] == 'Team' and (not ac['playerName'] or 'Technical' in ac['subType']):
                                    return 60 - qnow
                                elif ac['subType'] == 'Double Technical':
                                    return 60 - qnow
                                elif ac['subType'] == 'Double Personal':
                                    return 60 - qnow
                                else:
                                    continue
                            elif 'TOV' in rec:
                                if pm_nba[:5].lower() in rec['plyr']:
                                    return 60 - qnow
                                else:
                                    continue
                            else:
                                return 60 - qnow

    def game_scanner(self):
        '''
        回溯bbr网站pbp记录，生成自定义的数据格式record：[{rec1}, {rec2}, ...]
        梳理所有回合球权转换（包括节首）
        对比nba官网pbp记录，精确最后一分钟时间记录
        检查pbp记录时间单调性
        :return: 自定义的数据格式record
        '''
        record = []
        plyrs = self.teamplyrs()
        qtr_bp, qtr_ = -1, 1
        if self.gm == '199611010DET':
            record.append({'Q': 0, 'T': '0:00.0', 'JB': ['', '', ''], 'BP': 0})
            qtr_bp = 0
        if self.gm == '199611070POR':
            record.append({'Q': 0, 'T': '0:00.0', 'JB': ['', '', ''], 'BP': 1})
            qtr_bp = 1
        for qtr in range(self.quarters):
            if 0 < qtr <= 3 and qtr == qtr_:
                if qtr == 1 or qtr == 2:
                    # ========================第一节结束、第二节开始前，判断跳球记录是否缺失，若缺失，判断初始球权归属========================
                    if qtr == 1:
                        if qtr_bp == -1:  # 跳球记录缺失或跳球记录未记录得球者
                            if 'MK' in record[0] or 'TOV' in record[0] or ('PF' in record[0] and record[0]['PF'] == 'Offensive foul'):
                                qtr_bp = 0 if record[0]['BP'] else 1
                            elif 'MS' in record[0] or ('PF' in record[0] and (record[0]['PF'] == 'Shooting foul' or record[0]['PF'] == 'Personal foul')):
                                qtr_bp = record[0]['BP']
                            elif 'TVL' in record[0] and record[0]['TVL'] == 'def goaltending':
                                qtr_bp = record[0]['BP']
                            elif 'PVL' in record[0] and (record[0]['PVL'] == 'def goaltending' or record[0]['PVL'] == 'lane' or record[0]['PVL'] == 'kicked ball'):
                                qtr_bp = record[0]['BP']
                            elif 'PF' in record[0] and record[0]['PF'] == 'Loose ball foul':
                                qtr_bp = record[0]['BP']
                            elif 'JB' in record[0] and record[0]['BP'] == -1:    # 跳球记录未记录得球者
                                if 'PVL' in record[1]:
                                    if record[1]['PVL'] == 'jump ball' or record[1]['PVL'] == 'kicked ball':  # 200511160PHO    200511060LAL
                                        record[0]['BP'] = record[1]['BP']
                                        qtr_bp = record[0]['BP']
                                    elif record[1]['PVL'] == 'double lane' and 'MK' in record[2]:  # 199903050LAL
                                        record[0]['BP'] = 0 if record[2]['BP'] else 1
                                        record[1]['BP'] = 0 if record[2]['BP'] else 1
                                        qtr_bp = record[0]['BP']
                                elif 'TOV' in record[1]:
                                    if record[1]['TOV'] == 'jump ball violation.':    # 201011020DET
                                        record[0]['BP'] = record[1]['BP']
                                        qtr_bp = record[1]['BP']
                                    else:    # 199612260TOR
                                        record[0]['BP'] = 0 if record[1]['BP'] else 1
                                        qtr_bp = record[0]['BP']
                                elif 'D3S' in record[1]:
                                    record[0]['BP'] = record[1]['BP']
                                    qtr_bp = record[1]['BP']
                                elif 'FTO' in record[1] and 'TOV' in record[2]:    # 199701220BOS
                                    record[0]['BP'] = 0 if record[2]['BP'] else 1
                                    record[1]['BP'] = record[0]['BP']
                                    qtr_bp = record[0]['BP']
                                elif 'TVL' in record[1] and record[1]['TVL'] == 'jump ball' and 'TVL' not in record[2]:  # 201311290OKC
                                    record[0]['BP'] = record[1]['BP']
                                    qtr_bp = record[1]['BP']
                                elif 'MK' in record[1]:
                                    if 'PF' in record[2] and record[2]['drawn'] == record[1]['MK'][0]:    # 201201060TOR
                                        record[0]['BP'] = record[1]['BP']
                                        qtr_bp = record[1]['BP']
                                    else:    # 201212120PHO
                                        record[0]['BP'] = 0 if record[1]['BP'] else 1
                                        qtr_bp = 0 if record[1]['BP'] else 1
                                elif 'PF' in record[1]:
                                    if record[1]['PF'] == 'Shooting foul' or (record[1]['PF'] == 'Loose ball foul' and record[1]['T'] == '0:00.0'):
                                        record[0]['BP'] = record[1]['BP']
                                        qtr_bp = record[1]['BP']
                                    else:    # 199701250VAN
                                        record[0]['BP'] = record[1]['BP']
                                        qtr_bp = record[1]['BP']
                                elif self.gm in ['201404200HOU', '200803220PHI', '201501110SAC']:
                                    record.pop(0)
                                    qtr_bp = 0
                                elif self.gm in ['200103180GSW', '200511130BOS']:
                                    record.pop(0)
                                    qtr_bp = 1
                                elif self.gm in ['201802070MIA']:
                                    record.pop(1)
                                    record[0]['BP'] = 1
                                    qtr_bp = 1
                                else:
                                    qtr_bp = record[0]['BP']
                            if 'JB' not in record[0]:
                                record.insert(0, {'Q': 0, 'T': '0:00.0', 'BP': qtr_bp})
                        elif ('PVL' in record[0] and record[0]['PVL'] == 'jump ball') or ('TVL' in record[0] and record[0]['TVL'] == 'jump ball'):  # 跳球违例，修正球权记录
                            if 'JB' in record[1] and record[1]:
                                record[1]['BP'] = record[0]['BP']
                                qtr_bp = record[0]['BP']
                            else:
                                record.insert(1, {'Q': 0, 'T': '0:00.0', 'JB': ['', '', ''], 'BP': record[0]['BP']})
                                qtr_bp = record[0]['BP']
                    record.append({'Q': qtr, 'T': '12:00.0' if qtr == 1 else '24:00.0', 'BP': 0 if qtr_bp else 1})
                else:
                    record.append({'Q': qtr, 'T': '36:00.0', 'BP': qtr_bp})
                qtr_ += 1
            elif qtr > 3:
                # 加时初始球权
                record.append({'Q': qtr, 'T': '%d:00.0' % (48 + 5 * (qtr - 4)), 'BP': -1})
            for ply in self.yieldPlay(qtr):
                play = Play(ply, qtr)
                # ========================开始对一条记录进行处理========================
                # ========================跳球记录========================    [客场队员、主场队员]、得球方
                if len(play.play) == 2 and 'Jump' in play.play[1]:
                    if len(record) > 1 and len(record[-1]) == 3 and record[-1]['T'] in ['48:00.0', '53:00.0', '58:00.0', '63:00.0']:  # 加时开场跳球记录未缺失
                        record.pop()
                    rp, hp, bp = play.jumpball()
                    bpsn = 0 if bp in plyrs[0] else 1  # 球权 0客1主     !!!得球球员部分可能有特殊情况，待改
                    if play.now() == '0:00.0':
                        record.insert(0, {'Q': 0, 'T': play.now(), 'JB': [rp, hp, bp], 'BP': bpsn})
                        if len(record) == 2 and 'TVL' in record[-1] and record[-1]['TVL'] == 'delay of game':
                            record[-1]['BP'] = record[0]['BP']
                    else:
                        record.append({'Q': qtr, 'T': play.now(), 'JB': [rp, hp, bp], 'BP': bpsn})
                    if bp == '':
                        if len(record) > 1:    # 201612290UTA  42:49.0
                            record[-1]['BP'] = record[-2]['BP']
                        else:
                            bpsn = -1
                            record[-1]['BP'] = -1
                    if self.gm == '201803010SAC' and play.now() == '48:00.0':
                        record[-1]['BP'] = 1
                    if self.gm == '200612150LAL' and play.now() == '48:00.0':
                        record[-1]['BP'] = 0
                    if (self.gm == '199712270NYK' and play.now() == '0:00.0') or (self.gm == '201101210GSW' and play.now() == '0:00.0'):
                        record[-1]['BP'], qtr_bp = 0, 0
                    if qtr == 0 and (len(record) == 1 or record[-1]['T'] == '0:00.0') and self.gm not in ['199712270NYK', '201101210GSW']:  # 201412170TOR
                        qtr_bp = bpsn
                    elif qtr == 0 and len(record) == 2 and ('TVL' in record[0] and record[0]['TVL'] == 'delay of game') or ('PVL' in record[0] and record[0]['PVL'] == 'delay of game'):
                        qtr_bp = bpsn
                    elif len(record) > 2 and 'TOV' in record[-2] and record[-2]['TOV'] == 'turnover' and 'MS'in record[-3]:    # 纠正投篮不中-出现失误-跳球前的失误对球权判断的影响 201801050DEN  32:04.0
                        record[-2]['BP'] = record[-3]['BP']
                    elif len(record) > 2 and 'PF' in record[-2] and 'PF'in record[-3]:    # 球在空中时的double foul需通过跳球决定球权，之前的球权暂时延续上一条记录的球权 201912280CHI  39:23.0  https://official.nba.com/rule-no-12-fouls-and-penalties/#doublefoul Double Fouls
                        record[-2]['BP'] = record[-4]['BP']
                        record[-3]['BP'] = record[-4]['BP']
                    elif len(record) > 2 and 'PVL' in record[-3] and 'PVL' in record[-2] and \
                            record[-3]['PVL'] == 'lane' and record[-2]['PVL'] == 'lane':    # double lane需通过跳球决定球权， 200212230PHO  5:53.0
                        record[-2]['BP'] = record[-1]['BP']
                        record[-3]['BP'] = record[-1]['BP']
                    if self.gm == '201702130DEN':    # 开场双方跳球违例（特殊情况）
                        record[1], record[0] = record[0], record[1]
                        record[1], record[2] = record[2], record[1]
                        record[0]['BP'] = 1
                        record[1]['BP'] = 1
                else:
                    rec, ind = play.record()  # 若非长度为6的正常比赛记录行，则返回'', -1
                    s = play.score(ind=ind)
                    # ========================有得分或投丢========================
                    if s:
                        dd, mm = play.scoreType()
                        # ========================投进========================    [得分球员、得分、球员所属球队]、球权转换
                        if 'makes' in rec:
                            record.append({'Q': qtr, 'T': play.now(), 'MK': [rec.split(' ')[0], s, 0 if rec.split(' ')[0] in plyrs[0] else 1], 'D': dd, 'M': mm, 'BP': 0 if ind == 5 else 1})
                            # ========================助攻========================    助攻球员
                            if 'assist' in rec:
                                record[-1]['AST'] = rec.split(' ')[-1][:-1]
                                if record[-1]['AST'] == record[-1]['MK'][0]:
                                    opteam = 0 if record[-1]['MK'][0] in plyrs[0] else 1
                                    for x in plyrs[opteam]:
                                        if record[-1]['AST'][:-3] == x[:-3]:
                                            record[-1]['AST'] = x
                                            break
                                if record[-1]['AST'] == 'morrima02' and record[-1]['MK'][0] == 'morrima02':
                                    record[-1]['AST'] = 'morrima03'
                                elif record[-1]['AST'] == 'morrima03' and record[-1]['MK'][0] == 'morrima03':
                                    record[-1]['AST'] = 'morrima02'
                                elif record[-1]['AST'] == 'smithja02' and record[-1]['MK'][0] == 'smithja02':
                                    record[-1]['AST'] = 'smithjr01'
                                elif record[-1]['AST'] == 'smithjr01' and record[-1]['MK'][0] == 'smithjr01':
                                    record[-1]['AST'] = 'smithja02'
                                elif record[-1]['AST'] == 'willima02' and record[-1]['MK'][0] == 'willima02':
                                    record[-1]['AST'] = 'willima01'
                                elif record[-1]['AST'] == 'willima01' and record[-1]['MK'][0] == 'willima01':
                                    record[-1]['AST'] = 'willima02'
                                elif record[-1]['AST'] == 'greenje02' and record[-1]['MK'][0] == 'greenje02':
                                    record[-1]['AST'] = 'greenja01'
                                elif record[-1]['AST'] == 'greenja01' and record[-1]['MK'][0] == 'greenja01':
                                    record[-1]['AST'] = 'greenje02'
                                elif record[-1]['AST'] == 'willide01' and record[-1]['MK'][0] == 'willide01':
                                    record[-1]['AST'] = 'willide02'
                                elif record[-1]['AST'] == 'willide02' and record[-1]['MK'][0] == 'willide02':
                                    record[-1]['AST'] = 'willide01'
                                elif record[-1]['AST'] == 'martico01' and record[-1]['MK'][0] == 'martico01':
                                    record[-1]['AST'] = 'martica02'
                                elif record[-1]['AST'] == 'martica02' and record[-1]['MK'][0] == 'martica02':
                                    record[-1]['AST'] = 'martico01'
                            # ========================罚球进========================
                            if s == 1:
                                if '1 of 2' in rec or '1 of 3' in rec or '2 of 3' in rec:
                                    record[-1]['BP'] = 0 if record[-1]['MK'][0] in plyrs[0] else 1    # 修正某些clear path统计错犯规球员的情况    201912040CHI  29:46.0
                                    ftplyr = record[-1]['MK'][0]
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        if 'PF' in record[x - 1] and record[x - 1]['PF'] == 'Clear path foul':
                                            record[x - 1]['BP'] = 0 if ftplyr in plyrs[0] else 1
                                            t = x
                                            while t < -1:
                                                record[t]['BP'] = 0 if ftplyr in plyrs[0] else 1
                                                t += 1
                                            break
                                        x -= 1
                                if 'technical' in rec:  # 技术罚球，球权不转换
                                    if len(record) > 1 and 'BP' in record[-2]:
                                        record[-1]['BP'] = record[-2]['BP']
                                elif 'flagrant' in rec:  # 恶犯罚球，球权不转换，继续为罚球球员所在球队所有
                                    record[-1]['BP'] = record[-2]['BP']
                                    if self.gm == '200204160ATL':
                                        record[-1]['BP'] = 1
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        if ('MS' in record[x - 1] and record[x - 1]['MS'][0] not in plyrs[record[-1]['BP']]) or ('MK' in record[x - 1] and record[x - 1]['MK'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('ORB' in record[x - 1] and record[x - 1]['ORB'] not in plyrs[record[-1]['BP']]) or ('TOV' in record[x - 1]) or ('DRB' in record[x - 1] and record[x - 1]['BP'] != record[-1]['BP']):
                                            break
                                        else:
                                            record[x - 1]['BP'] = record[-1]['BP']
                                            x -= 1
                                elif '1 of 1' in rec:  # 投篮命中追加罚球，期间球权暂不转换
                                    if len(record) > 1 and 'PF' in record[-2] and record[-2]['PF'] == 'Away from play foul':
                                        if 'MK' in record[-3] and record[-3]['MK'][0] in plyrs[record[-2]['BP']]:    # 200512150SEA  14:03.0
                                            record[-1]['BP'] = 0 if record[-2]['BP'] else 1
                                        else:    # 200705060PHO  47:33.3
                                            record[-1]['BP'] = record[-2]['BP']
                                    elif len(record) > 2 and 'PF' in record[-3] and record[-3]['PF'] == 'Away from play foul':
                                        if 'MK' in record[-3] and record[-3]['MK'][0] in plyrs[record[-2]['BP']]:  # 200512150SEA  14:03.0
                                            record[-1]['BP'] = 0 if record[-2]['BP'] else 1
                                    elif len(record) > 1 and 'PF' in record[-2] and record[-2]['PF'] == 'Clear path foul':    # 200112200NYK  11:26.7
                                        record[-1]['BP'] = record[-2]['BP']
                                    elif len(record) > 1 and 'PF' in record[-2] and record[-2]['PF'] == 'Inbound foul':    # 200112200NYK  11:26.7
                                        record[-1]['BP'] = record[-2]['BP']
                                    else:
                                        x = -1
                                        flag = 0
                                        while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T'] and record[x]['Q'] == record[x - 1]['Q']:
                                            if 'PF' in record[x - 1] and record[x - 1]['PF'] == 'Away from play foul' and \
                                                    record[x - 1]['plyr'] in plyrs[record[-1]['BP']]:
                                                if 'MK' in record[x - 2] and record[x - 2]['MK'][0] not in plyrs[record[-1]['BP']] and record[x - 2]['MK'][1] > 1:
                                                    flag = 0
                                                elif 'ORB' in record[x - 3] and record[x - 3]['BP'] != record[-1]['BP']:
                                                    flag = 1
                                                break
                                            else:
                                                x -= 1
                                        if flag:    # 球权不转换
                                            record[-1]['BP'] = 0 if record[-1]['BP'] else 1
                                        else:
                                            while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T'] and record[x]['Q'] == record[x - 1]['Q']:
                                                if 'MS' in record[x - 1] and record[x - 1]['MS'][1] > 1:
                                                    break
                                                else:
                                                    record[x - 1]['BP'] = 0 if record[-1]['BP'] else 1
                                                    x -= 1
                                    if (self.gm == '201710200MIN' and play.now() == '47:55.0') or (self.gm == '200111080PHO' and play.now() == '35:55.3'):
                                        record[-1]['BP'] = 0
                                    if len(record) > 1 and 'PF' in record[-2] and record[-2]['PF'] == 'Personal foul':    # 201712290SAC  21:39.0
                                        record[-1]['BP'] = record[-2]['BP']
                                elif 'clear path' in rec:  # clear path罚球，球权不转换
                                    record[-1]['BP'] = 0 if record[-1]['MK'][0] in plyrs[0] else 1
                            if record[-1]['MK'][1] > 1 and self.gm[:4] >= '2019':
                                if len(record) > 1 and 'JB' in record[-2] and record[-2]['BP'] == record[-1]['BP']:    # 跳球出界却记录有得球球员    202008200IND 4:33.0
                                    record[-2]['BP'] = 0 if record[-1]['BP'] else 1
                                if len(record) > 2 and 'JB' in record[-3] and 'SWT' in record[-2] and record[-3]['BP'] == record[-1]['BP']:    # 类似上一条
                                    record[-2]['BP'] = 0 if record[-1]['BP'] else 1
                                    record[-3]['BP'] = 0 if record[-1]['BP'] else 1
                            if (self.gm == '201401020CHI' and play.now() == '41:13.0') or (self.gm == '201402070DET' and play.now() == '13:16.0') or \
                                    (self.gm == '201501030DEN' and play.now() == '18:55.0') or (self.gm == '201710300MIA' and play.now() == '31:01.0'):    # 未记录恶意犯规导致球权判断错误
                                record[-1]['BP'] = 1
                            if (self.gm == '201411070DEN' and play.now() == '11:56.0') or (self.gm == '201503120WAS' and play.now() == '35:37.0') or (self.gm == '' and play.now() == '15:02.0'):
                                record[-1]['BP'] = 0    # 未记录恶意犯规导致球权判断错误
                            if record[-1]['MK'][1] > 1 and len(record) > 1 and 'PF' in record[-2] and 'Shooting' in record[-2]['PF'] and record[-2]['T'] == record[-1]['T'] and record[-2]['drawn'] == record[-1]['MK'][0]:
                                record[-1], record[-2] = record[-2], record[-1]
                        # ========================投失========================    [出手球员、得分、球员所属球队]，球权暂时仍为进攻方所有
                        else:
                            if rec.split(' ')[0] == 'misses':
                                continue
                            record.append({'Q': qtr, 'T': play.now(),
                                           'MS': [rec.split(' ')[0], s, 0 if rec.split(' ')[0] in plyrs[0] else 1],
                                           'D': dd, 'M': mm, 'BP': 0 if ind == 1 else 1})
                            if len(record) == 2 and 'JB' in record[0] and record[0]['BP'] != record[1]['BP']:  # 201910280SAS
                                record[0]['BP'] = record[1]['BP']
                                qtr_bp = record[0]['BP']
                            # ========================盖帽========================    盖帽球员
                            if 'block by' in rec:
                                record[-1]['BLK'] = rec.split(' ')[-1][:-1]
                                if record[-1]['BLK'] == record[-1]['MS'][0]:
                                    opteam = 0 if record[-1]['BP'] else 1
                                    for x in plyrs[opteam]:
                                        if record[-1]['BLK'][:-3] == x[:-3]:
                                            record[-1]['BLK'] = x
                                            break
                            if len(record) > 1 and len(record[-2]) == 4 and record[-2]['T'] == '48:00.0':    # 加时开场跳球记录缺失
                                record[-2]['BP'] = record[-1]['BP']
                            # ========================丢罚球========================
                            if s == 1:
                                if 'clear path' in rec:  # clear path罚球，球权不转换
                                    record[-1]['BP'] = record[-2]['BP']
                                # 修正某些clear path统计错犯规球员的情况    201912040CHI  29:46.0
                                ftplyr = record[-1]['MS'][0]
                                x = -1
                                while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                    if 'PF' in record[x - 1] and record[x - 1]['PF'] == 'Clear path foul':
                                        record[x - 1]['BP'] = 0 if ftplyr in plyrs[0] else 1
                                        t = x
                                        while t < -1:
                                            record[t]['BP'] = 0 if ftplyr in plyrs[0] else 1
                                            t += 1
                                        break
                                    x -= 1
                                if 'technical' in rec:  # 技术罚球，球权不转换
                                    if len(record) > 1 and 'BP' in record[-2]:
                                        record[-1]['BP'] = record[-2]['BP']
                                elif 'flagrant' in rec:  # 恶犯罚球，球权不转换，继续为罚球球员所在球队所有
                                    record[-1]['BP'] = record[-2]['BP']
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        if ('MS' in record[x - 1] and record[x - 1]['MS'][0] not in plyrs[record[-1]['BP']]) or ('MK' in record[x - 1] and record[x - 1]['MK'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('ORB' in record[x - 1] and record[x - 1]['ORB'] not in plyrs[record[-1]['BP']]) or ('TOV' in record[x - 1]) or ('DRB' in record[x - 1] and record[x - 1]['BP'] != record[-1]['BP']):
                                            break
                                        else:
                                            record[x - 1]['BP'] = record[-1]['BP']
                                            x -= 1
                                elif '1 of 1' in rec:  # 追加罚球，期间球权暂不转换
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        if ('TF' in record[x - 1] and record[x - 1]['TF'] == 'Technical') or ('MS' in record[x - 1] and record[x - 1]['MS'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('MK' in record[x - 1] and record[x - 1]['MK'][0] not in plyrs[record[-1]['BP']]) or ('DRB' in record[x - 1] and record[x - 1]['BP'] != record[-1]['BP']) or ('TOV' in record[x - 1]):
                                            break
                                        else:
                                            record[x - 1]['BP'] = record[-1]['BP']
                                            x -= 1
                                if self.gm == '202008130BRK' and record[-1]['MS'][0] == 'allenja01' and play.now() == '31:07.0':
                                    record[-2]['BP'] = 1
                            if len(record) > 1 and 'JB' in record[-2] and record[-2]['BP'] != record[-1]['BP']:    # 跳球出界却记录有得球球员    202008200IND 4:33.0
                                record[-2]['BP'] = record[-1]['BP']
                            if len(record) > 2 and 'JB' in record[-3] and 'SWT' in record[-2] and record[-3]['BP'] != record[-1]['BP']:    # 类似上一条
                                record[-2]['BP'] = record[-1]['BP']
                                record[-3]['BP'] = record[-1]['BP']
                            if 'MS' in record[-1] and len(record) > 1 and record[-2]['BP'] != record[-1]['BP']:    # 出现以MS标记的球权转换记录
                                try:
                                    assert record[-2]['T'] != record[-1]['T']    # or record[-2]['Q'] != record[-1]['Q']
                                except:
                                    print(self.gm, record[-1])
                                if len(record[-2]) > 3 or record[-2]['T'] not in ['48:00.0', '53:00.0', '58:00.0', '63:00.0']:
                                    record.insert(-1, {'Q': record[-2]['Q'], 'T': record[-2]['T'], 'DRB': 'Team', 'BP': record[-1]['BP']})
                                else:
                                    record[-2]['BP'] = record[-1]['BP']
                    # ========================前场篮板========================    前板球员、球权
                    elif 'Offensive rebound' in rec:
                        if rec[-7:] != 'by Team':    # 球员篮板
                            record.append({'Q': qtr, 'T': play.now(), 'ORB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                            if play.now() == record[-2]['T'] and 'MK' in record[-2] and record[-2]['MK'][0] == rec.split(' ')[-1]:    # 纠正同一个人进球先于进攻篮板记录的问题
                                record[-1], record[-2] = record[-2], record[-1]
                        else:    # Offensive rebound by Team
                            record.append({'Q': qtr, 'T': play.now(), 'ORB': 'Team', 'BP': 0 if ind == 1 else 1})
                            if record[-1]['T'] == record[-2]['T'] and 'JB' in record[-2]:    # 纠正跳球出界后跳球记录中仍记有得球人的错误    201910240DET  44:48.0
                                record[-2]['BP'] = record[-1]['BP']
                    # ========================后场篮板========================    后板球员、球权
                    elif 'Defensive rebound' in rec:
                        if rec[-7:] != 'by Team':
                            record.append({'Q': qtr, 'T': play.now(), 'DRB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                        else:
                            record.append({'Q': qtr, 'T': play.now(), 'DRB': 'Team', 'BP': 0 if ind == 1 else 1})
                    # ========================换人========================    [上场球员、下场球员、换人球队]    球权不转换
                    elif 'enters' in rec:
                        tmp = rec.split(' ')
                        if tmp[0] == tmp[-1]:    # 自己换自己可还行
                            print('自己换自己error', self.gm, play.play)
                        if (tmp[0] not in plyrs[0] and tmp[0] not in plyrs[1]) or (tmp[-1] not in plyrs[0] and tmp[-1] not in plyrs[1]):
                            continue
                        record.append({'Q': qtr, 'T': play.now(), 'SWT': [tmp[0], tmp[-1], 0 if tmp[0] in plyrs[0] else 1]})
                        if record[-1]['SWT'][0] == 'martico01' and record[-1]['SWT'][1] == 'martico01':
                            record[-1]['SWT'][1] = 'martica02'
                        if len(record) > 1 and 'BP' in record[-2]:
                            record[-1]['BP'] = record[-2]['BP']
                        if len(record) > 1 and record[-1]['T'] == record[-2]['T'] and 'DRB' in record[-2] and record[-2]['DRB'] == record[-1]['SWT'][0]:
                            record[-1], record[-2] = record[-2], record[-1]
                    # ========================暂停========================
                    elif 'timeout' in rec:
                        tmp = rec.split(' ')
                        if tmp[0] == 'Official':  # 官方暂停
                            record.append({'Q': qtr, 'T': play.now(), 'OTO': ''})
                        elif '20' in tmp:  # 短暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'STO': 0 if ind == 1 else 1})
                        elif 'full' in tmp:  # 长暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'FTO': 0 if ind == 1 else 1})
                        elif tmp[0] == 'Turnover':  # excessive timeout turnover    失误球队
                            record.append({'Q': qtr, 'T': play.now(), 'ETT': 0 if ind == 1 else 1, 'BP': 0 if ind == 5 else 1})
                        elif tmp[0] == 'Excess':  # Excess timeout    犯规球队（记录在对方球队位置）
                            record.append({'Q': qtr, 'T': play.now(), 'ETO': 0 if ind == 5 else 1, 'BP': 0 if ind == 1 else 1})
                        else:
                            if 'no' not in rec:
                                print(rec, self.gm)
                        if ' no' not in rec and 'ETO' not in record[-1] and 'ETT' not in record[-1]:
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                    # ========================犯规========================
                    elif 'foul' in rec and 'offensive' not in rec:  # 犯规（小写的进攻犯规实为失误统计）
                        # print(rec)
                        tmp = rec.split(' ')
                        ix = tmp.index('by') if 'by' in tmp else -1
                        if 'Turnover' == tmp[0]:
                            plyr = tmp[2]
                            if not plyr:
                                continue
                            record.append({'Q': qtr, 'T': play.now(), 'TOV': 'foul', 'plyr': plyr, 'BP': 0 if ind == 5 else 1})
                        if 'Technical' in rec:  # 技术犯规（不记入个人犯规）    技犯类型、技犯球员、球权和之前保持一致
                            record.append({'Q': qtr, 'T': play.now(), 'TF': 'Technical', 'plyr': tmp[-1]})
                            if record[-1]['plyr'] and record[-1]['plyr'][-1] == 'c':
                                record[-1]['plyr'] = 'Team'
                            if record[-1]['plyr'] == 'by':
                                record[-1]['plyr'] = ''
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            continue
                        elif ('tech foul' in rec or 'Taunting technical' in rec) and 'Def 3 sec' not in rec:  # 技术犯规（不记入个人犯规）    技犯类型、技犯球员、球权和之前保持一致
                            if 'Ill def tech foul' in rec:
                                record.append({'Q': qtr, 'T': play.now(), 'D3S': tmp[-1]})
                            else:
                                record.append({'Q': qtr, 'T': play.now(), 'TF': ' '.join(tmp[:ix]), 'plyr': tmp[-1]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            continue
                        elif 'Def 3 sec' in rec:  # 防守3秒违例    违例球员、球权不变
                            if tmp[-1] == 'Team':    # 未记录球员的防守三秒记录在对方球队栏位    201810190LAC  7:37.0
                                record.append({'Q': qtr, 'T': play.now(), 'D3S': tmp[-1], 'BP': 0 if ind == 1 else 1})
                            else:
                                record.append({'Q': qtr, 'T': play.now(), 'D3S': tmp[-1]})
                                record[-1]['BP'] = 1 if record[-1]['D3S'] in plyrs[0] else 0
                            continue
                        elif 'Clear path' in rec:  # clear path（计入个人犯规和球队犯规）    犯规球员
                            record.append({'Q': qtr, 'T': play.now(), 'PF': 'Clear path foul', 'plyr': tmp[ix + 1]})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            continue
                        elif 'Teamfoul' in rec:  # 2000赛季后无此项
                            # if play.now() == record[-1]['T']:
                            if rec[-4:] != 'Team':
                                record.append({'Q': qtr, 'T': play.now(), 'TOV': 'Offensive foul', 'plyr': tmp[ix + 1], 'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else '', 'BP': 1 if tmp[ix + 1] in plyrs[0] else 0})
                            else:
                                record.append({'Q': qtr, 'T': play.now(), 'TF': 'Teamfoul', 'plyr': 'Team', 'BP': record[-1]['BP']})
                            if len(record) > 2 and 'PF' in record[-3] and 'TOV' in record[-2] and record[-3]['plyr'] == record[-2]['plyr'] and record[-3]['plyr'] == record[-1]['plyr']:
                                record.pop()
                            if len(record) > 1 and 'FF1' in record[-2] and record[-1]['plyr'] == record[-2]['plyr']:
                                record.pop()
                            if len(record) > 1 and 'FF2' in record[-2] and record[-1]['plyr'] == record[-2]['plyr']:
                                record.pop()
                            continue
                        elif 'Double technical foul' in rec:  # 双方技犯    [双方球员]
                            record.append({'Q': qtr, 'T': play.now(), 'DTF': [tmp[-3], tmp[-1]]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            continue
                        # assert 'drawn by' in rec
                        if 'Flagrant foul type 1' in rec:  # 一级恶意犯规（计入个人犯规和球队犯规）    犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF1': int(tmp[3]), 'plyr': tmp[ix + 1], 'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            if 'MK' in record[-2] and record[-2]['MK'][0] in plyrs[record[-1]['BP']]:    # 200102200CHI  30:37.0
                                record[-2]['BP'] = record[-1]['BP']
                            continue
                        if 'Flagrant foul type 2' in rec:  # 二级恶意犯规    犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF2': int(tmp[3]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            if 'MK' in record[-2] and record[-2]['MK'][0] in plyrs[record[-1]['BP']]:    # 201903060DET  37:53.0
                                record[-2]['BP'] = record[-1]['BP']
                            if 'FF2' in record[-2] and record[-2]['drawn'] == record[-1]['plyr'] and record[-1]['drawn'] == record[-2]['plyr']:    # 双方恶意犯规    201103300WAS  15:12.0
                                record[-1]['BP'] = record[-3]['BP']
                                record[-2]['BP'] = record[-3]['BP']
                            continue
                        if 'Double personal foul' in rec:  # 双方犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            # print(self.gm, play.play, rec)
                            record.append({'Q': qtr, 'T': play.now(), 'PF': ' '.join(tmp[:ix]), 'plyr': tmp[ix + 1]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            record.append({'Q': qtr, 'T': play.now(), 'PF': ' '.join(tmp[:ix]), 'plyr': tmp[ix + 3]})
                            record[-1]['BP'] = record[-2]['BP']
                            # print(record[-2:])
                            continue
                        if 'foul by' in rec:  # 其他犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            if rec[-2:] == 'by':
                                continue
                            record.append({'Q': qtr, 'T': play.now(), 'PF': ' '.join(tmp[:ix]), 'plyr': tmp[ix + 1], 'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            if not record[-1]['plyr']:
                                record[-1]['plyr'] = record[-1]['drawn']
                                record[-1]['drawn'] = ''
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            if record[-1]['PF'] == 'Away from play foul':  # 无球犯规追加罚球，之前进球后球权暂不转换
                                if len(record) > 1 and 'MK' in record[-2] and record[-2]['MK'][0] in plyrs[record[-1]['BP']]:
                                    record[-2]['BP'] = record[-1]['BP']
                            if record[-1]['PF'] == 'Shooting foul':  # 2+1或3+1罚球前的进球后球权暂不转换
                                if len(record) > 1 and 'MK' in record[-2] and record[-2]['MK'][0] in plyrs[record[-1]['BP']] and record[-2]['MK'][1] > 1:
                                    record[-2]['BP'] = record[-1]['BP']
                            if self.gm == '201401150PHO' and play.now() == '16:27.0' and record[-1]['plyr'] == 'youngni01':
                                record[-1]['BP'] = 0
                            if len(record) > 1 and 'PF' in record[-2] and record[-2]['PF'] == 'Personal foul' and \
                                    (record[-2]['drawn'] == record[-1]['plyr'] or record[-1]['drawn'] == record[-2]['plyr']) and self.gm != '201301140CHI':    # 双方犯规    201701110OKC  6:34.0
                                record[-2]['BP'] = record[-3]['BP']
                                record[-1]['BP'] = record[-3]['BP']
                    # ========================失误========================
                    elif 'Turnover' in rec:  # 失误    失误种类、失误球员、转换球权
                        tmp = rec.split(' ')
                        tp = rec[rec.index('(') + 1:rec.index(';')] if ';' in rec else rec[rec.index('(') + 1:-1]
                        plyr = 'Team' if 'by Team' in rec else tmp[2]
                        if not plyr and tp != '5 sec' and tp != '8 sec':
                            continue
                        record.append({'Q': qtr, 'T': play.now(), 'TOV': tp, 'plyr': plyr, 'BP': 0 if ind == 5 else 1})
                        # ========================抢断========================    抢断球员
                        if 'steal by' in rec:
                            record[-1]['STL'] = tmp[-1][:-1]
                            if record[-1]['STL'] == record[-1]['plyr']:
                                opteam = record[-1]['BP']
                                for x in plyrs[opteam]:
                                    if record[-1]['STL'][:-3] == x[:-3]:
                                        record[-1]['STL'] = x
                                        break
                        if len(record) > 1 and record[-1]['BP'] == record[-2]['BP'] and record[-1]['T'] != record[-2]['T'] and 'TVL' in record[-2] and record[-2]['TVL'] == 'jump ball' and self.gm > '2016':
                            record[-2]['BP'] = 0 if record[-2]['BP'] else 1
                            continue
                        if len(record) > 1 and record[-1]['BP'] == record[-2]['BP'] and record[-1]['T'] != record[-2]['T'] and not \
                                ('PF' in record[-2] and record[-2]['PF'] in ['Offensive foul', 'Offensive charge foul'] and record[-2]['plyr'] == record[-1]['plyr']) and \
                                len(record[-2]) != 3:
                            if qtr == 4 and record[-2]['Q'] == 3:
                                record.append({'Q': qtr, 'T': '48:00.0', 'BP': 0 if record[-1]['BP'] else 1})
                            else:
                                record.append({'Q': qtr, 'T': play.now(), 'DRB': 'Team', 'BP': 0 if record[-2]['BP'] else 1})
                            record[-1], record[-2] = record[-2], record[-1]
                        if self.gm == '199611090DAL' and play.now() == '37:05.0' and record[-1]['TOV'] == 'lost ball':
                            record.append({'Q': qtr, 'T': play.now(), 'DRB': 'Team', 'BP': 0})
                            record[-1], record[-2] = record[-2], record[-1]
                        if len(record) > 1 and 'FF1' in record[-2] and record[-1]['plyr'] == record[-2]['plyr']:
                            pass
                        if len(record) > 2 and 'PF' in record[-2] and record[-1]['plyr'] == record[-2]['plyr'] and record[-1]['TOV'] == 'turnover':    # 201910250CHO 23:31.4 投篮命中、无球队员防守犯规追加罚球
                            if record[-3]['BP'] == record[-1]['BP'] and record[-2]['PF'] != 'Away from play foul':
                                record.pop()
                                continue
                            if record[-2]['PF'] == 'Loose ball foul' and 'MK' in record[-3]:
                                record[-3]['BP'] = 0 if record[-3]['BP'] else 1
                        # if len(record) > 1 and 'PF' in record[-2] and record[-2]['PF'] not in ['Offensive foul', 'Loose ball foul'] and record[-1]['plyr'] == record[-2]['plyr'] and record[-1]['TOV'] == 'turnover':
                        #     record.pop()
                        #     continue
                    # ========================违例========================
                    elif 'Violation by' in rec:
                        if 'Team' in rec:  # 球队违例    违例种类、违例球队、转换球权
                            if 'jump ball' in rec:  # 跳球违例，明确初始球权
                                if not record:
                                    qtr_bp = 0 if ind == 5 else 1
                            record.append({'Q': qtr, 'T': play.now(), 'TVL': rec[rec.index('(') + 1:-1],
                                           'tm': 0 if ind == 1 else 1, 'BP': 0 if ind == 5 else 1})
                            if len(record) > 1 and record[-1]['TVL'] == 'kicked ball' and record[-2]['BP'] != record[-1]['BP']:
                                print('脚踢球失误', self.gm, record[-1])
                            if record[-1]['TVL'] == 'def goaltending':  # 防守干扰球，球权不做多余转换
                                if len(record) > 1 and record[-1]['T'] != record[-2]['T'] or (self.gm == '199711210WAS' and play.now() == '36:44.0'):
                                    record.pop()
                                    # print(self.gm, '无效TVL:', rec)
                                    continue
                                record[-1]['BP'] = 0 if record[-1]['BP'] else 1
                            elif record[-1]['TVL'] == 'delay of game':
                                if len(record) > 1 and 'BP' in record[-2]:
                                    record[-1]['BP'] = record[-2]['BP']
                            elif record[-1]['TVL'] == 'double lane':    # 罚球时双方同时提前进线则跳球决定球权
                                if len(record) > 1 and 'BP' in record[-2]:
                                    record[-1]['BP'] = record[-2]['BP']
                            elif record[-1]['TVL'] == 'jump ball' and len(record) > 2 and 'TVL' in record[-2] and record[-2]['TVL'] == 'jump ball':    # 跳球时双方同时违例
                                    record[-1]['BP'] = record[-3]['BP']
                                    record[-2]['BP'] = record[-3]['BP']
                            elif record[-1]['TVL'] == 'jump ball' and len(record) > 2 and 'MK' in record[-2] and 'PVL' in record[-3] and record[-3]['PVL'] == 'def goaltending':    # 201701060ORL  13:08.0
                                    record[-1], record[-3] = record[-3], record[-1]
                            elif record[-1]['TVL'] == 'jump ball' and len(record) > 2 and ('OTO' in record[-2] or 'FTO' in record[-2]) and 'PF' in record[-3]:    # 未知情况，跳球原因不明    201701200HOU  42:09.0
                                    record[-1]['BP'] = record[-2]['BP']
                            elif len(record) > 1 and play.now() == '48:00.0' and record[-1]['TVL'] == 'jump ball' and record[-2]['BP'] == -1:    # 201612200MIA
                                record[-2]['BP'] = record[-1]['BP']
                        else:  # 球员违例    违例种类、违例球员、转换球权
                            if 'jump ball' in rec:  # 跳球违例，明确初始球权
                                # print(record[-1])
                                if not record:
                                    qtr_bp = 0 if ind == 5 else 1
                                if len(record) > 1 and 'JB' in record[-1] and play.now() == '53:00.0':    # 200411230GSW 2OT
                                    record[-1]['BP'] = 0 if ind == 5 else 1
                            record.append({'Q': qtr, 'T': play.now(), 'PVL': rec[rec.index('(') + 1:-1],
                                           'plyr': rec.split(' ')[2], 'BP': 0 if ind == 5 else 1})
                            if record[-1]['PVL'] == 'double lane':    # 罚球时双方同时提前进线则跳球决定球权
                                if len(record) > 1 and 'BP' in record[-2]:
                                    record[-1]['BP'] = record[-2]['BP']
                            elif record[-1]['PVL'] == 'def goaltending':  # 防守干扰球，球权不做多余转换    201710170GSW  16:53.0
                                if len(record) > 1 and 'MK' in record[-2] and record[-1]['plyr'] in plyrs[record[-2]['BP']]:
                                    record[-1]['BP'] = record[-2]['BP']
                            elif record[-1]['PVL'] == 'lane':  # 罚球提前进线，球权不做多余转换    201710180DET  29:56.0
                                if len(record) > 1 and 'MK' in record[-2] and record[-2]['MK'][1] == 1 and \
                                        (record[-1]['plyr'] in plyrs[record[-2]['BP']] or record[-1]['plyr'] == ''):
                                    record[-1]['BP'] = record[-2]['BP']
                                elif (len(record) > 1 and 'ORB' in record[-2] and record[-2]['ORB'] == 'Team') or \
                                        (len(record) > 1 and 'PVL' in record[-2] and record[-2]['PVL'] == 'lane' and record[-2]['plyr'] == record[-1]['plyr']):
                                    record[-1]['BP'] = record[-2]['BP']
                            if self.gm == '200203010DEN' and record[-1]['T'] == '44:28.0':
                                record[-1]['BP'] = 0
                    # ========================回放========================
                    elif 'Instant' in rec:  # 若录像回放之后改判会是什么情况
                        if 'Challenge' in rec:  # 教练挑战    挑战球队0客1主
                            record.append({'Q': qtr, 'T': play.now(), 'CCH': 0 if ind == 1 else 1})
                        else:  # 录像回放    0客1主
                            record.append({'Q': qtr, 'T': play.now(), 'IRP': 0 if ind == 1 else 1})
                        if len(record) > 1 and 'BP' in record[-2]:
                            record[-1]['BP'] = record[-2]['BP']
                    # ========================驱逐========================
                    elif 'ejected' in rec:  # 驱逐出场    被驱逐球员
                        if rec.split(' ')[0]:
                            record.append({'Q': qtr, 'T': play.now(), 'EJT': rec.split(' ')[0]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                    # ========================防守三秒（违例）========================
                    elif 'Defensive three seconds' in rec:  # 防守三秒    违例球员
                        record.append({'Q': qtr, 'T': play.now(), 'D3S': rec.split(' ')[-1]})
                        record[-1]['BP'] = 1 if record[-1]['D3S'] in plyrs[0] else 0
                    # ========================例外情况（应无）========================
                    else:
                        if rec:
                            print(play.play, self.gm)
        # ========================梳理球队得分、加时初始球权确定========================
        for i in range(len(record)):
            if i == 0:
                record[i]['S'] = [0, 0]
            else:
                record[i]['S'] = copy.copy(record[i - 1]['S'])
                if 'MK' in record[i]:
                    record[i]['S'][record[i]['MK'][2]] += record[i]['MK'][1]
            if record[i]['BP'] == -1:
                if record[i]['T'] not in ['36:00.0', '48:00.0', '53:00.0', '58:00.0', '63:00.0']:
                    print(self.gm, i, record[i])
                if i + 1 < len(record):
                    if 'MK' in record[i + 1] or ('PF' in record[i + 1] and record[i + 1]['PF'] == 'Offensive foul') or 'TOV' in record[i + 1] or 'DRB' in record[i + 1]:
                        record[i]['BP'] = 0 if record[i + 1]['BP'] else 1
                    elif 'MS' in record[i + 1] or 'PF' in record[i + 1] or ('TVL' in record[i + 1] and record[i + 1]['TVL'] == 'jump ball'):
                        record[i]['BP'] = record[i + 1]['BP']
                    elif self.gm == '201611250NYK':
                        record[i]['BP'] = 1
                        record[i + 1]['BP'] = 1
                    elif self.gm == '201702080BRK':
                        record[i]['BP'] = 0
                        record[i + 1]['BP'] = 0
                else:
                    print(self.gm, i, record[i], 'Ah')
        # ========================精确最后一分钟时间记录（对比nba官网stats pbp记录）====================
        try:
            self.nba_actions, _ = read_nba_pbp(self.nba_file)
        except:
            print('匹配nba pbp文件失败', self.gm)
        if self.nba_actions:
            self.nba_pbp_lastMin()
            for ix, rec in enumerate(record):
                qtr_end = (rec['Q'] + 1) * 12 if rec['Q'] < 4 else 48 + (rec['Q'] - 3) * 5
                s = (MPTime('%d:00.0' % qtr_end) - MPTime(rec['T'])).secs()
                if not s % 1 and qtr_end - MPTime(rec['T']).min < 2:  # 时间未精确到0.1且在每节最后一分钟以内（包括倒计时1:00.0）
                    match = self.match_rec_with_action(rec, s)
                    if match:
                        # print(rec, match)
                        if ((self.ss < '2013_2014' and match >= float(rec['T'][rec['T'].index(':') + 1:]) or self.ss > '2016_2017') or self.ss >= '2013_2014' and self.ss <= '2016_2017') and match % 1:
                            tmp = rec['T'][:rec['T'].index(':')] + ':%02d.%d' % (int(match), round(match % 1 * 10)) if match != 60.0 else rec['T'][:rec['T'].index(':')] + ':00.0'
                            # print(tmp)
                            if int(tmp.split(':')[0]) == qtr_end and tmp.split(':')[1] != '00.0':
                                tmp = str(qtr_end - 1) + ':' + tmp.split(':')[1]
                            if record[ix - 1]['T'] <= tmp:
                                rec['T'] = tmp
                            else:
                                rec['T'] = record[ix - 1]['T']
                        elif str(match) < record[ix - 1]['T'][record[ix - 1]['T'].index(':') + 1:] and qtr_end - MPTime(record[ix - 1]['T']).min < 2:
                            rec['T'] = record[ix - 1]['T']
                    else:
                        # print(self.gm, '未匹配nba pbp')
                        # print(rec)
                        pass
        # ========================检查时间递增========================
        for ix, rec in enumerate(record):
            if ix and MPTime(rec['T']) < MPTime(record[ix - 1]['T']):
                print('时间混乱！', self.gm, rec)
                break
        # ========================换人记录时间检查========================
        sws = []
        if self.nba_actions:
            for ac in self.nba_actions:
                if ac['actionType'] == 'Substitution                            ':
                    try:
                        off_pn = n2b_dict[ac['personId']]
                        # print(ac)
                    except:
                        print(self.gm, ac)
                    qtr = ac['period'] - 1
                    qtr_end = (qtr + 1) * 12 if qtr < 4 else 48 + (qtr - 3) * 5
                    t = ac['clock']
                    t = '%d:%s.%s' % (int(t[2:4]), t[5:7], t[-3:-2])
                    t = MPTime('%d:00.0' % qtr_end) - MPTime(t)
                    sws.append([qtr, off_pn, str(t), 0])
                    # print(sws[-1])
            for ix, rec in enumerate(record):
                if 'SWT' in rec:
                    f = 0
                    for s in sws:
                        if not s[-1] and s[0] == rec['Q'] and s[1] == rec['SWT'][1] and s[2] == rec['T']:
                            s[-1] = 1
                            f = 1
                            break
                    if not f:
                        # print(rec)
                        for s in sws:
                            if not s[-1] and s[0] == rec['Q'] and s[1] == rec['SWT'][1]:
                                # print(rec, s)
                                rec['T'] = s[2]
                                s[-1] = 1
                                f = 1
                                break
                        if not f:
                            print(self.gm, '未匹配换人纪录', rec)
        # for ix, rec in enumerate(record):
        # t, bp = '', -1
        # for ix, rec in enumerate(record):
        #     if ix:
        #         if t:
        #             if rec['T'] == t:
        #                 if len(rec) > 4 and 'SWT' not in rec and 'FTO' not in rec and 'TVL' not in rec and 'IRP' not in rec and 'CCH' not in rec:
        #                     print(self.gm, rec)
        #             else:
        #                 t = ''
        #                 # print()
        #         if 'MK' in rec and rec['BP'] != record[ix - 1]['BP']:
        #             t, bp = rec['T'], rec['BP']
        #             # print(rec)
        return record

    # ==================== 修正数据 ====================
    @staticmethod
    def error_stats(a, b):
        '''
            对比nba官网和由record统计出的单场比赛球员数据，找出不一致的地方
            :param a: nba官网球员数据统计
            :param b: 由record统计出的球员数据
            :return: 数据不一致项目的下标 [...]
        '''
        assert len(a) == len(b)
        res = []
        for i in range(len(a)):
            if a[i] != b[i]:
                res.append(i)
        return res

    def match_record_b2n(self, rec):
        '''
        利用record记录匹配nba官网pbp记录
        :param rec: 单条record记录
        :return: 匹配到的nba官网pbp记录（未匹配到返回空{}）
        '''
        qtr_end = '%d:00.0' % (12 * (rec['Q'] + 1) if rec['Q'] < 4 else 48 + 5 * (rec['Q'] - 3))
        for r in self.gn.record:
            if r['Q'] == rec['Q']:
                if MPTime(r['T']) + MPTime(rec['T']) == MPTime(qtr_end):
                    if r['S'] == rec['S']:
                        # print(r)
                        if list(r)[2] == list(rec)[2]:
                            if 'MK' in r or 'MS' in r:
                                if ('MK' in r and rec['MK'][1] == r['MK'][1]) or ('MS' in r and rec['MS'][1] == r['MS'][1]):
                                    return r
                                else:
                                    continue
                            return r
        return {}

    def match_record_b2n_3pa(self, rec):
        '''
        利用record记录匹配nba官网pbp记录（专门匹配两分球错记为三分球的记录）
        :param rec: 单条record记录
        :return: 匹配到的nba官网pbp记录（未匹配到返回空{}）
        '''
        qtr_end = '%d:00.0' % (12 * (rec['Q'] + 1) if rec['Q'] < 4 else 48 + 5 * (rec['Q'] - 3))
        for r in self.gn.record:
            if r['Q'] == rec['Q'] and 'MS' in r:
                if MPTime(r['T']) + MPTime(rec['T']) == MPTime(qtr_end):
                    if r['MS'][1] == 2:
                        return r
                    else:
                        continue
        return {}

    def match_record_n2b(self, rec, record, picked):
        '''
        利用nba官网pbp记录匹配record记录
        :param rec: 单条record记录
        :param record: 自定义的数据格式
        :param picked: 记录每条record记录是否匹配过的数据格式
        :return: 匹配到的record记录（未匹配到返回空{}）
        '''
        qtr_end = '%d:00.0' % (12 * (rec['Q'] + 1) if rec['Q'] < 4 else 48 + 5 * (rec['Q'] - 3))
        for i, r in enumerate(record):
            if picked[i] == 0 and r['Q'] == rec['Q']:
                if MPTime(r['T']) + MPTime(rec['T']) == MPTime(qtr_end):
                    if 'S' not in r or 'S' not in rec:
                        print(self.gm, r, rec)
                    if r['S'] == rec['S']:
                        if list(r)[2] == list(rec)[2]:
                            if 'MK' in r or 'MS' in r:
                                item = 'MK' if 'MK' in r else 'MS'
                                if (r[item][1] == 1 and rec[item][1] == 1 and r['D'] == rec['D']) or (r[item][1] != 1 and r[item][1] == rec[item][1]):
                                    return i, r
                                else:
                                    continue
                            return i, r
        return 0, {}

    def game_analyser(self, record, T=0):
        '''
        对比bbr和NBA官网球员单场比赛技术统计，找出不一致并修正
        :param record: 自定义的数据格式
        :param T: 是否为复查
        :return: 修正后的record
        '''
        P = 1 if self.gm > '202011' else 0
        plyrs = self.teamplyrs()
        plyr_stats = {}
        ss = [0, 0]
        for i in record:
            # if 'whitnch01' in plyr_stats and plyr_stats['whitnch01'][0, 4] in [2, 3]:
            #     print(i, plyr_stats['whitnch01'])
            # 数据统计
            if 'MK' in i:
                ss[0 if i['MK'][0] in plyrs[0] else 1] += i['MK'][1]
                if i['MK'][1] == 1:
                    plyr_stats = self.plyrstats(i['MK'][0], [6, 7], plyr_stats)
                else:
                    if i['MK'][1] == 2:
                        plyr_stats = self.plyrstats(i['MK'][0], [0, 1], plyr_stats)
                    else:
                        plyr_stats = self.plyrstats(i['MK'][0], [0, 1, 3, 4], plyr_stats)
                    if 'AST' in i:
                        plyr_stats = self.plyrstats(i['AST'], [12], plyr_stats)
            elif 'MS' in i:
                if i['MS'][1] == 1:
                    plyr_stats = self.plyrstats(i['MS'][0], [7], plyr_stats)
                elif i['MS'][1] == 2:
                    plyr_stats = self.plyrstats(i['MS'][0], [1], plyr_stats)
                else:
                    plyr_stats = self.plyrstats(i['MS'][0], [1, 4], plyr_stats)
                if 'BLK' in i:
                    plyr_stats = self.plyrstats(i['BLK'], [14], plyr_stats)
            elif 'ORB' in i and i['ORB'] != 'Team':
                plyr_stats = self.plyrstats(i['ORB'], [9, 11], plyr_stats)
            elif 'DRB' in i and i['DRB'] != 'Team':
                plyr_stats = self.plyrstats(i['DRB'], [10, 11], plyr_stats)
            elif 'TOV' in i:
                if i['plyr'] != 'Team' and i['plyr'] != '':
                    plyr_stats = self.plyrstats(i['plyr'].rstrip(')'), [15], plyr_stats)
                if 'STL' in i:
                    plyr_stats = self.plyrstats(i['STL'], [13], plyr_stats)
            elif ('PF' in i and i['PF'] != 'Teamfoul') or 'FF1' in i or 'FF2' in i:
                if i['plyr'] and i['plyr'] != 'Team':
                    plyr_stats = self.plyrstats(i['plyr'], [16], plyr_stats)

        self.gn = Game_nba(self.nba_file, self.ss)
        if self.gn.nba_actions:
            self.gn.game_scanner()
            # for i in self.gn.record:
            #     print(i)
        plyrs_n = self.teamplyrs_nba()

        # 整理nba官网提供的比赛详细数据
        pms = [{}, {}]
        for i in range(2):
            plyrs_nba = self.gn.stats[['awayTeam', 'homeTeam'][i]]['players']
            for pm in plyrs_nba:
                if pm['statistics']['minutes']:
                    tmp = list(pm['statistics'].values())[1:-2]
                    if pm['personId'] not in n2b_dict:
                        print(self.gm)
                        print(pm)
                    pms[i][n2b_dict[pm['personId']]] = tmp[0:2] + tmp[3:5] + tmp[6:8] + tmp[9:]

        for i in range(2):
            for k in pms[i]:
                if k in plyr_stats:
                    tmp = pms[i][k]
                    gs = [int(x) for x in list(plyr_stats[k][0])]
                    gs = gs[:2] + gs[3:5] + gs[6:8] + gs[9:-1]
                    e = self.error_stats(tmp, gs)
                    if e:
                        for ix in e:
                            if ix != 8:
                                if T and P:    # 复查
                                    print('-' * 50)
                                    print(self.gm, k + '(%s):' % pm2pn[k], error_index[ix][0], str(tmp[ix]) + '—>' + str(gs[ix]))
                                # for r in self.gn.record:    # 检查bbr漏记的恶意犯规和特定种类的失误
                                #     if ix == 13 and 'PF' in r and 'Flagrant Type' in r['PF']:
                                #         print(r)
                                #         if 'PF' in r:
                                #             if '1' in r['PF']:
                                #                 st = 'Flagrant foul type 1 by %s' % n2b_dict[list(r['plyr'].keys())[0]]
                                #             else:
                                #                 st = 'Flagrant foul type 2 by %s' % n2b_dict[list(r['plyr'].keys())[0]]
                                #             edit_gm(r['Q'], MPTime(r['T']), self.gm, r, type='nba', st=st)
                                #     elif ix == 12 and 'TOV' in r:
                                #         if 'Illegal Screen' in r['TOV']:
                                #             print(r)
                                #             st = 'Turnover by %s (illegal screen)' % n2b_dict[list(r['plyr'].keys())[0]]
                                #             edit_gm(r['Q'], MPTime(r['T']), self.gm, r, type='nba', st=st)
                                #         elif '5 Second' in r['TOV']:
                                #             print(r)
                                #             if r['plyr']:
                                #                 st = 'Turnover by %s (5 sec)' % n2b_dict[list(r['plyr'].keys())[0]]
                                #                 edit_gm(r['Q'], MPTime(r['T']), self.gm, r, type='nba', st=st)
                                #         elif 'Punched' in r['TOV']:
                                #             print(r)
                                #             st = 'Turnover by %s (punched ball)' % n2b_dict[list(r['plyr'].keys())[0]]
                                #             edit_gm(r['Q'], MPTime(r['T']), self.gm, r, type='nba', st=st)
                                #         elif 'Player Out' in r['TOV']:
                                #             print(r)
                                #             st = 'Turnover by %s (out of bounds)' % n2b_dict[list(r['plyr'].keys())[0]]
                                #             edit_gm(r['Q'], MPTime(r['T']), self.gm, r, type='nba', st=st)
                                #         elif 'Basket from Below' in r['TOV']:
                                #             print(r)
                                #             st = 'Turnover by %s (enter basket from below)' % n2b_dict[list(r['plyr'].keys())[0]]
                                #             edit_gm(r['Q'], MPTime(r['T']), self.gm, r, type='nba', st=st)
                                #         elif 'Backcourt' in r['TOV']:
                                #             print(r)
                                #             if r['plyr']:
                                #                 st = 'Turnover by %s (back court)' % n2b_dict[list(r['plyr'].keys())[0]]
                                #                 edit_gm(r['Q'], MPTime(r['T']), self.gm, r, type='nba', st=st)
                                if len(error_index[ix]) > 1 and self.gn.record:
                                    # 确定得到球员姓名途径
                                    if error_index[ix][1] in ['MK', 'MS']:
                                        toName = "['%s'][0]" % error_index[ix][1]
                                    elif error_index[ix][1] in ['TOV', 'PF']:
                                        toName = "['plyr']"
                                    else:
                                        toName = "[error_index[ix][1]]"

                                # ===========================多记=============================
                                if self.gn.record and tmp[ix] < gs[ix]:
                                    for ii, rec in enumerate(record):
                                        if error_index[ix][1] in rec and eval('rec' + toName) == k:
                                            r = self.match_record_b2n(rec)
                                            # print(rec, toName, error_index[ix])
                                            # print(r)
                                            if ix == 3 and 'MS' in rec and rec['MS'][1] == 3:
                                                r_ = self.match_record_b2n_3pa(rec)
                                                if T and P and r_ and rec['MS'][1] != r_['MS'][1]:
                                                    print('得分不匹配', self.gm, r_)
                                                    st = '%s misses %d-pt %s from %d ft' % (
                                                    n2b_dict[list(r_['MS'][0])[0]], r_['MS'][1], 'jump shot' if 'jump shot' in r_['M'].lower() else 'layup', round(r_['D']))
                                                    if 'BLK' in r_:
                                                        st += ' (block by %s)' % n2b_dict[list(r_['BLK'])[0]]
                                                    print(st)
                                            if r:
                                                try:
                                                    rpm = n2b_dict[list(eval('r' + toName))[0]][:3].lower() if error_index[ix][1] in r and error_index[ix][1] != 'AST' else (r['AST'][:3].lower() if error_index[ix][1] == 'AST' and 'AST' in r else '')
                                                    if rpm != k[:3]:
                                                        if error_index[ix][1] in ['MK', 'MS']:
                                                            record[ii][error_index[ix][1]][0] = n2b_dict[list(eval('r' + toName))[0]]
                                                        elif error_index[ix][1] in ['TOV', 'PF']:
                                                            record[ii]['plyr'] = n2b_dict[list(eval('r' + toName))[0]]
                                                        else:
                                                            if error_index[ix][1] in r:    # 球员记录错误
                                                                # print()
                                                                if error_index[ix][1] != 'AST':
                                                                    if ('STL' in r and record[ii]['plyr'] == n2b_dict[list(eval('r' + toName))[0]]) or ('BLK' in r and record[ii]['MS'][0] == n2b_dict[list(eval('r' + toName))[0]]):
                                                                        print('球员记录错误', r)
                                                                    else:
                                                                        record[ii][error_index[ix][1]] = n2b_dict[list(eval('r' + toName))[0]]
                                                                else:
                                                                    for pn in plyrs_n[i]:
                                                                        if r['AST'] == pn[2]:
                                                                            record[ii]['AST'] = n2b_dict[pn[0]]
                                                            else:    # 多记录此项数据
                                                                # print('删除元素', error_index[ix][1])
                                                                record[ii].pop(error_index[ix][1])
                                                                # print(record[ii])
                                                                # print('无元素', r)
                                                        if T:
                                                            print(rec)
                                                            print(r)
                                                            print(plyrs_n[0])
                                                            print(plyrs_n[1])
                                                except:
                                                    print(self.gm)
                                                    print(r)
                                                    raise KeyError
                                            else:
                                                if T:
                                                    if 'DRB' not in rec and 'ORB' not in rec:
                                                        print('未在NBApbp记录中匹配到', self.gm, rec)
                                # ===========================漏记=============================
                                elif self.gn.record:
                                    if ix in [9, 11]:
                                        item = 'MS' if ix == 11 else 'MK'
                                        for ii, rec in enumerate(record):
                                            if item in rec and error_index[ix][1] not in rec:
                                                r = self.match_record_b2n(rec)
                                                if r and error_index[ix][1] in r:
                                                    if ix == 11:
                                                        record[ii][error_index[ix][1]] = n2b_dict[list(r[error_index[ix][1]])[0]]
                                                    else:
                                                        for pn in plyrs_n[i]:
                                                            if r['AST'] == pn[2]:
                                                                record[ii]['AST'] = n2b_dict[pn[0]]
                                    else:
                                        picked = np.zeros((len(record), ))
                                        for r in self.gn.record:
                                            ii, rec = self.match_record_n2b(r, record, picked)
                                            if rec and picked[ii] == 0:
                                                picked[ii] = 1
                                                # if error_index[ix][1] not in r:
                                                #     print('缺项', self.gm, r)
                                            else:
                                                if T and P and 'JB' in r:
                                                    print(self.gm, r)
                                                    print(self.teamplyrs())
                                                    print('Jump ball:  vs.  ( gains possession)')
                                                if T and P and error_index[ix][1] in r:
                                                    print(self.gm, r)
                                                    # if 'PF' in r and 'Shooting' in r['PF']:
                                                    #     edit_gm(r['Q'], MPTime(r['T']), self.gm, r, type='nba')
                                                    if 'MS' in r and r['MS'][1] > 1:
                                                        if T:
                                                            st = '%s misses %d-pt %s from %d ft' % (n2b_dict[list(r['MS'][0])[0]], r['MS'][1], 'jump shot' if 'jump shot' in r['M'].lower() else 'layup', round(r['D']))
                                                            if 'BLK' in r:
                                                                st += ' (block by %s)' % n2b_dict[list(r['BLK'])[0]]
                                                            print(st)
                                                            if ix == 3:
                                                                edit_gm(r['Q'], MPTime(r['T']), self.gm, r, type='nba', st=st)
                                                    elif 'MK' in r and r['MK'][1] > 1:
                                                        if T:
                                                            st = '%s makes %d-pt %s from %d ft' % (n2b_dict[list(r['MK'][0])[0]], r['MK'][1], 'jump shot' if 'jump shot' in r['M'].lower() else 'layup', round(r['D']))
                                                            if 'AST' in r:
                                                                for pn in plyrs_n[i-1]:
                                                                    if r['AST'] == pn[2]:
                                                                        ast = n2b_dict[pn[0]]
                                                                st += ' (assist by %s)' % ast
                                                            print(st)
                                                    elif 'DRB' in r:
                                                        st = 'Defensive rebound by %s' % n2b_dict[list(r['DRB'])[0]]
                                                        print(st)
                                                    elif 'ORB' in r:
                                                        st = 'Offensive rebound by %s' % n2b_dict[list(r['ORB'])[0]]
                                                        print(st)
                                                    elif 'JB' in r:
                                                        print('Jump ball:  vs.  ( gains possession)')
                                                        print(self.teamplyrs())
                                                    elif 'TOV' in r and r['plyr']:
                                                        st = 'Turnover by %s (%s)' % (n2b_dict[list(r['plyr'])[0]], r['TOV'].lower())
                                                        if 'STL' in r:
                                                            st = st[:-1] + '; steal by %s)' % n2b_dict[list(r['STL'])[0]]
                                                        print(st)
        # ======================== 生成回合进行指示变量 ========================
        if T:
            for ix, rec in enumerate(record):
                if 'D3S' in rec or ('TOV' in rec and 'STL' in rec) or \
                        ('ORB' in rec and not ('MS' in record[ix - 1] and record[ix - 1]['MS'][1] == 1)) or \
                        ('MS' in rec and rec['MS'][1] > 1) or \
                        ('DRB' in rec and rec['DRB'] != 'Team') or \
                        ('DRB' in rec and 'MS' in record[ix - 1] and rec['T'] != record[ix - 1]['T']) or \
                        ('JB' in rec and rec['JB'][2]) or \
                        ('PF' in rec and 'Offensive' not in rec['PF'] and 'Shooting' not in rec['PF']) or \
                        ('PF' in rec and 'Shooting' in rec['PF'] and 'MK' in record[ix - 1] and record[ix - 1]['MK'][1] > 1 and record[ix - 1]['BP'] == rec['BP']) or \
                        ('MK' in rec and rec['MK'][0] in plyrs[rec['BP']] and rec['MK'][1] > 1):
                    rec['POS'] = 1    # 此时被换下不用修正pace（-0.5）
                elif ('MK' in rec and rec['MK'][0] not in plyrs[rec['BP']]) or \
                        (('MK' in rec and rec['MK'][0] in plyrs[rec['BP']] and rec['MK'][1] == 1)) or \
                        'TOV' in rec or 'DRB' in rec or 'PF' in rec or 'MS' in rec or 'ORB' in rec or 'FF1' in rec or 'FF2' in rec or 'ETO' in rec:
                    rec['POS'] = 0    # 此时被换下需修正pace（-0.5）
                elif (('SWT' in rec or 'FTO' in rec or 'STO' in rec or 'OTO' in rec or 'CCH' in rec or 'IRP' in rec or 'TF' in rec or 'EJT' in rec) and rec['T'] != record[ix - 1]['T']):
                    rec['POS'] = 1
                elif 'SWT' in rec or 'FTO' in rec or 'STO' in rec or 'OTO' in rec or 'CCH' in rec or 'IRP' in rec or 'TF' in rec or 'EJT' in rec or 'TVL' in rec or 'PVL' in rec or 'DTF' in rec or 'ETT' in rec:
                    if 'POS' in record[ix - 1]:
                        rec['POS'] = record[ix - 1]['POS']
                else:
                    if len(rec) > 4 and not (len(rec) == 5 and 'JB' in rec and not rec['JB'][2]):
                        print(rec)
                        print()
            # print('\n')
        return record

    # ==================== 检查球权转换 ====================
    def find_time_series(self, record):
        '''
        检查时间点相同的记录前后顺序（影响球权转换）
        :param record: 自定义的数据格式
        :return: 无
        '''
        plyrs = self.teamplyrs()
        qtr = -1
        time_series = ''  # 连续相同的时间点
        tmp = []  # 连续相同的时间点的记录
        for i in record:
            if i['T'] == time_series and i['Q'] == qtr:
                tmp.append(i)
            else:
                if len(tmp) >= 1:
                    if len(tmp) > 1:
                        if len(set([x['BP'] for x in tmp])) != 1:
                            bp, flag, ix = tmp[0]['BP'], 0, 0
                            for r in tmp:  # 找到球权转换的那一条记录
                                if r['BP'] != bp:
                                    break
                                else:
                                    ix += 1
                            if ('DRB' in tmp[ix] and tmp[ix]['DRB'] in plyrs[bp]) or \
                                    ('MK' in tmp[ix] and tmp[ix]['MK'][0] not in plyrs[bp]) or \
                                    ('TOV' in tmp[ix] and tmp[ix]['plyr'] not in plyrs[bp] and tmp[ix]['plyr'] != 'Team' and tmp[ix]['plyr'] != '') or \
                                    ('PF' in tmp[ix] and tmp[ix]['plyr'] not in plyrs[bp]) or \
                                    ('TVL' in tmp[ix] and 'tm' in tmp[ix] and tmp[ix]['tm'] != bp) or \
                                    ('PVL' in tmp[ix] and tmp[ix]['plyr'] not in plyrs[bp]) or \
                                    ('FF1' in tmp[ix] and tmp[ix]['plyr'] not in plyrs[bp]) or \
                                    ('DRB' not in tmp[ix] and 'MK' not in tmp[ix] and 'TVL' not in tmp[ix] and
                                     'TOV' not in tmp[ix] and 'PF' not in tmp[ix] and 'JB' not in tmp[ix] and
                                     'PVL' not in tmp[ix] and 'FF1' not in tmp[ix] and 'ETO' not in tmp[ix]):
                                flag = 1
                                print('初次转换')
                            for r in range(ix, len(tmp)):
                                if tmp[r]['BP'] == bp:
                                    if 'MK' not in tmp[r] and 'TOV' not in tmp[r] and 'PVL' not in tmp[r] and \
                                            'DRB' not in tmp[r] and 'PF' not in tmp[r]:
                                        flag = 1
                                        print('二次转换')
                                    break
                            if flag:
                                print('error')
                                print('%s，连续%d条记录，时间点：%s' % (self.gm, len(tmp), time_series))
                                print('初始球权%d，球权转换index:' % bp, ix)
                                for r in tmp:
                                    print(r)
                                print()
                                edit_gm(i['Q'], MPTime(i['T']), self.gm, i)
                    tmp = [i]
                elif not tmp:
                    tmp.append(i)
                time_series = i['T']
                qtr = i['Q']

    def start_of_quarter(self, record):
        '''
        检查节首球权转换
        :param record: 自定义的数据格式
        :return: 无
        '''
        s = record[0]
        if s['BP'] not in [0, 1]:
            print(self.gm, '开场球权')
            print(record[0])
            edit_gm(0, MPTime('0:00.0'), self.gm, s)
        sbp = record[0]['BP']
        q = 1
        ot = 0
        for i in record:
            if i['Q'] == q:
                if q in [1, 2]:
                    if i['BP'] == sbp and self.gm != '201401180IND':
                        print('节首球权23', self.gm, q, i)
                        edit_gm(q, MPTime('%d:00.0' % (q * 12)), self.gm, i)
                elif q == 3:
                    if i['BP'] != sbp:
                        print('节首球权4', self.gm, q, i)
                        edit_gm(q, MPTime('36:00.0'), self.gm, i)
                else:
                    ot = q - 3
                q += 1
            if ot:
                if 'JB' not in i and i['BP'] == -1:
                    print('节首球权OT', self.gm, q - 1, i)
                    edit_gm(q - 1, MPTime('%d:00.0' % (48 + 5 * (q - 5))), self.gm, i)
                ot = 0

    # ==================== 生成轮换记录 ====================
    def rotation(self, record):
        '''
        生成比赛轮换记录
        :param record: 自定义的数据格式
        :return: 比赛轮换记录rot
        '''
        PoN = 0
        rot = []
        plyrs = self.teamplyrs()
        starters = [x[:5] for x in plyrs]
        rot.append({'Q': 0, 'T': '0:00.0', 'R': copy.deepcopy(starters), 'TN': '', 'S': [0, 0]})
        q = 3
        tseries = ''
        tmp = []
        ejt = []
        # print('首发', rot)
        for ix, i in enumerate(record):
            if PoN:
                print(i)
            if tmp and i['T'] != tmp[0][1]:
                tmp = []
            if ejt and i['T'] != ejt[0][1]:
                ejt = []
            if i['T'] != tseries:
                if rot[-1]['T'] == tseries:
                    rot[-1]['S'] = record[ix - 1]['S']
                tseries = i['T']
            # 第一节只需根据轮换记录确定场上球员
            if i['Q'] == 0:
                if 'SWT' in i:    # [0上、1下、2队]
                    assert i['SWT'][0] and i['SWT'][1]
                    starters[i['SWT'][2]] = [i['SWT'][0] if x == i['SWT'][1] else x for x in starters[i['SWT'][2]]]
                    rot.append({'Q': i['Q'], 'T': i['T'], 'R': copy.deepcopy(starters), 'TN': '', 'S': i['S']})
                    if PoN:
                        print('\t轮换', rot[-1])
            # 第二节开始节首登场人员不确定，全置为空
            elif len(i) == 4 or (i['Q'] > 3 and i['Q'] != q) or (self.gm == '200506190DET' and i['T'] == '48:00.0'):
                if i['Q'] > 3:
                    q += 1
                starters = [[], []]
                # 在boxscore统计中搜索是否有打满整节的球员，如有直接加入阵容
                if self.gm > '201810' and self.gm != '202008150POR':
                    qbx = self.bxscr[self.bx_dict[i['Q']]]
                    maxqt = '12:00' if i['Q'] < 4 else '5:00'
                    for qs in range(2):
                        for qp in qbx[qs][1:-1]:
                            if qp[1] == maxqt and qp[0] not in starters[qs]:
                                starters[qs].append(qp[0])
                # 隐身球员手动加入阵容= =
                if self.gm == '200011290VAN' and q == 5:
                    starters[1].append('bibbymi01')
                elif self.gm == '200012160MIN' and q == 4:
                    starters[1].append('szczewa02')
                elif self.gm == '200101040NYK' and q == 4:
                    starters[1].append('childch01')
                elif self.gm == '200101090CHH' and q == 4:
                    starters[0].append('drewbr01')
                elif self.gm == '200101090CHH' and q == 6:
                    starters[1].append('brownpj01')
                elif self.gm == '200101230ORL' and q == 5:
                    starters[1].append('millemi01')
                elif self.gm == '200103130HOU' and q == 5:
                    starters[1].append('norrimo01')
                elif self.gm == '200103140SAS' and q == 4:
                    starters[1].append('ferryda01')
                elif self.gm == '200103260CHI' and q == 4:
                    starters[0].append('cheanca01')
                elif self.gm == '200103270SAC' and q == 4:
                    starters[0].append('jacksma01')
                elif self.gm == '200111150HOU' and q == 4:
                    starters[1].append('williwa02')
                elif self.gm == '200111210UTA' and q == 4:
                    starters[0].append('jefferi01')
                elif self.gm == '200112190NJN' and q == 4:
                    starters[1].append('kittlke01')
                elif self.gm == '200112290MIL' and q == 4:
                    starters[1].append('hamda01')
                elif self.gm == '200201110CHH' and q == 4:
                    starters[0].append('richaqu01')
                elif self.gm == '200201120UTA' and q == 4:
                    starters[1].append('malonka01')
                elif self.gm == '200201290HOU' and q == 4:
                    starters[1].append('moblecu01')
                elif self.gm == '200203030WAS' and q == 4:
                    starters[0].append('millemi01')
                elif self.gm == '200203130ORL' and q == 4:
                    starters[0].append('majerda01')
                    starters[1].append('armstda01')
                elif self.gm == '200204030PHI' and q == 4:
                    starters[0].append('mariosh01')
                elif self.gm == '200205020NJN' and q == 4:
                    starters[1].append('kittlke01')
                elif self.gm == '200211220BOS' and q == 5:
                    starters[0].append('newblir01')
                elif self.gm == '200211260ATL' and q == 4:
                    starters[1].append('newblir01')
                elif self.gm == '200212160MIA' and q == 4:
                    starters[0].append('ricegl01')
                elif self.gm == '200212180CLE' and q == 4:
                    starters[1].append('parkesm01')
                elif self.gm == '200212200DET' and q == 4:
                    starters[1].append('robincl02')
                elif self.gm == '200301040WAS' and q == 4:
                    starters[0].append('millere01')
                elif self.gm == '200301250CLE' and q == 4:
                    starters[0].append('benjaco01')
                elif self.gm == '200302280MEM' and q == 4:
                    starters[1].append('battish01')
                elif self.gm == '200303210SEA' and q == 4:
                    starters[1].append('lewisra02')
                elif self.gm == '200304060BOS' and q == 4:
                    starters[1].append('delkto01')
                elif self.gm == '200304130MEM' and q == 4:
                    starters[0].append('hamilri01')
                elif self.gm == '200304190SAS' and q == 4:
                    starters[0].append('johnsjo02')
                elif self.gm == '200305100SAC' and q == 5:
                    starters[0].append('finlemi01')
                elif self.gm == '200305120BOS' and q == 5:
                    starters[1].append('mccarwa01')
                elif self.gm == '200305160PHI' and q == 4:
                    starters[1].append('colemde01')
                elif self.gm == '200311150MEM' and q == 4:
                    starters[1].append('poseyja01')
                elif self.gm == '200311290CLE' and q == 4:
                    starters[1].append('bremejr01')
                elif self.gm == '200401100SAS' and q == 4:
                    starters[1].append('bowenbr01')
                elif self.gm == '200401110LAC' and q == 4:
                    starters[0].append('millemi01')
                elif self.gm == '200403260MIA' and q == 4:
                    starters[0].append('howarjo01')
                    starters[1].append('jonesed02')
                elif self.gm == '200403310WAS' and q == 4:
                    starters[0].append('rogerro01')
                elif self.gm == '200405140DET' and q == 4:
                    starters[1].append('hunteli01')
                elif self.gm == '200411030CLE' and q == 4:
                    starters[0].append('jacksst02')
                elif self.gm == '200411080LAC' and q == 4:
                    starters[1].append('jaricma01')
                elif self.gm == '200412010SEA' and q == 4:
                    starters[0].append('boozeca01')
                elif self.gm == '200501130HOU' and q == 4:
                    starters[0].append('buforro01')
                elif self.gm == '200501140LAC' and q == 4:
                    starters[0].append('hasleud01')
                elif self.gm == '200503140ATL' and q == 4:
                    starters[1].append('guglito01')
                elif self.gm == '200504080TOR' and q == 4:
                    starters[0].append('childjo01')
                elif self.gm == '200504090LAC' and q == 4:
                    starters[0].append('bowenbr01')
                elif self.gm == '200504090LAC' and q == 5:
                    starters[1].append('jaricma01')
                elif self.gm == '200511260NYK' and q == 4:
                    starters[0].append('salmojo01')
                elif self.gm == '200512120PHI' and q == 4:
                    starters[0].append('hassetr01')
                    starters[1].append('korveky01')
                elif self.gm == '200512190MEM' and q == 5:
                    starters[1].append('battish01')
                elif self.gm == '200512280LAL' and q == 4:
                    starters[0].append('warriha01')
                elif self.gm == '200601100DEN' and q == 4:
                    starters[1].append('watsoea01')
                elif self.gm == '200602050TOR' and q == 4:
                    starters[0].append('moblecu01')
                elif self.gm == '200602080MIL' and q == 5:
                    starters[1].append('bellch01')
                elif self.gm == '200603150NYK' and q == 5:
                    starters[1].append('woodsqy01')
                elif self.gm == '200604020MIN' and q == 4:
                    starters[1].append('mccanra01')
                elif self.gm == '200604020TOR' and q == 5:
                    starters[0].append('westda01')
                elif self.gm == '200604060DEN' and q == 4:
                    starters[1].append('buckngr01')
                elif self.gm == '200604190MIN' and q == 4:
                    starters[0].append('jonesda02')
                elif self.gm == '200604290MEM' and q == 4:
                    starters[1].append('jonesed02')
                elif self.gm == '200612070NJN' and q == 4:
                    starters[1].append('houseed01')
                elif self.gm == '200612150LAL' and q == 4:
                    starters[1].append('waltolu01')
                elif self.gm == '200612150LAL' and q == 5:
                    starters[0].append('battish01')
                elif self.gm == '200612290CHA' and q == 4:
                    starters[1].append('anderde01')
                elif self.gm == '200612290CHA' and q == 5:
                    starters[1].append('anderde01')
                elif self.gm == '200701200HOU' and q == 4:
                    starters[0].append('diawaya01')
                elif self.gm == '200701240UTA' and q == 4:
                    starters[0].append('millemi01')
                elif self.gm == '200702210IND' and q == 5:
                    starters[0].append('boykiea01')
                elif self.gm == '200703040BOS' and q == 4:
                    starters[0].append('mccanra01')
                elif self.gm == '200703040BOS' and q == 5:
                    starters[0].append('smithcr01')
                elif self.gm == '200703230ATL' and q == 4:
                    starters[0].append('udokaim01')
                elif self.gm == '200703280BOS' and q == 4:
                    starters[1].append('westde01')
                elif self.gm == '200703300LAL' and q == 4:
                    starters[0].append('battish01')
                    starters[1].append('parkesm01')
                elif self.gm == '200711140CLE' and q == 4:
                    starters[1].append('gibsoda01')
                elif self.gm == '200711270CLE' and q == 4:
                    starters[1].append('gibsoda01')
                elif self.gm == '200712310CHA' and q == 4:
                    starters[1].append('feltora01')
                elif self.gm == '200801110CLE' and q == 4:
                    starters[1].append('gibsoda01')
                elif self.gm == '200801130TOR' and q == 5:
                    starters[1].append('delfica01')
                elif self.gm == '200801210ATL' and q == 4:
                    starters[0].append('jonesja02')
                elif self.gm == '200803020LAL' and q == 4:
                    starters[1].append('farmajo01')
                elif self.gm == '200803240DET' and q == 4:
                    starters[1].append('stuckro01')
                elif self.gm == '200803240GSW' and q == 4:
                    starters[1].append('jacksst02')
                elif self.gm == '200804160MIN' and q == 4:
                    starters[0].append('villach01')
                elif self.gm == '200804190SAS' and q == 5:
                    starters[0].append('barbole01')
                elif self.gm == '200811060POR' and q == 4:
                    starters[0].append('artesro01')
                elif self.gm == '200811160NYK' and q == 4:
                    starters[1].append('randoza01')
                elif self.gm == '200812010GSW' and q == 4:
                    starters[1].append('jacksst02')
                elif self.gm == '200812170CHI' and q == 4:
                    starters[0].append('thornal01')
                elif self.gm == '200812270HOU' and q == 5:
                    starters[1].append('battish01')
                elif self.gm == '200901030MIA' and q == 4:
                    starters[1].append('diawaya01')
                elif self.gm == '200901270LAL' and q == 4:
                    starters[1].append('vujacsa01')
                elif self.gm == '200902010SAC' and q == 4:
                    starters[0].append('watsoea01')
                elif self.gm == '200902170NYK' and q == 4:
                    starters[1].append('duhonch01')
                elif self.gm == '200903180HOU' and q == 5:
                    starters[0].append('princta01')
                elif self.gm == '200904010GSW' and q == 4:
                    starters[1].append('watsocj01')
                elif self.gm == '200904150MIA' and q == 4:
                    starters[0].append('afflaar01')
                elif self.gm == '200904150SAS' and q == 4:
                    starters[0].append('butlera01')
                elif self.gm == '200904300CHI' and q == 6:
                    starters[1].append('salmojo01')
                elif self.gm == '200911040NOH' and q == 4:
                    starters[1].append('stojape01')
                elif self.gm == '200912160MIL' and q == 4:
                    starters[0].append('fishede01')
                elif self.gm == '200912180DAL' and q == 4:
                    starters[0].append('arizatr01')
                elif self.gm == '200912190CHI' and q == 4:
                    starters[1].append('hinriki01')
                elif self.gm == '200912190PHI' and q == 4:
                    starters[1].append('greenwi01')
                elif self.gm == '200912230SAC' and q == 4:
                    starters[1].append('thompja02')
                elif self.gm == '201001300DAL' and q == 4:
                    starters[1].append('mariosh01')
                elif self.gm == '201002190MEM' and q == 5:
                    starters[1].append('randoza01')
                elif self.gm == '201003040MIA' and q == 4:
                    starters[1].append('richaqu01')
                elif self.gm == '201003190SAC' and q == 5:
                    starters[1].append('thompja02')
                elif self.gm == '201004140MIA' and q == 4:
                    starters[0].append('leeco01')
                    starters[1].append('jonesja02')
                elif self.gm == '201005240BOS' and q == 4:
                    starters[0].append('cartevi01')
                elif self.gm == '201011020WAS' and q == 4:
                    starters[1].append('hinriki01')
                elif self.gm == '201011050PHO' and q == 4:
                    starters[0].append('randoza01')
                elif self.gm == '201011060UTA' and q == 4:
                    starters[1].append('kirilan01')
                elif self.gm == '201012040CHI' and q == 4:
                    starters[0].append('battish01')
                elif self.gm == '201012180CLE' and q == 4:
                    starters[1].append('moonja01')
                elif self.gm == '201012260DET' and q == 4:
                    starters[1].append('hamilri01')
                elif self.gm == '201101190ORL' and q == 4:
                    starters[0].append('holidjr01')
                elif self.gm == '201101280OKC' and q == 4:
                    starters[1].append('greenje02')
                elif self.gm == '201102110CLE' and q == 4:
                    starters[0].append('gomesry01')
                elif self.gm == '201103110NJN' and q == 4:
                    starters[0].append('gomesry01')
                elif self.gm == '201103160MIL' and q == 4:
                    starters[0].append('richaja01')
                    starters[1].append('delfica01')
                elif self.gm == '201201050ATL' and q == 5:
                    starters[0].append('hasleud01')
                elif self.gm == '201201190HOU' and q == 4:
                    starters[0].append('arizatr01')
                elif self.gm == '201201250UTA' and q == 4:
                    starters[1].append('bellra01')
                elif self.gm == '201202190OKC' and q == 4:
                    starters[0].append('breweco01')
                elif self.gm == '201203060BOS' and q == 4:
                    starters[0].append('scolalu01')
                elif self.gm == '201203150UTA' and q == 4:
                    starters[1].append('burksal01')
                elif self.gm == '201203230OKC' and q == 4:
                    starters[0].append('ellinwa01')
                elif self.gm == '201203250ATL' and q == 6:
                    starters[0].append('harride01')
                elif self.gm == '201204060DAL' and q == 4:
                    starters[0].append('matthwe02')
                elif self.gm == '201204150LAL' and q == 4:
                    starters[0].append('kiddja01')
                elif self.gm == '201204220LAL' and q == 4:
                    starters[1].append('blakest01')
                elif self.gm == '201205070LAC' and q == 4:
                    starters[1].append('foyera01')
                elif self.gm == '201212010CLE' and q == 5:
                    starters[1].append('gibsoda01')
                elif self.gm == '201301260UTA' and q == 4:
                    starters[0].append('augusdj01')
                elif self.gm == '201301270BOS' and q == 4:
                    starters[1].append('terryja01')
                elif self.gm == '201302040UTA' and q == 4:
                    starters[1].append('willima02')
                elif self.gm == '201302100BOS' and q == 6:
                    starters[1].append('greenje02')
                elif self.gm == '201302260MIA' and q == 4:
                    starters[1].append('chalmma01')
                elif self.gm == '201304280BOS' and q == 4:
                    starters[1].append('bradlav01')
                elif self.gm == '201305250MEM' and q == 4:
                    starters[1].append('princta01')
                elif self.gm == '201311160WAS' and q == 4:
                    starters[0].append('dellama01')
                elif self.gm == '201311290SAC' and q == 4:
                    starters[0].append('collida01')
                elif self.gm == '201312020CHI' and q == 6:
                    starters[1].append('hinriki01')
                elif self.gm == '201312180MIL' and q == 4:
                    starters[1].append('antetgi01')
                elif self.gm == '201312180TOR' and q == 4:
                    starters[0].append('sessira01')
                elif self.gm == '201312220LAC' and q == 4:
                    starters[0].append('rubiori01')
                elif self.gm == '201312260CLE' and q == 5:
                    starters[1].append('jackja01')
                elif self.gm == '201401200CHI' and q == 4:
                    starters[1].append('butleji01')
                elif self.gm == '201402210ORL' and q == 4:
                    starters[1].append('mooreet01')
                elif self.gm == '201402270TOR' and q == 6:
                    starters[1].append('salmojo01')
                elif self.gm == '201403190DAL' and q == 4:
                    starters[0].append('hummero01')
                elif self.gm == '201403240NOP' and q == 4:
                    starters[1].append('riverau01')
                elif self.gm == '201403260CHA' and q == 4:
                    starters[1].append('hendege02')
                elif self.gm == '201404250POR' and q == 4:
                    starters[1].append('willima01')
                elif self.gm == '201410290CHO' and q == 4:
                    starters[0].append('dudleja01')
                elif self.gm == '201412020CHI' and q == 5:
                    starters[1].append('dunlemi02')
                elif self.gm == '201412080WAS' and q == 4:
                    starters[1].append('bealbr01')
                elif self.gm == '201412230OKC' and q == 4:
                    starters[0].append('blakest01')
                elif self.gm == '201412260MEM' and q == 4:
                    starters[1].append('leeco01')
                elif self.gm == '201502070DAL' and q == 4:
                    starters[0].append('batumni01')
                elif self.gm == '201502260PHO' and q == 4:
                    starters[1].append('knighbr03')
                elif self.gm == '201503010HOU' and q == 4:
                    starters[0].append('dellama01')
                    starters[1].append('arizatr01')
                elif self.gm == '201503060BRK' and q == 4:
                    starters[0].append('tuckepj01')
                elif self.gm == '201503200BRK' and q == 5:
                    starters[1].append('bogdabo02')
                elif self.gm == '201510300DET' and q == 4:
                    starters[1].append('caldwke01')
                elif self.gm == '201512140DET' and q == 4:
                    starters[1].append('morrima03')
                elif self.gm == '201512250MIA' and q == 4:
                    starters[1].append('dragigo01')
                elif self.gm == '201601040MIA' and q == 4:
                    starters[1].append('dragigo01')
                elif self.gm == '201601050DAL' and q == 5:
                    starters[1].append('matthwe02')
                elif self.gm == '201601140PHI' and q == 4:
                    starters[1].append('thompho01')
                elif self.gm == '201601180LAC' and q == 4:
                    starters[1].append('piercpa01')
                elif self.gm == '201601250SAC' and q == 4:
                    starters[1].append('gayru01')
                elif self.gm == '201602010IND' and q == 4:
                    starters[0].append('smithjr01')
                elif self.gm == '201603120TOR' and q == 4:
                    starters[0].append('winslju01')
                elif self.gm == '201604100PHI' and q == 4:
                    starters[0].append('ennisty01')
                elif self.gm == '201604240BOS' and q == 4:
                    starters[1].append('crowdja01')
                elif self.gm == '201605090POR' and q == 4:
                    starters[1].append('crabbal01')
                elif self.gm == '201611010MIA' and q == 4:
                    starters[0].append('koufoko01')
                    starters[1].append('waitedi01')
                elif self.gm == '201611300OKC' and q == 4:
                    starters[0].append('porteot01')
                    starters[1].append('roberan03')
                elif self.gm == '201612110PHO' and q == 4:
                    starters[0].append('gallola01')
                elif self.gm == '201612200MIL' and q == 4:
                    starters[1].append('hensojo01')
                elif self.gm == '201701080POR' and q == 5:
                    starters[1].append('crabbal01')
                elif self.gm == '201703100SAC' and q == 4:
                    starters[1].append('caulewi01')
                elif self.gm == '201703110CHO' and q == 4:
                    starters[0].append('hillso01')
                elif self.gm == '201703290ORL' and q == 4:
                    starters[0].append('grantje01')
                elif self.gm == '201705020BOS' and q == 4:
                    starters[0].append('porteot01')
                elif self.gm == '201710250LAL' and q == 4:
                    starters[0].append('oubreke01')
                elif self.gm == '201712230IND' and q == 4:
                    starters[0].append('crabbal01')
                elif self.gm == '201801100NYK' and q == 4:
                    starters[1].append('beaslmi01')
                elif self.gm == '201801140NYK' and q == 4:
                    starters[0].append('clarkia01')
                elif self.gm == '201801220NOP' and q == 5:
                    starters[1].append('milleda01')
                elif self.gm == '201802250MIL' and q == 4:
                    starters[1].append('bledser01')
                elif self.gm == '201803070DET' and q == 4:
                    starters[0].append('lowryky01')
                elif self.gm == '201803260CHO' and q == 4:
                    starters[0].append('leeco01')
                    starters[1].append('bacondw01')
                elif self.gm == '201803300LAL' and q == 4:
                    starters[0].append('terryja01')
                elif self.gm == '200304050CHI' and q == 4:
                    starters[1].append('roseja01')
                elif self.gm == '201101140HOU' and q == 4:
                    starters[0].append('jackja01')
                elif self.gm == '201304100ORL' and q == 4:
                    starters[0].append('dunlemi02')

                elif self.gm == '200012280DAL' and i['Q'] == 1:
                    starters[1].append('davishu01')
                elif self.gm == '201801060MIN' and i['Q'] == 1:
                    starters[0].append('cunnida01')
                elif self.gm == '200202030WAS' and i['Q'] == 2:
                    starters[0].append('millere01')
                elif self.gm == '200212040DEN' and i['Q'] == 2:
                    starters[0].append('chrisdo01')
                elif self.gm == '201002260LAL' and i['Q'] == 2:
                    starters[1].append('artesro01')
                elif self.gm == '201204090CHA' and i['Q'] == 2:
                    starters[1].append('biyombi01')
                elif self.gm == '201305180IND' and i['Q'] == 2:
                    starters[1].append('stephla01')
                elif self.gm == '200503270MIN' and i['Q'] == 2:
                    starters[1].append('hassetr01')
                elif self.gm == '200103180GSW' and i['Q'] == 3:
                    starters[0].append('barrybr01')
                elif self.gm == '200204080ORL' and i['Q'] == 3:
                    starters[1].append('garripa01')
                elif self.gm == '200305100SAC' and i['Q'] == 3:
                    starters[0].append('finlemi01')
                elif self.gm == '200703250MIN' and i['Q'] == 3:
                    starters[1].append('blounma01')
                elif self.gm == '200712120NYK' and i['Q'] == 3:
                    starters[1].append('jonesfr01')
                elif self.gm == '201503100BRK' and i['Q'] == 3:
                    starters[0].append('cunnida01')
                elif self.gm == '201503200SAS' and i['Q'] == 3:
                    starters[0].append('jerebjo01')
                elif self.gm == '201611280WAS' and i['Q'] == 3:
                    starters[0].append('templga01')
                elif self.gm == '201804250OKC' and i['Q'] == 3:
                    starters[0].append('inglejo01')
                elif self.gm == '200111210SAC' and i['Q'] == 3:
                    starters[0].append('anderde01')
                if 'JB' in i:
                    pms = [p for p in i['JB']]
                    for pm in pms:
                        if pm:
                            side = 0 if pm in plyrs[0] else 1
                            if pm not in starters[side]:
                                starters[side].append(pm)
                now = i['T']
                if now[now.index(':'):now.index('.')] != '00':
                    now = now[:now.index(':')] + ':00.0'
                rot.append({'Q': i['Q'], 'T': now, 'R': copy.deepcopy(starters), 'TN': '', 'S': i['S']})
                if PoN:
                    print('\t轮换', rot[-1])
            elif 'SWT' in i:    # 其它节次换人时可能出现多种复杂情况
                pmn, pmf, side = i['SWT'][0], i['SWT'][1], i['SWT'][2]    # 上下边
                assert pmn and pmf
                tmp.append([pmf, i['T']])
                if pmf in starters[side]:    # 下场球员尚在阵容记录中
                    if pmn not in starters[side]:    # 上场球员不在阵容中
                        starters[side] = [pmn if x == pmf else x for x in starters[side]]
                    else:    # 上场球员已在阵容中
                        starters[side].pop(starters[side].index(pmf))
                else:    # 下场球员已不在阵容记录中
                    if pmn not in starters[side]:
                        starters[side].append(pmn)
                        # if 'SWT' not in record[ix - 1] or ('SWT' in record[ix - 1] and pmf != record[ix - 1]['SWT'][0]):
                        x = -1
                        while rot[x]['Q'] == i['Q'] and pmf not in [p[0] for p in ejt]:
                            if pmf not in rot[x]['R'][side]:
                                rot[x]['R'][side].append(pmf)
                            try:
                                assert len(rot[x]['R'][side]) < 6
                            except:
                                print('back', self.gm, pmf)
                                print(rot[x])
                                print(rot[-1])
                                print(i)
                                # raise KeyError
                                edit_gm(i['Q'], MPTime(i['T']), self.gm, i)
                            x -= 1
                    try:
                        assert len(starters[0]) < 6 and len(starters[1]) < 6
                    except:
                        print('SWT', self.gm)
                        print(rot[-1])
                        print(i)
                        # raise KeyError
                        edit_gm(i['Q'], MPTime(i['T']), self.gm, i)
                rot.append({'Q': i['Q'], 'T': i['T'], 'R': copy.deepcopy(starters), 'TN': '', 'S': i['S']})
                if PoN:
                    print('\t轮换', rot[-1])
            elif 'EJT' in i:
                pm = i['EJT']
                ejt.append([pm, i['T']])
                assert pm
                side = 0 if pm in plyrs[0] else 1
                if pm in starters[side]:
                    starters[side].pop(starters[side].index(pm))
            else:
                pms = []
                k = list(i.keys())[2]
                if k == 'JB':
                    pms = i[k]
                elif k in ['MK', 'MS']:
                    if i['M'] != 'technical':
                        pms.append(i[k][0])
                    if 'AST' in i:
                        pms.append(i['AST'])
                    elif 'BLK' in i:
                        pms.append(i['BLK'])
                elif k in ['ORB', 'DRB', 'D3S']:
                    if i[k] and i[k] != 'Team':
                        pms.append(i[k])
                elif k in ['TOV', 'PF', 'FF1', 'FF2', 'PVL']:
                    if i['plyr'] and i['plyr'] != 'Team':
                        pms.append(i['plyr'])
                    if 'STL' in i:
                        pms.append(i['STL'])
                    elif 'drawn' in i:
                        pms.append(i['drawn'])
                else:
                    if 'FTO' not in i and 'OTO' not in i and 'STO' not in i and 'ETT' not in i and 'ETO' not in i and 'OTO' not in i and 'TVL' not in i and 'CCH' not in i and 'IRP' not in i and 'TF' not in i and 'DTF' not in i:
                        print('没有动静')
                        print(i)
                if pms:
                    for pm in pms:
                        if pm:
                            if self.gm == '200212260SEA' and pm == 'barrybr01' and i['T'] == '48:00.0':
                                continue
                            side = 0 if pm in plyrs[0] else 1
                            if PoN:
                                print(pm, side, tmp, starters)
                            if pm not in starters[side]:
                                if not tmp or (tmp and i['T'] == tmp[0] and pm not in [x[0] for x in tmp]):    # 处理同时刻换人记录先于下场球员动作记录的情况
                                    starters[side].append(pm)
                                    x = -1
                                    while rot[x]['Q'] == i['Q']:
                                        if pm not in rot[x]['R'][side]:
                                            rot[x]['R'][side].append(pm)
                                        try:
                                            assert len(rot[x]['R'][side]) < 6
                                        except:
                                            print('back', self.gm, pm)
                                            print(rot[x])
                                            print(rot[-1])
                                            print(i)
                                            # raise KeyError
                                            edit_gm(i['Q'], MPTime(i['T']), self.gm, i)
                                        x -= 1
                            try:
                                assert len(starters[0]) < 6 and len(starters[1]) < 6
                            except:
                                print(plyrs)
                                print(self.gm)
                                print(rot[-1])
                                print(i)
                                # raise KeyError
                                edit_gm(i['Q'], MPTime(i['T']), self.gm, i)
                    if PoN:
                        print('\t轮换', rot[-1])
        if 'S' not in rot[-1]:
            rot[-1]['S'] = record[-1]['S']
        rot = [x for x in rot if 'TN' in x]    # 仅保留节首以及换人时间点的记录
        rot_, t = [], ''
        # 保留同一时间点最后一条记录
        for i in range(1, len(rot)):
            try:
                assert len(rot[i]['R'][0]) == 5 and len(rot[i]['R'][1]) == 5 and len(set(rot[i]['R'][0])) == 5 and len(set(rot[i]['R'][1])) == 5
            except:
                print('error')
                print(plyrs)
                print(self.gm)
                print(rot[i])
                print()
                break
                # raise KeyError
            if rot[i]['T'] != rot[i - 1]['T'] or rot[i]['Q'] != rot[i - 1]['Q']:
                rot_.append(rot[i - 1])
        rot_.append(rot[-1])
        for r in rot_:
            if len(r['R'][0]) != 5 or len(r['R'][1]) != 5:
                print(self.gm, '轮换人数有误')
                raise KeyError
        return rot_

    # ==================== 轮换累计数据 ====================
    @staticmethod
    def plyrstats(pm, item, plyr_stats):
        '''
        根据record记录累计球员个人数据
        :param pm: pm
        :param item: 数据项目 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS
        :param plyr_stats: 球员个人数据记录 {pm1: np.zeros((1, 18)), pm2: ...}
        :return: plyr_stats
        '''
        # 球员个人数据梳理
        if pm and item:
            if pm not in plyr_stats:
                # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS
                plyr_stats[pm] = np.zeros((1, 18))
            for it in item:
                plyr_stats[pm][0, it] += 1
        return plyr_stats

    def replayer(self, record, rot):
        '''
        统计比赛轮换及累计数据，为轮换记录rot增加实时数据记录('team')
        :param record: 自定义的数据格式
        :param rot: 轮换记录
        :return: Boxscore类，rot
        '''
        plyrs = self.teamplyrs()
        plyrs_oncourt = rot[0]['R']
        switch_ptr = 1
        bxs = Boxscore(self.gm, plyrs_oncourt, plyrs)
        star_of_game = 0
        switchrec = {}
        # throwin = 0    # 记录下一回合是否开始（球是否进场）
        # 排除赛前的比赛延误警告和跳球违例
        for i in record:
            if ('TVL' in i and (i['TVL'] == 'delay of game' or i['TVL'] == 'jump ball')) or ('PVL' in i and (i['PVL'] == 'delay of game' or i['PVL'] == 'jump ball')):
                star_of_game += 1
            else:
                break
        bp = record[star_of_game]['BP']  # 初始球权
        bxs.update_pace(bp)
        record = record[star_of_game:]
        for ix, rec in enumerate(record):
            # ========================换人or节间========================
            if ix > 0 and record[ix - 1]['T'] == rot[switch_ptr]['T'] and \
                    rec['T'] != rot[switch_ptr]['T'] and (rec['Q'] == rot[switch_ptr]['Q'] or len(rec) == 4):
                # print(rec, rot[switch_ptr])
                # 节内发生换人，初始化上场球员数据（未到节间不清除下场球员数据）
                x = -1
                while ix + x > -1 and 'SWT' not in record[ix + x]:
                    x -= 1
                try:
                    assert 'SWT' in record[ix + x] or ix + x == -1
                except:
                    print(self.gm, rec, record[ix + x])
                    raise KeyError
                if ix + x != -1:
                    swr = record[ix + x]
                    switime = record[ix + x]['T']
                    while ix + x > -1 and ('SWT' in record[ix + x] or 'FTO' in record[ix + x] or 'OTO' in record[ix + x] or 'STO' in record[ix + x] or 'IRP' in record[ix + x]):
                        x -= 1
                    if ('POS' in record[ix + x] and record[ix + x]['POS']) or switime != record[ix + x]['T']\
                            and \
                            not ('MK' in record[ix - 1] and record[ix - 1]['D'] in [[1, 1], [2, 2], [3, 3]] and 'SWT' in record[ix - 2]) and \
                            not ('MK' in record[ix - 1] and record[ix - 1]['D'] in [[1, 1], [2, 2], [3, 3]] and 'MK' in record[ix - 2] and record[ix - 2]['MK'][1] == 1 and 'SWT' in record[ix - 3]):
                        # print('1型节中换人', swr)
                        # print(rot[switch_ptr]['T'])
                        # print()
                        bxs.swt(rot[switch_ptr])
                    else:
                        # print('2型节中换人', swr)
                        # print(rot[switch_ptr]['T'])
                        # print()
                        bxs.swt(rot[switch_ptr], t=1)
                    if rot[switch_ptr]['Q'] == 0:
                        rot[switch_ptr]['team'] = [bxs.qtr_stats[0]['team'].copy(), bxs.qtr_stats[1]['team'].copy()]
                    else:
                        rot[switch_ptr]['team'] = [bxs.qtr_stats[0]['team'] + bxs.tdbxs[0][0]['team'], bxs.qtr_stats[1]['team'] + bxs.tdbxs[1][0]['team']]
                if switch_ptr < len(rot) - 1:
                    switch_ptr += 1
            if ix > 0 and rec['Q'] != record[ix - 1]['Q']:
                # 一节结束，整理本节数据（更新所有上过场球员的数据，包括基础和进阶）
                # print(rot[switch_ptr])
                # print(rec)
                if rot[switch_ptr]['Q'] != rec['Q']:
                    bxs.swt(rot[switch_ptr])
                    if rot[switch_ptr]['Q'] == 0:
                        rot[switch_ptr]['team'] = [bxs.qtr_stats[0]['team'].copy(), bxs.qtr_stats[1]['team'].copy()]
                    else:
                        rot[switch_ptr]['team'] = [bxs.qtr_stats[0]['team'] + bxs.tdbxs[0][0]['team'], bxs.qtr_stats[1]['team'] + bxs.tdbxs[1][0]['team']]
                    if switch_ptr < len(rot) - 1:
                        switch_ptr += 1
                try:
                    assert rot[switch_ptr]['Q'] == rec['Q']
                except:
                    print(self.gm, rec)
                    raise KeyError
                # print(bxs.tdbxs)
                bxs.qtr_end(rec['Q'], rot[switch_ptr])
                # print(bxs.tdbxs)
            # ========================数据统计========================
            # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS 18BP 19MP 20RPTS 21HPTS
            pms = {}
            if 'MK' in rec:
                bxs.update_pts(rec['MK'], rec, rot[switch_ptr])
                if rec['MK'][1] == 1:
                    pms[rec['MK'][0]] = [6, 7]
                else:
                    pms[rec['MK'][0]] = [0, 1]
                    if rec['MK'][1] == 3:
                        pms[rec['MK'][0]] += [3, 4]
                    if 'AST' in rec:
                        pms[rec['AST']] = [12]
            elif 'MS' in rec:
                if rec['MS'][1] == 1:
                    pms[rec['MS'][0]] = [7]
                else:
                    pms[rec['MS'][0]] = [1]
                    if rec['MS'][1] == 3:
                        pms[rec['MS'][0]] += [4]
                if 'BLK' in rec:
                    pms[rec['BLK']] = [14]
            elif 'ORB' in rec and rec['ORB'] != 'Team':
                pms[rec['ORB']] = [9, 11]
            elif 'DRB' in rec and rec['DRB'] != 'Team':
                pms[rec['DRB']] = [10, 11]
            elif 'TOV' in rec:
                if rec['plyr'] != 'Team' and rec['plyr'] != '':
                    # print(rec)
                    pms[rec['plyr']] = [15]
                if 'STL' in rec:
                    pms[rec['STL']] = [13]
            elif ('PF' in rec and rec['PF'] != 'Teamfoul') or 'FF1' in rec or 'FF2' in rec:
                if rec['plyr'] and rec['plyr'] != 'Team':
                    pms[rec['plyr']] = [16]
            # print(rec, rot[switch_ptr])
            bxs.update_basic(pms, rec, rot[switch_ptr])
            # ========================pace统计========================
            if rec['BP'] != bp or (len(rec) == 4 and rec['T'] in ['12:00.0', '24:00.0', '36:00.0']) or (rec['T'] in ['48:00.0', '53:00.0', '58:00.0', '63:00.0'] and 'JB' in rec):    # 球权交换或节初或加时赛初跳球:
                try:
                    if not rec['T'] == '%d:00.0' % ((rec['Q'] + 1) * 12 if rec['Q'] < 4 else 48 + (rec['Q'] - 3) * 5):
                        assert 'MS' not in rec
                except:
                    print('MS转换球权', self.gm, rec, bp)
                    edit_gm(rec['Q'], MPTime(rec['T']), self.gm, rec)
                if not rec['T'] == '%d:00.0' % ((rec['Q'] + 1) * 12 if rec['Q'] < 4 else 48 + (rec['Q'] - 3) * 5):    # 排除节末
                    bp = rec['BP']
                    switchrec = rec
                    bxs.update_pace(bp)
                    # if rec['Q'] in [2]:
                    #     print(rec)
                    #     if 'wisemja01' in bxs.qtr_stats[0]:
                    #         print('wisemja01', bxs.qtr_stats[0]['wisemja01'][0][18])
                    #         print()
        # 赛末换人补充处理
        if 'team' not in rot[-1]:
            # print(self.gm, rot[switch_ptr]['T'])
            bxs.swt(rot[-1])
            rot[-1]['team'] = [bxs.qtr_stats[0]['team'] + bxs.tdbxs[0][0]['team'], bxs.qtr_stats[1]['team'] + bxs.tdbxs[1][0]['team']]
        # 全场比赛结束，整理剩余比赛数据
        bxs.qtr_end(record[-1]['Q'] + 1, rot[switch_ptr], end=1)
        # print(list(bxs.tdbxs[0][0]['team']))
        return bxs, rot

    def preprocess(self, load=0):
        if load:
            record = LoadPickle(gameMarkToDir(self.gm, self.RoP, tp=3))
        else:
            record = self.game_scanner()  # 比赛过程初回溯
        record = self.game_analyser(record)  # 球员数据检查
        record = self.game_analyser(record, T=1)  # 球员数据复查
        season_dir = 'D:/sunyiwu/stat/data/seasons_scanned/%s/%s/' % (self.ss, self.RoP if self.RoP == 'regular' else 'playoff')
        if not load:
            writeToPickle(season_dir + self.gm + '_scanned.pickle', record)
        self.find_time_series(record)  # 检查同时刻记录的球权转换
        self.start_of_quarter(record)  # 检查节首球权
        rot = self.rotation(record)  # 生成比赛轮换记录
        bxs, rot = self.replayer(record, rot)  # 生成比赛中球员轮换、在场累计等详细数据
        return record, rot, bxs


class GameBoxScore(object):
    def __init__(self, gm, RoP):
        self.gamemark = gm
        self.boxes = LoadPickle(gameMarkToDir(gm, RoP, shot=True))
        self.quarters = len(self.boxes) - 5 if len(self.boxes) > 3 else 0


if __name__ == '__main__':
    regularOrPlayoffs = ['regular', 'playoff']
    count_games = 0
    for season in range(2000, 2021):
        ss = '%d_%d' % (season, season + 1)
        # print(ss)
        for i in range(1):
            season_dir = 'D:/sunyiwu/stat/data/seasons_scanned/%s/' % ss
            if not os.path.exists(season_dir):
                os.mkdir(season_dir)
            season_dir = 'D:/sunyiwu/stat/data/seasons_scanned/%s/%s/' % (ss, regularOrPlayoffs[i])
            if not os.path.exists(season_dir):
                os.mkdir(season_dir)
            gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
            for gm in tqdm(gms):
                if 1:
                    count_games += 1
                    game = Game(gm, regularOrPlayoffs[i])
                    record, rot, bxs = game.preprocess()
                    # record = game.game_scanner()    # 比赛过程初步胜利
                    # record = game.game_analyser(record)    # 球员数据检查
                    # record = game.game_analyser(record, T=1)    # 球员数据复查
                    # # 保存文件
                    # if 1:
                    #     writeToPickle(season_dir + gm[:-7] + '_scanned.pickle', record)
                    # game.find_time_series(record)    # 检查同时刻记录的球权转换
                    # game.start_of_quarter(record)    # 检查节首球权
                    # rot = game.rotation(record)    # 生成比赛轮换记录
                    # bxs, rot = game.replayer(record, rot)    # 生成比赛中球员轮换、在场数据累积等详细数据
    print(count_games)

