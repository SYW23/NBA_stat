import sys
sys.path.append('../')
from util import minusMinutes, gameMarkToDir, LoadPickle, writeToPickle
from klasses.miscellaneous import MPTime
from klasses.Play import Play
from windows.tools import GameDetailEditor
import os
from tqdm import tqdm
import numpy as np
import copy
import time

sum_score_error = []
shootings_error = []
odta_error = []
sbtp_error = []
rot_error = 0


def edit_gm(qtr, now, gm, i):
    qtr += 1
    qtr_end = '%d:00.0' % (qtr * 12 if qtr < 5 else 48 + 5 * (qtr - 4))
    now = MPTime(qtr_end) - now
    playbyplay_editor_window = GameDetailEditor(gm=gm, title='第%d节 剩余%s    %s' % (qtr, now, str(i)))
    playbyplay_editor_window.loop()


class Game(object):
    # 构造参数：比赛唯一识别号，球员本队，常规赛or季后赛，对手球队简写
    def __init__(self, gm, ROP, team=None, op=None, HomeOrAts=[[4, 5], [2, 1]]):
        self.gm = gm  # 比赛唯一识别号
        self.gameflow = LoadPickle(gameMarkToDir(gm, ROP))  # 比赛过程详细记录
        if team:
            self.HOA = 1 if team == gm[-3:] else 0  # 0客1主
            self.hometeam = team if self.HOA else op
            self.roadteam = op if self.HOA else team
        self.quarters = len(self.gameflow)
        self.playFoulTime = []
        self.pm2pn = LoadPickle('D:/sunyiwu/stat/data/playermark2playername.pickle')
        self.bxscr = LoadPickle(gameMarkToDir(gm, ROP, tp=2))
        self.sum_score_error = []
        self.shootings_error = []
        self.bx_dict = {0: 3, 1: 4, 2: 6, 3: 7, 4: 9, 5: 10, 6: 11, 7: 12}

    def yieldPlay(self, qtr):
        for p in self.gameflow[qtr]:
            yield p

    def teamplyrs(self):
        plyrs = [[], []]
        for i, tm in enumerate(self.bxscr[1]):
            for p in tm[1:-1]:
                if len(p) > 2:
                    plyrs[i].append(p[0])
        if self.gm == '200203290LAL':    # 首发也能记错
            plyrs[1][4], plyrs[1][5] = plyrs[1][5], plyrs[1][4]
        if self.gm == '200212220TOR':    # 首发也能记错
            plyrs[1][3], plyrs[1][5] = plyrs[1][5], plyrs[1][3]
        if self.gm == '201611080SAC':    # 首发也能记错
            plyrs[1][3], plyrs[1][6] = plyrs[1][6], plyrs[1][3]
        return plyrs

    def game_scanner(self):
        record = []
        plyrs = self.teamplyrs()
        foultype, totype, vltype = [], [], []
        qtr_bp, qtr_ = -1, 1
        if self.gm == '199611010DET':
            record.append({'Q': 0, 'T': '0:00.0', 'JB': ['', '', ''], 'BP': 0})
            qtr_bp = 0
        if self.gm == '199611070POR':
            record.append({'Q': 0, 'T': '0:00.0', 'JB': ['', '', ''], 'BP': 1})
            qtr_bp = 1
        for qtr in range(self.quarters):
            if 0 < qtr < 4 and qtr == qtr_:
                if qtr == 1 or qtr == 2:
                    # print(record[0], qtr_bp)
                    # 第一节结束、第二节开始前，判断跳球记录是否缺失，若缺失，判断初始球权归属
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
                        elif ('PVL' in record[0] and record[0]['PVL'] == 'jump ball') or  ('TVL' in record[0] and record[0]['TVL'] == 'jump ball'):  # 跳球违例，修正球权记录
                            if 'JB' in record[1] and record[1]:
                                record[1]['BP'] = record[0]['BP']
                                qtr_bp = record[0]['BP']
                            else:
                                record.insert(1, {'Q': 0, 'T': '0:00.0', 'JB': ['', '', ''], 'BP': record[0]['BP']})
                                qtr_bp = record[0]['BP']
                    record.append({'Q': qtr, 'T': '12:00.0' if qtr == 1 else '24:00.0', 'BP': 0 if qtr_bp else 1})
                    # print(qtr_bp, record[-1], record[0])
                else:
                    # if qtr_bp == -1:
                    #     print('跳球记录存疑，', self.gm)
                    #     print(record)
                    record.append({'Q': qtr, 'T': '36:00.0', 'BP': qtr_bp})
                qtr_ += 1
            elif qtr > 3:
                # 加时初始球权
                record.append({'Q': qtr, 'T': '%d:00.0' % (48 + 5 * (qtr - 4)), 'BP': -1})
            for ply in self.yieldPlay(qtr):
                play = Play(ply, qtr)
                # ==========开始对一条记录进行处理==========
                if len(play.play) == 2 and 'Jump' in play.play[1]:  # 跳球记录    [客场队员、主场队员]、得球方
                    # print(play.play)
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
                            # print('跳球存疑')
                            bpsn = -1
                            record[-1]['BP'] = -1
                            # print(record)
                    if (self.gm == '201611120NOP' and play.now() == '12:44.0') or (self.gm == '201803010SAC' and play.now() == '48:00.0'):    # 201611120NOP  12:44.0
                        record[-1]['BP'] = 1
                    if (self.gm == '200612150LAL' and play.now() == '48:00.0') or (self.gm == '201412130PHI' and play.now() == '22:45.0'):
                        record[-1]['BP'] = 0
                    if (self.gm == '199712270NYK' and play.now() == '0:00.0') or (self.gm == '201101210GSW' and play.now() == '0:00.0'):
                        record[-1]['BP'] = 0
                        qtr_bp = 0
                    if (self.gm == '201312100IND' and play.now() == '46:50.0'):
                        record[-1]['BP'] = 1
                    if qtr == 0 and (len(record) == 1 or record[-1]['T'] == '0:00.0') and self.gm not in ['199712270NYK', '201101210GSW']:  # 201412170TOR
                        qtr_bp = bpsn
                    elif qtr == 0 and len(record) == 2 and \
                            ('TVL' in record[0] and record[0]['TVL'] == 'delay of game') or \
                            ('PVL' in record[0] and record[0]['PVL'] == 'delay of game'):
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
                    # 有得分或投丢
                    if s:
                        dd, mm = play.scoreType()
                        if 'makes' in rec:  # 投进    [得分球员、得分、球员所属球队]、球权转换
                            record.append({'Q': qtr, 'T': play.now(), 'MK': [rec.split(' ')[0], s, 0 if rec.split(' ')[0] in plyrs[0] else 1], 'D': dd, 'M': mm, 'BP': 0 if ind == 5 else 1})
                            if 'assist' in rec:  # 助攻    助攻球员
                                record[-1]['AST'] = rec.split(' ')[-1][:-1]
                            if s == 1:
                                if '1 of 2' in rec or '1 of 3' in rec or '2 of 3' in rec:
                                    record[-1]['BP'] = 0 if record[-1]['MK'][0] in plyrs[0] else 1
                                    # 修正某些clear path统计错犯规球员的情况    201912040CHI  29:46.0
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
                                    # record[-1]['BP'] = 0 if record[-1]['MK'][0] in plyrs[0] else 1
                                    record[-1]['BP'] = record[-2]['BP']
                                    if self.gm == '200204160ATL':
                                        record[-1]['BP'] = 1
                                    if self.gm == '200001220PHO' and play.now() == '40:36.0' and record[-2]['MK'][0] == 'ferryda01':
                                        record.append({'Q': qtr, 'T': play.now(), 'DRB': 'Team', 'BP': 1})
                                        record[-2], record[-1] = record[-1], record[-2]
                                        record[-1]['BP'] = 1
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        if ('MS' in record[x - 1] and record[x - 1]['MS'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('MK' in record[x - 1] and record[x - 1]['MK'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('ORB' in record[x - 1] and record[x - 1]['ORB'] not in plyrs[record[-1]['BP']]) or \
                                                ('TOV' in record[x - 1]) or \
                                                ('DRB' in record[x - 1] and record[x - 1]['BP'] != record[-1]['BP']):
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
                                                # print(self.gm, record[x - 2])
                                                if 'MK' in record[x - 2] and record[x - 2]['MK'][0] not in plyrs[record[-1]['BP']] and record[x - 2]['MK'][1] > 1:
                                                    flag = 0
                                                elif 'ORB' in record[x - 3] and record[x - 3]['BP'] != record[-1]['BP']:
                                                    # print(self.gm)
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
                            if (self.gm == '201411070DEN' and play.now() == '11:56.0') or (self.gm == '201503120WAS' and play.now() == '35:37.0') or \
                                    (self.gm == '' and play.now() == '15:02.0'):
                                record[-1]['BP'] = 0    # 未记录恶意犯规导致球权判断错误
                        else:  # 投失    [出手球员、得分、球员所属球队]，球权暂时仍为进攻方所有
                            if rec.split(' ')[0] == 'misses':
                                continue
                            record.append({'Q': qtr, 'T': play.now(),
                                           'MS': [rec.split(' ')[0], s, 0 if rec.split(' ')[0] in plyrs[0] else 1],
                                           'D': dd, 'M': mm, 'BP': 0 if ind == 1 else 1})
                            if len(record) == 2 and 'JB' in record[0] and record[0]['BP'] != record[1]['BP']:  # 201910280SAS
                                record[0]['BP'] = record[1]['BP']
                                qtr_bp = record[0]['BP']
                            if 'block by' in rec:  # 盖帽    盖帽球员
                                record[-1]['BLK'] = rec.split(' ')[-1][:-1]
                            if len(record) > 1 and len(record[-2]) == 4 and record[-2]['T'] == '48:00.0':    # 加时开场跳球记录缺失
                                record[-2]['BP'] = record[-1]['BP']
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
                                    # record[-1]['BP'] = 0 if record[-1]['MS'][0] in plyrs[0] else 1
                                    record[-1]['BP'] = record[-2]['BP']
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        if ('MS' in record[x - 1] and record[x - 1]['MS'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('MK' in record[x - 1] and record[x - 1]['MK'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('ORB' in record[x - 1] and record[x - 1]['ORB'] not in plyrs[record[-1]['BP']]) or \
                                                ('TOV' in record[x - 1]) or \
                                                ('DRB' in record[x - 1] and record[x - 1]['BP'] != record[-1]['BP']):
                                            break
                                        else:
                                            record[x - 1]['BP'] = record[-1]['BP']
                                            x -= 1
                                elif '1 of 1' in rec:  # 追加罚球，期间球权暂不转换
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        if ('TF' in record[x - 1] and record[x - 1]['TF'] == 'Technical') or \
                                                ('MS' in record[x - 1] and record[x - 1]['MS'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('MK' in record[x - 1] and record[x - 1]['MK'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('DRB' in record[x - 1] and record[x - 1]['BP'] != record[-1]['BP']) or \
                                                ('TOV' in record[x - 1]):
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
                                # print(record)
                                if len(record[-2]) > 3 or record[-2]['T'] not in ['48:00.0', '53:00.0', '58:00.0', '63:00.0']:
                                    record.insert(-1, {'Q': record[-2]['Q'], 'T': record[-2]['T'], 'DRB': 'Team', 'BP': record[-1]['BP']})
                                else:
                                    record[-2]['BP'] = record[-1]['BP']
                    # 前场篮板    前板球员、球权
                    elif 'Offensive rebound' in rec:
                        if rec[-7:] != 'by Team':    # 球员篮板
                            record.append({'Q': qtr, 'T': play.now(), 'ORB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                            if play.now() == record[-2]['T'] and 'MK' in record[-2] and record[-2]['MK'][0] == rec.split(' ')[-1]:    # 纠正同一个人进球先于进攻篮板记录的问题
                                record[-1], record[-2] = record[-2], record[-1]
                        else:    # Offensive rebound by Team
                            record.append({'Q': qtr, 'T': play.now(), 'ORB': 'Team', 'BP': 0 if ind == 1 else 1})
                            if record[-1]['T'] == record[-2]['T'] and 'JB' in record[-2]:    # 纠正跳球出界后跳球记录中仍记有得球人的错误    201910240DET  44:48.0
                                record[-2]['BP'] = record[-1]['BP']
                    # 后场篮板    后板球员、球权
                    elif 'Defensive rebound' in rec:
                        if rec[-7:] != 'by Team':
                            record.append({'Q': qtr, 'T': play.now(), 'DRB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                        else:
                            record.append({'Q': qtr, 'T': play.now(), 'DRB': 'Team', 'BP': 0 if ind == 1 else 1})
                    # 换人    [上场球员、下场球员、换人球队]    球权不转换
                    elif 'enters' in rec:
                        tmp = rec.split(' ')
                        if tmp[0] == tmp[-1]:    # 自己换自己可还行
                            print('error', self.gm, play.play)
                        if (tmp[0] not in plyrs[0] and tmp[0] not in plyrs[1]) or (tmp[-1] not in plyrs[0] and tmp[-1] not in plyrs[1]):
                            continue
                        record.append({'Q': qtr, 'T': play.now(), 'SWT': [tmp[0], tmp[-1], 0 if tmp[0] in plyrs[0] else 1]})
                        if len(record) > 1 and 'BP' in record[-2]:
                            record[-1]['BP'] = record[-2]['BP']
                        if len(record) > 1 and record[-1]['T'] == record[-2]['T'] and 'DRB' in record[-2] and record[-2]['DRB'] == record[-1]['SWT'][0]:
                            record[-1], record[-2] = record[-2], record[-1]
                    # 暂停
                    elif 'timeout' in rec:
                        tmp = rec.split(' ')
                        if tmp[0] == 'Official':  # 官方暂停
                            record.append({'Q': qtr, 'T': play.now(), 'OTO': ''})
                        elif '20' in tmp:  # 短暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'STO': 0 if ind == 1 else 1})
                        elif 'full' in tmp:  # 长暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'FTO': 0 if ind == 1 else 1})
                        elif tmp[0] == 'Turnover':  # excessive timeout turnover    失误球队
                            record.append({'Q': qtr, 'T': play.now(), 'ETT': 0 if ind == 1 else 1})
                        elif tmp[0] == 'Excess':  # Excess timeout    犯规球队（记录在对方球队位置）
                            record.append({'Q': qtr, 'T': play.now(), 'ETO': 0 if ind == 5 else 1})
                        else:
                            if 'no' not in rec:
                                print(rec, self.gm)
                        if ' no' not in rec:
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                    # 犯规
                    elif 'foul' in rec and 'offensive' not in rec:  # 犯规（小写的进攻犯规实为失误统计）
                        # print(rec)
                        tmp = rec.split(' ')
                        ix = tmp.index('by') if 'by' in tmp else -1
                        if 'Turnover' == tmp[0]:
                            plyr = tmp[2]
                            if not plyr:
                                continue
                            record.append({'Q': qtr, 'T': play.now(), 'TOV': 'foul', 'plyr': plyr, 'BP': 0 if ind == 5 else 1})
                            if self.gm == '200102270MIA' and play.now() == '2:02.0':
                                record.pop()
                                continue
                        if 'Technical' in rec:  # 技术犯规（不记入个人犯规）    技犯类型、技犯球员、球权和之前保持一致
                            record.append({'Q': qtr, 'T': play.now(), 'TF': 'Technical', 'plyr': tmp[-1]})
                            if record[-1]['plyr'] == 'by':
                                record[-1]['plyr'] = ''
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            continue
                        elif ('tech foul' in rec or 'Taunting technical' in rec) and 'Def 3 sec' not in rec:  # 技术犯规（不记入个人犯规）    技犯类型、技犯球员、球权和之前保持一致
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
                                if self.gm == '201502060ORL' and record[-1]['D3S'] == 'ellinwa01' and play.now() == '25:40.0':
                                    record[-1]['BP'] = 0
                            continue
                        elif 'Clear path' in rec:  # clear path（计入个人犯规和球队犯规）    犯规球员
                            record.append({'Q': qtr, 'T': play.now(), 'PF': 'Clear path foul', 'plyr': tmp[ix + 1]})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            if self.gm in ['201811140TOR', '201811170BOS', '201812260ORL',
                                      '201901020WAS', '201901160DAL', '201901230NOP',
                                      '201901300MIN', '202002090ATL', '201912290NOP']:
                                record[-1]['BP'] = 0 if record[-1]['BP'] else 1
                            continue
                        elif 'Teamfoul' in rec:  # 2000赛季后无此项
                            # if play.now() == record[-1]['T']:
                            if rec[-4:] != 'Team':
                                record.append({'Q': qtr, 'T': play.now(), 'TOV': 'Offensive foul', 'plyr': tmp[ix + 1],
                                               'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else '', 'BP': 1 if tmp[ix + 1] in plyrs[0] else 0})
                            else:
                                record.append({'Q': qtr, 'T': play.now(), 'TF': 'Teamfoul', 'plyr': 'Team', 'BP': record[-1]['BP']})
                                # record.append({'Q': qtr, 'T': play.now(), 'PF': 'Teamfoul', 'plyr': '', 'BP': record[-1]['BP']})
                            if len(record) > 2 and 'PF' in record[-3] and 'TOV' in record[-2] and record[-3]['plyr'] == record[-2]['plyr'] and record[-3]['plyr'] == record[-1]['plyr']:
                                record.pop()
                            if len(record) > 1 and 'FF1' in record[-2] and record[-1]['plyr'] == record[-2]['plyr']:
                                record.pop()
                            if len(record) > 1 and 'FF2' in record[-2] and record[-1]['plyr'] == record[-2]['plyr']:
                                record.pop()
                            # if (self.gm == '199801180POR' and record[-1]['T'] == '26:47.0') or (self.gm == '199903180SAC' and record[-1]['T'] == '16:02.0'):
                            #     record.pop()
                            continue
                        elif 'Double technical foul' in rec:  # 双方技犯    [双方球员]
                            record.append({'Q': qtr, 'T': play.now(), 'DTF': [tmp[-3], tmp[-1]]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            continue
                        # assert 'drawn by' in rec
                        if 'Flagrant foul type 1' in rec:  # 一级恶意犯规（计入个人犯规和球队犯规）    犯规种类、犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF1': int(tmp[3]), 'plyr': tmp[ix + 1], 'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            if 'MK' in record[-2] and record[-2]['MK'][0] in plyrs[record[-1]['BP']]:    # 200102200CHI  30:37.0
                                record[-2]['BP'] = record[-1]['BP']
                            continue
                        if 'Flagrant foul type 2' in rec:  # 二级恶意犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF2': int(tmp[3]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            if 'MK' in record[-2] and record[-2]['MK'][0] in plyrs[record[-1]['BP']]:    # 201903060DET  37:53.0
                                record[-2]['BP'] = record[-1]['BP']
                            if 'FF2' in record[-2] and record[-2]['drawn'] == record[-1]['plyr'] and record[-1]['drawn'] == record[-2]['plyr']:    # 双方恶意犯规    201103300WAS  15:12.0
                                # print('打架啦')
                                record[-1]['BP'] = record[-3]['BP']
                                record[-2]['BP'] = record[-3]['BP']
                                # print(record[-3:])
                            continue
                        if 'Double personal foul' in rec:  # 双方犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'PF': ' '.join(tmp[:ix]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            record.append({'Q': qtr, 'T': play.now(), 'PF': ' '.join(tmp[:ix]), 'plyr': tmp[ix + 3],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            if ' '.join(tmp[:ix]) not in foultype:
                                foultype.append(' '.join(tmp[:ix]))
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
                            if ' '.join(tmp[:ix]) not in foultype:
                                foultype.append(' '.join(tmp[:ix]))
                            if (self.gm == '201512170LAL' and play.now() == '23:30.0' and record[-1]['plyr'] == 'howardw01') or \
                                    (self.gm == '201503220OKC' and play.now() == '21:44.0' and record[-1]['plyr'] == 'whiteha01') or \
                                    (self.gm == '201412150PHO' and play.now() == '25:08.0' and record[-1]['plyr'] == 'parkeja01') or \
                                    (self.gm == '201401150PHO' and play.now() == '16:27.0' and record[-1]['plyr'] == 'youngni01'):
                                record[-1]['BP'] = 0
                            if len(record) > 1 and 'PF' in record[-2] and record[-2]['PF'] == 'Personal foul' and \
                                    (record[-2]['drawn'] == record[-1]['plyr'] or record[-1]['drawn'] == record[-2]['plyr']) and self.gm != '201301140CHI':    # 双方犯规    201701110OKC  6:34.0
                                record[-2]['BP'] = record[-3]['BP']
                                record[-1]['BP'] = record[-3]['BP']
                    # 失误
                    elif 'Turnover' in rec:  # 失误    失误种类、失误球员、转换球权
                        tmp = rec.split(' ')
                        tp = rec[rec.index('(') + 1:rec.index(';')] if ';' in rec else rec[rec.index('(') + 1:-1]
                        plyr = 'Team' if 'by Team' in rec else tmp[2]
                        if not plyr and tp != '5 sec' and tp != '8 sec':
                            continue
                        record.append({'Q': qtr, 'T': play.now(), 'TOV': tp, 'plyr': plyr, 'BP': 0 if ind == 5 else 1})
                        if 'steal by' in rec:  # 抢断    抢断球员
                            record[-1]['STL'] = tmp[-1][:-1]
                        if len(record) > 1 and record[-1]['BP'] == record[-2]['BP'] and record[-1]['T'] != record[-2]['T'] and 'TVL' in record[-2] and record[-2]['TVL'] == 'jump ball' and self.gm > '2016':
                            record[-2]['BP'] = 0 if record[-2]['BP'] else 1
                            continue
                        if len(record) > 1 and record[-1]['BP'] == record[-2]['BP'] and record[-1]['T'] != record[-2]['T'] and not \
                                ('PF' in record[-2] and record[-2]['PF'] in ['Offensive foul', 'Offensive charge foul'] and record[-2]['plyr'] == record[-1]['plyr']) and \
                                len(record[-2]) != 3:
                            if qtr == 4 and record[-2]['Q'] == 3:
                                record.append({'Q': qtr, 'T': '48:00.0', 'BP': 0 if record[-1]['BP'] else 1})
                            else:
                                # if self.gm > '201004040IND':
                                #     print(self.gm, record[-1])
                                #     edit_gm(record[-1]['Q'], MPTime(record[-1]['T']), self.gm, record[-1])
                                record.append({'Q': qtr, 'T': play.now(), 'DRB': 'Team', 'BP': 0 if record[-2]['BP'] else 1})
                            record[-1], record[-2] = record[-2], record[-1]
                        if self.gm == '199611090DAL' and play.now() == '37:05.0' and record[-1]['TOV'] == 'lost ball':
                            record.append({'Q': qtr, 'T': play.now(), 'DRB': 'Team', 'BP': 0})
                            record[-1], record[-2] = record[-2], record[-1]
                        if len(record) > 1 and 'FF1' in record[-2] and record[-1]['plyr'] == record[-2]['plyr']:
                            pass
                        if len(record) > 1 and 'PF' in record[-2] and record[-1]['plyr'] == record[-2]['plyr'] and record[-1]['TOV'] == 'turnover':
                            record.pop()
                            continue
                        # if (self.gm == '201710180MEM' and play.now() == '26:05.0') or (self.gm == '201710200PHO' and play.now() == '36:39.0'):
                        #     record.pop()
                        #     continue
                        if (self.gm == '201710200BRK' and play.now() == '24:57.0') or (self.gm == '201710240POR' and play.now() == '3:40.0') and 'TOV' in record[-2]:
                            record.pop()
                        if tp not in totype:
                            totype.append(tp)
                    # 违例
                    elif 'Violation by' in rec:
                        if 'Team' in rec:  # 球队违例    违例种类、违例球队、转换球权
                            if 'jump ball' in rec:  # 跳球违例，明确初始球权
                                if not record:
                                    qtr_bp = 0 if ind == 5 else 1
                            record.append({'Q': qtr, 'T': play.now(), 'TVL': rec[rec.index('(') + 1:-1],
                                           'tm': 0 if ind == 1 else 1, 'BP': 0 if ind == 5 else 1})
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
                            elif self.gm == '201702140LAL':    # 46:56.0
                                record.pop()
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
                        if rec[rec.index('(') + 1:-1] not in vltype:
                            vltype.append(rec[rec.index('(') + 1:-1])
                    # 回放
                    elif 'Instant' in rec:  # 若录像回放之后改判会是什么情况
                        if 'Challenge' in rec:  # 教练挑战    挑战球队0客1主
                            record.append({'Q': qtr, 'T': play.now(), 'CCH': 0 if ind == 1 else 1})
                        else:  # 录像回放    0客1主
                            record.append({'Q': qtr, 'T': play.now(), 'IRP': 0 if ind == 1 else 1})
                        if len(record) > 1 and 'BP' in record[-2]:
                            record[-1]['BP'] = record[-2]['BP']
                    # 驱逐
                    elif 'ejected' in rec:  # 驱逐出场    被驱逐球员
                        if rec.split(' ')[0]:
                            record.append({'Q': qtr, 'T': play.now(), 'EJT': rec.split(' ')[0]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                    # 防守三秒（违例）
                    elif 'Defensive three seconds' in rec:  # 防守三秒    违例球员
                        record.append({'Q': qtr, 'T': play.now(), 'D3S': rec.split(' ')[-1]})
                        record[-1]['BP'] = 1 if record[-1]['D3S'] in plyrs[0] else 0
                    # 例外情况（应无）
                    else:
                        if rec:
                            print(play.play, self.gm)
        # 梳理球队得分、加时初始球权确定
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
        return sorted(vltype), sorted(totype), sorted(foultype), record

    @staticmethod
    def plyrstats(pn, item, plyr_stats):
        # 球员个人数据梳理
        if pn and item:
            if pn not in plyr_stats:
                # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT%
                # 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS
                plyr_stats[pn] = np.zeros((1, 18))
            for it in item:
                plyr_stats[pn][0, it] += 1
        return plyr_stats

    def find_time_series(self, record):
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
                                     'PVL' not in tmp[ix] and 'FF1' not in tmp[ix]):
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

    def pace(self, record):  # 回合数统计
        star_of_game = 0
        # 排除赛前的比赛延误警告和跳球违例
        for i in record:
            if ('TVL' in i and (i['TVL'] == 'delay of game' or i['TVL'] == 'jump ball')) or ('PVL' in i and (i['PVL'] == 'delay of game' or i['PVL'] == 'jump ball')):
                star_of_game += 1
            else:
                if len(i) != 4 and 'JB' not in i:  # 199612280SAC
                    print('pace', self.gm, i)
                break
        exchange, bp = 0.5, record[star_of_game]['BP']
        rht = [0, 1] if record[star_of_game]['BP'] else [1, 0]
        # print(record[0])
        for i in record[star_of_game:]:
            # print(i, bp)
            if i['BP'] != bp or (len(i) == 4 and (i['T'] == '12:00.0' or i['T'] == '24:00.0' or i['T'] == '36:00.0')) or \
                    ((i['T'] == '48:00.0' or i['T'] == '53:00.0' or i['T'] == '58:00.0' or i['T'] == '63:00.0') and 'JB' in i):  # 球权交换或节初或加时赛初跳球:
                try:
                    if self.gm not in ['199611010NJN', '199611010ORL', '199611010VAN', '201910230PHO', '201910240DET'] and \
                            not ((i['Q'] == 0 and i['T'] == '12:00.0') or (i['Q'] == 1 and i['T'] == '24:00.0') or
                                 (i['Q'] == 2 and i['T'] == '36:00.0') or (i['Q'] == 3 and i['T'] == '48:00.0') or
                                 (i['Q'] == 4 and i['T'] == '53:00.0') or (i['Q'] == 5 and i['T'] == '58:00.0') or
                                 (i['Q'] == 6 and i['T'] == '63:00.0') or (i['Q'] == 7 and i['T'] == '68:00.0')):
                        assert 'MS' not in i
                except:
                    print('MS转换球权', self.gm, i, bp)
                    edit_gm(i['Q'], MPTime(i['T']), self.gm, i)
                if not ((i['Q'] == 0 and i['T'] == '12:00.0') or (i['Q'] == 1 and i['T'] == '24:00.0') or (i['Q'] == 2 and i['T'] == '36:00.0') or (i['Q'] == 3 and i['T'] == '48:00.0') or
                        (i['Q'] == 4 and i['T'] == '53:00.0') or (i['Q'] == 5 and i['T'] == '58:00.0') or (i['Q'] == 6 and i['T'] == '63:00.0') or (i['Q'] == 7 and i['T'] == '68:00.0')):  # 排除节末
                    exchange += 0.5
                    bp = i['BP']
                    rht[bp] += 1
        return exchange, rht

    def boxscores(self, record):
        # 0FG 1FGA 2FG% 33P 43PA 53P% 6FT 7FTA 8FT% 9ORB 10DRB 11TRB 12AST 13STL 14BLK 15TOV 16PF 17PTS 18PACE
        stats = np.zeros((2, 7, 19))
        plyrs = self.teamplyrs()
        for i in record:
            # 数据统计
            if 'MK' in i:
                stats[0 if i['MK'][0] in plyrs[0] else 1][6][17] += i['MK'][1]
                if i['MK'][1] == 1:
                    stats[0 if i['MK'][0] in plyrs[0] else 1][6][6] += 1
                    stats[0 if i['MK'][0] in plyrs[0] else 1][6][7] += 1
                else:
                    stats[0 if i['MK'][0] in plyrs[0] else 1][6][0] += 1
                    stats[0 if i['MK'][0] in plyrs[0] else 1][6][1] += 1
                    if i['MK'][1] == 3:
                        stats[0 if i['MK'][0] in plyrs[0] else 1][6][3] += 1
                        stats[0 if i['MK'][0] in plyrs[0] else 1][6][4] += 1
                    if 'AST' in i:
                        stats[0 if i['AST'] in plyrs[0] else 1][6][12] += 1
            elif 'MS' in i:
                if i['MS'][1] == 1:
                    stats[0 if i['MS'][0] in plyrs[0] else 1][6][7] += 1
                else:
                    stats[0 if i['MS'][0] in plyrs[0] else 1][6][1] += 1
                    if i['MS'][1] == 3:
                        stats[0 if i['MS'][0] in plyrs[0] else 1][6][4] += 1
                if 'BLK' in i:
                    stats[0 if i['BLK'] in plyrs[0] else 1][6][14] += 1
            elif 'ORB' in i and i['ORB'] != 'Team':
                stats[0 if i['ORB'] in plyrs[0] else 1][6][9] += 1
                stats[0 if i['ORB'] in plyrs[0] else 1][6][11] += 1
            elif 'DRB' in i and i['DRB'] != 'Team':
                stats[0 if i['DRB'] in plyrs[0] else 1][6][10] += 1
                stats[0 if i['DRB'] in plyrs[0] else 1][6][11] += 1
            elif 'TOV' in i:
                if i['plyr'] != 'Team' and i['plyr'] != '':
                    stats[0 if i['plyr'] in plyrs[0] else 1][6][15] += 1
                if 'STL' in i:
                    stats[0 if i['STL'] in plyrs[0] else 1][6][13] += 1
            elif ('PF' in i and i['PF'] != 'Teamfoul') or 'FF1' in i or 'FF2' in i:
                if i['plyr'] and i['plyr'] != 'Team':
                    stats[0 if i['plyr'] in plyrs[0] else 1][6][16] += 1
        _, rht = self.pace(record)
        stats[0][6][18] += rht[0]
        stats[1][6][18] += rht[1]
        return stats

    def game_analyser(self, record):  # 球队、球员单场比赛技术统计，并与实际对比
        plyrs = self.teamplyrs()
        ttl = [self.bxscr[1][0][-1], self.bxscr[1][1][-1]]
        plyr_stats = {}
        ss = [0, 0]
        # print(record[0])
        sts = np.zeros((2, 8))  # 0罚进1罚球出手2两分进3两分出手4三分进5三分出手6运动进7运动出手
        odta = np.zeros((2, 4))  # 0前板1后板2篮板3助攻
        sbtp = np.zeros((2, 4))  # 0抢断1盖帽2失误3犯规
        for i in record:
            # 数据统计
            if 'MK' in i:
                ss[0 if i['MK'][0] in plyrs[0] else 1] += i['MK'][1]
                if i['MK'][1] == 1:
                    sts[0 if i['MK'][0] in plyrs[0] else 1][0] += 1
                    sts[0 if i['MK'][0] in plyrs[0] else 1][1] += 1
                    plyr_stats = self.plyrstats(self.pm2pn[i['MK'][0]], [6, 7], plyr_stats)
                else:
                    sts[0 if i['MK'][0] in plyrs[0] else 1][6] += 1
                    sts[0 if i['MK'][0] in plyrs[0] else 1][7] += 1
                    if i['MK'][1] == 2:
                        sts[0 if i['MK'][0] in plyrs[0] else 1][2] += 1
                        sts[0 if i['MK'][0] in plyrs[0] else 1][3] += 1
                        plyr_stats = self.plyrstats(self.pm2pn[i['MK'][0]], [0, 1], plyr_stats)
                    else:
                        sts[0 if i['MK'][0] in plyrs[0] else 1][4] += 1
                        sts[0 if i['MK'][0] in plyrs[0] else 1][5] += 1
                        plyr_stats = self.plyrstats(self.pm2pn[i['MK'][0]], [0, 1, 3, 4], plyr_stats)
                    if 'AST' in i:
                        odta[0 if i['AST'] in plyrs[0] else 1][3] += 1
                        plyr_stats = self.plyrstats(self.pm2pn[i['AST']], [12], plyr_stats)
            elif 'MS' in i:
                if i['MS'][1] == 1:
                    sts[0 if i['MS'][0] in plyrs[0] else 1][1] += 1
                    plyr_stats = self.plyrstats(self.pm2pn[i['MS'][0]], [7], plyr_stats)
                elif i['MS'][1] == 2:
                    sts[0 if i['MS'][0] in plyrs[0] else 1][7] += 1
                    sts[0 if i['MS'][0] in plyrs[0] else 1][3] += 1
                    plyr_stats = self.plyrstats(self.pm2pn[i['MS'][0]], [1], plyr_stats)
                else:
                    sts[0 if i['MS'][0] in plyrs[0] else 1][7] += 1
                    sts[0 if i['MS'][0] in plyrs[0] else 1][5] += 1
                    plyr_stats = self.plyrstats(self.pm2pn[i['MS'][0]], [1, 4], plyr_stats)
                if 'BLK' in i:
                    sbtp[0 if i['BLK'] in plyrs[0] else 1][1] += 1
                    plyr_stats = self.plyrstats(self.pm2pn[i['BLK']], [14], plyr_stats)
            elif 'ORB' in i and i['ORB'] != 'Team':
                odta[0 if i['ORB'] in plyrs[0] else 1][0] += 1
                odta[0 if i['ORB'] in plyrs[0] else 1][2] += 1
                plyr_stats = self.plyrstats(self.pm2pn[i['ORB']], [9, 11], plyr_stats)
            elif 'DRB' in i and i['DRB'] != 'Team':
                odta[0 if i['DRB'] in plyrs[0] else 1][1] += 1
                odta[0 if i['DRB'] in plyrs[0] else 1][2] += 1
                plyr_stats = self.plyrstats(self.pm2pn[i['DRB']], [10, 11], plyr_stats)
            elif 'TOV' in i:
                if i['plyr'] != 'Team' and i['plyr'] != '':
                    sbtp[0 if i['plyr'] in plyrs[0] else 1][2] += 1
                    plyr_stats = self.plyrstats(self.pm2pn[i['plyr'].rstrip(')')], [15], plyr_stats)
                # elif i['plyr'] == 'Team' and i['TOV'] == 'shot clock':
                #     sbtp[0 if i['BP'] else 1][2] += 1
                if 'STL' in i:
                    sbtp[0 if i['STL'] in plyrs[0] else 1][0] += 1
                    plyr_stats = self.plyrstats(self.pm2pn[i['STL']], [13], plyr_stats)
            elif ('PF' in i and i['PF'] != 'Teamfoul') or 'FF1' in i or 'FF2' in i:
                if i['plyr'] and i['plyr'] != 'Team':
                    sbtp[0 if i['plyr'] in plyrs[0] else 1][3] += 1
                    plyr_stats = self.plyrstats(self.pm2pn[i['plyr']], [16], plyr_stats)
                    # if i['plyr'] == 'russebr01':
                    #     print(i)
        # 判断总得分
        if ss != [x[0] for x in self.bxscr[0].values()]:
            sum_score_error.append(self.gm)
        # 判断投篮分项数据
        for i in range(2):
            if sts[i][0] != int(ttl[i][8]) or sts[i][1] != int(ttl[i][9]) or \
                    sts[i][4] != int(ttl[i][5]) or sts[i][5] != int(ttl[i][6]) or \
                    sts[i][6] != int(ttl[i][2]) or sts[i][7] != int(ttl[i][3]):
                shootings_error.append(self.gm)
                break
        # 判断篮板助攻
        for i in range(2):
            if odta[i][0] != int(ttl[i][11]) or odta[i][1] != int(ttl[i][12]) or \
                    odta[i][2] != int(ttl[i][13]) or odta[i][3] != int(ttl[i][14]):
                odta_error.append(self.gm)
                break
        # 判断sbtp
        for i in range(2):
            if sbtp[i][0] != int(ttl[i][15]) or sbtp[i][1] != int(ttl[i][16]) or \
                    sbtp[i][2] != int(ttl[i][17]) or sbtp[i][3] != int(ttl[i][18]):
                sbtp_error.append(self.gm)
                break

    def start_of_quarter(self, record):
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
                    if i['BP'] == sbp:
                        print('节首球权', self.gm, q, i)
                        edit_gm(q, MPTime('%d:00.0' % (q * 12)), self.gm, i)
                elif q == 3:
                    if i['BP'] != sbp:
                        print('节首球权', self.gm, q, i)
                        edit_gm(q, MPTime('36:00.0'), self.gm, i)
                else:
                    ot = q - 3
                q += 1
            if ot:
                if 'JB' not in i and i['BP'] == -1:
                    print('节首球权', self.gm, q - 1, i)
                    edit_gm(q - 1, MPTime('%d:00.0' % (48 + 5 * (q - 5))), self.gm, i)
                ot = 0

    def rotation(self, record):
        PoN = 0
        rot = []
        plyrs = self.teamplyrs()
        starters = [x[:5] for x in plyrs]
        rot.append({'T': '0:00.0', 'Q': 0, 'R': copy.deepcopy(starters), 'TN': '', 'S': [0, 0]})
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
                    rot.append({'T': i['T'], 'Q': i['Q'], 'R': copy.deepcopy(starters), 'TN': ''})
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
                rot.append({'T': i['T'], 'Q': i['Q'], 'R': copy.deepcopy(starters), 'TN': ''})
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
                rot.append({'T': i['T'], 'Q': i['Q'], 'R': copy.deepcopy(starters), 'TN': ''})
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
            if rot[i]['T'] != rot[i - 1]['T']:
                rot_.append(rot[i - 1])
        rot_.append(rot[-1])
        return rot_


class GameBoxScore(object):
    def __init__(self, gm, ROP):
        self.gamemark = gm
        self.boxes = LoadPickle(gameMarkToDir(gm, ROP, shot=True))
        self.quarters = len(self.boxes) - 5 if len(self.boxes) > 3 else 0


if __name__ == '__main__':
    regularOrPlayoffs = ['regular', 'playoffs']
    ft, to, vl = [], [], []
    count_games = 0
    for season in range(2000, 2020):
        ss = '%d_%d' % (season, season + 1)
        # print(ss)
        for i in range(2):
            season_dir = 'D:/sunyiwu/stat/data/seasons_scanned/%s/' % ss
            if not os.path.exists(season_dir):
                os.mkdir(season_dir)
            season_dir = 'D:/sunyiwu/stat/data/seasons_scanned/%s/%s/' % (ss, regularOrPlayoffs[i])
            if not os.path.exists(season_dir):
                os.mkdir(season_dir)
            gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
            for gm in tqdm(gms):
                gmdir = gameMarkToDir(gm[:-7], regularOrPlayoffs[i])
                ctm = os.path.getmtime(gmdir)
                if 1:
                    count_games += 1
                    # print('\t\t\t' + gm)
                    game = Game(gm[:-7], regularOrPlayoffs[i])
                    vltmp, totmp, fttmp, record = game.game_scanner()
                    # 保存文件
                    if 1:
                        writeToPickle(season_dir + gm[:-7] + '_scanned.pickle', record)
                    # game.find_time_series(record)
                    # game.start_of_quarter(record)
                    # _, _ = game.pace(record)
                    # game.game_analyser(record)
                    # try:
                    rot = game.rotation(record)
                    ct = 0
                    for r in rot:
                        if len(r['R'][0]) != 5 or len(r['R'][1]) != 5:
                            ct += 1
                    if ct != 0:
                        # print(gm)
                        rot_error += 1
                    # except:
                    #     print('error')
                    # for ix, r in enumerate(record):
                    #     if 'BP' not in r and 'EJT' not in r:
                    #         print(r, gm[:-7])

    #                 ft = list(set(ft + fttmp))
    #                 to = list(set(to + totmp))
    #                 vl = list(set(vl + vltmp))
    # print(len(sum_score_error))
    # print(len(shootings_error))
    # print(len(sbtp_error))
    # print(len(odta_error))
    # print(count_games)
    # print(ft)
    # print(to)
    # print(vl)
    print(rot_error)
    # 2000-2020
    # 11
    # 501
    # 1329
    # 592
    # 25674

    # 1996-2020
    # 21
    # 573
    # 2335
    # 860
    # 30250


