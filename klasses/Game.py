import sys

sys.path.append('../')
from util import minusMinutes, gameMarkToDir, LoadPickle
from klasses.miscellaneous import MPTime
from windows.tools import GameDetailWindow
import os
from tqdm import tqdm
import numpy as np

sum_score_error = []
shootings_error = []
odta_error = []
sbtp_error = []


class Play(object):
    # 构造参数：本条play的list，本节序号，主要关注球员唯一识别号，球员主客场
    def __init__(self, lst, ind, pm=None, HOA=None, HomeOrAts=[[4, 5], [2, 1]]):
        self.play = lst  # 0:时间, 1:客队描述, 2:客队加分, 3:比分, 4:主队加分, 5:主队描述
        self.quarter = ind
        self.HOA = HOA
        self.pm = pm
        self.HomeOrAt = HomeOrAts[HOA - 1] if HOA != None else None
        oppoHOA = None if HOA == None else 0 if HOA else 1
        self.oppoHomeOrAt = HomeOrAts[oppoHOA - 1] if oppoHOA != None else None
        self.playDisc = self.play[self.HomeOrAt[1]] \
            if len(self.play) == 6 and self.HomeOrAt != None else None
        self.oppoPlayDisc = self.play[self.oppoHomeOrAt[1]] \
            if len(self.play) == 6 and self.oppoHomeOrAt != None else None

    # 无偏方法（无主客队之分）
    def time(self):  # 当前时间（本节倒计时）
        return MPTime(self.play[0])

    def now(self):  # 比赛经过时间（字符串形式：'%d:%02d.%d'）
        if self.quarter <= 3:  # 常规时间
            return minusMinutes('%d:00.0' % ((self.quarter + 1) * 12), self.play[0])
        else:  # 加时赛
            return minusMinutes('%d:00.0' % (48 + (self.quarter - 3) * 5), self.play[0])

    def nowtime(self):  # 精确至0.1秒的比赛经过时间（数字，单位秒）
        t = self.now()
        minute, second, miniSec = [int(x) for x in [t[:-5], t[-4:-2], t[-1]]]
        now = 60 * minute + second + 0.1 * miniSec
        return now

    def leaderAndDiff(self):  # 返回领先球队并计算分差（计算了本条play记录的计分之后）
        scores = [int(x) for x in self.play[3].split('-')]
        diff = abs(scores[0] - scores[1])
        if scores[0] == scores[1]:
            return 'tie', diff
        else:
            if scores[0] > scores[1]:
                return 0, diff  # 0客1主
            else:
                return 1, diff  # 0客1主

    def diffbeforescore(self, score):
        scores = [int(x) for x in self.play[3].split('-')]
        if self.play[2] or self.play[4]:
            if self.play[2]:
                scores[0] -= score
            else:
                scores[1] -= score
        return abs(scores[0] - scores[1])

    def playRecord(self):
        if len(self.play) == 6:  # 是一条完整比赛记录
            return True
        return False

    def jumpball(self):
        j = self.play[1].split(' ')
        # print(j)
        if self.play[1][-3:] == 'vs.':
            if len(j) == 3:
                return '', '', ''
            else:
                return j[2], '', ''
        if '(' in j or j[-1][-1] != ')':
            return j[2], j[4], ''
        return j[2], j[4], j[5][1:]  # 客队跳球球员、主队跳球球员、得球球员

    def record(self):  # 返回本条记录主要内容
        if self.playRecord():
            return self.play[1] if self.play[1] else self.play[5], \
                   1 if self.play[1] else 5
        else:
            return '', -1

    # 有/无偏方法
    def score(self, ind=None):  # 返回得分或投失分数值
        if ind != None:
            statement = self.play[ind]
        else:
            statement = self.playDisc
        if 'free throw' in statement:
            return 1
        elif '2-pt' in statement:
            return 2
        elif '3-pt' in statement:
            return 3
        elif 'no shot' in statement:
            return 1

    # 有偏方法（有主客队之分）
    def teamPlay(self):
        if self.playDisc:  # 主队有比赛情况记录
            return True
        return False

    def oppoPlay(self):
        if self.play[self.oppoHomeOrAt[1]]:  # 对手有比赛情况记录
            return True
        return False

    def playerMadeShoot(self):  # 判断球员是否得分，前提：playRecord、teamPlay
        if self.playDisc.split(' ')[0] == self.pm and \
                self.play[self.HomeOrAt[0]]:  # 球员匹配且有得分纪录
            return True
        return False

    def playerMissShoot(self):  # 判断球员是否投失，前提：playRecord、teamPlay
        if self.playDisc.split(' ')[0] == self.pm and \
                'misses no shot' not in self.playDisc and \
                'misses' in self.playDisc:  # 球员匹配且无得分纪录
            return True
        return False

    def playerOffReb(self):  # 判断球员是否有进攻篮板，前提：playRecord、teamPlay
        if 'by %s' % self.pm in self.playDisc and 'Offensive' in self.playDisc:
            return True
        return False

    def playerDefReb(self):  # 判断球员是否有防守篮板，前提：playRecord、teamPlay
        if 'by %s' % self.pm in self.playDisc and 'Defensive' in self.playDisc:
            return True
        return False

    def playerAst(self):  # 判断球员是否助攻，前提：playRecord、teamPlay
        if self.playDisc.split(' ')[0] != self.pm and \
                'assist by' in self.playDisc and self.pm in self.playDisc:
            return True
        return False

    def playerTO(self):  # 判断球员是否助攻，前提：playRecord、teamPlay
        if 'Turnover by %s' % self.pm in self.playDisc:
            return True
        return False

    def playerStl(self):  # 判断球员是否抢断，前提：playRecord、oppoPlay
        if 'steal by %s' % self.pm in self.oppoPlayDisc:
            return True
        return False

    def playerBlk(self):  # 判断球员是否盖帽，前提：playRecord、oppoPlay
        if 'block by by %s' % self.pm in self.oppoPlayDisc:
            return True
        return False


class Shooting(object):
    def __init__(self, lst):
        self.record = lst
        self.marginX = 5
        self.marginY = 10

    def posi(self, season):  # 投篮点坐标
        cors = self.record[0].split(';')
        x = int(cors[1].split(':')[1].rstrip('px')) + self.marginX
        y = int(cors[0].split(':')[1].rstrip('px')) + self.marginY
        if season >= 2013:
            y += 20
        return x, y

    def quarter(self):  # 节次
        return int(self.record[2][1][-1])

    def nowtime(self):  # 时间
        return self.record[1].split(' ')[2]

    def score(self):  # 分数
        return 2 if '2-pointer' in self.record[1] else 3

    def distance(self):  # 距离
        return int(self.record[1].split('<br>')[-2].split(' ')[-2])

    def TTL(self):  # 领先/打平/落后
        if 'leads' in self.record[1]:
            return 'lead'
        elif 'trails' in self.record[1]:
            return 'trail'
        elif 'tied' in self.record[1]:
            return 'tie'
        return ''

    def diff(self):  # 分差（以主/客场球队视角）
        ss = self.record[1].split(' ')[-1].split('-')
        return ss[0] - ss[1]

    def pm(self):  # playermark
        return self.record[2][2].split('-')[1]

    def MM(self):
        return 1 if self.record[2][3] == 'make' else 0


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

    def yieldPlay(self, qtr):
        for p in self.gameflow[qtr]:
            yield p

    def teamplyrs(self):
        plyrs = [[], []]
        for i, tm in enumerate(self.bxscr[1]):
            for p in tm[1:-1]:
                plyrs[i].append(p[0])
        return plyrs

    def game_scanner(self, gm):
        record = []
        plyrs = self.teamplyrs()
        foultype, totype, vltype = [], [], []
        qtr_bp, qtr_ = -1, 1
        if gm == '199611010DET':
            record.append({'Q': 0, 'T': '0:00.0', 'BP': 0})
            qtr_bp = 0
        for qtr in range(self.quarters):
            if 0 < qtr < 4 and qtr == qtr_:
                if qtr == 1 or qtr == 2:
                    # 第一节结束、第二节开始前，判断跳球记录是否缺失，若缺失，判断初始球权归属
                    if qtr == 1:
                        if qtr_bp == -1:  # 跳球记录缺失
                            if 'MK' in record[0] or 'TOV' in record[0] or ('PF' in record[0] and
                                                                           record[0]['PF'] == 'Offensive foul'):
                                qtr_bp = 0 if record[0]['BP'] else 1
                            elif 'MS' in record[0] or ('PF' in record[0] and (record[0]['PF'] == 'Shooting foul' or
                                                                              record[0]['PF'] == 'Personal foul')):
                                qtr_bp = record[0]['BP']
                            elif 'TVL' in record[0] and record[0]['TVL'] == 'def goaltending':
                                qtr_bp = record[0]['BP']
                            elif 'PVL' in record[0] and (record[0]['PVL'] == 'def goaltending' or
                                                         record[0]['PVL'] == 'lane' or
                                                         record[0]['PVL'] == 'kicked ball'):
                                qtr_bp = record[0]['BP']
                            elif 'PF' in record[0] and record[0]['PF'] == 'Loose ball foul':
                                qtr_bp = record[0]['BP']
                            elif 'JB' in record[0] and record[0]['BP'] == -1:
                                if 'PVL' in record[1] and record[1]['PVL'] == 'jump ball':  # 200511160PHO    200511060LAL
                                    record[0]['BP'] = record[1]['BP']
                                    qtr_bp = record[0]['BP']
                                elif 'TOV' in record[1] and record[1]['TOV'] == 'jump ball violation.':  # 201011020DET
                                    record[0]['BP'] = 0 if record[1]['BP'] else 1
                                    qtr_bp = 0 if record[1]['BP'] else 1
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
                                elif 'PF' in record[1] and (record[1]['PF'] == 'Shooting foul' or
                                                            (record[1]['PF'] == 'Loose ball foul' and record[1]['T'] == '0:00.0')):
                                    record[0]['BP'] = record[1]['BP']
                                    qtr_bp = record[1]['BP']
                                elif gm == '201404200HOU':
                                    record.pop(0)
                                    qtr_bp = 0
                                else:
                                    qtr_bp = record[0]['BP']
                            if 'JB' not in record[0]:
                                record.insert(0, {'Q': qtr, 'T': '0:00.0', 'BP': qtr_bp})
                        elif ('PVL' in record[0] and record[0]['PVL'] == 'jump ball') or \
                                ('TVL' in record[0] and record[0]['TVL'] == 'jump ball'):  # 跳球违例，修正球权记录
                            if 'JB' in record[1] and record[1]:
                                record[1]['BP'] = record[0]['BP']
                                qtr_bp = record[0]['BP']
                            else:
                                record.insert(1, {'Q': qtr, 'T': '0:00.0', 'JB': ['', ''], 'BP': record[0]['BP']})
                                qtr_bp = record[0]['BP']
                    record.append({'Q': qtr, 'T': '12:00.0' if qtr == 1 else '24:00.0', 'BP': 0 if qtr_bp else 1})
                else:
                    # if qtr_bp == -1:
                    #     print('跳球记录存疑，', gm)
                    #     print(record)
                    record.append({'Q': qtr, 'T': '36:00.0', 'BP': qtr_bp})
                qtr_ += 1
            for ply in self.yieldPlay(qtr):
                play = Play(ply, qtr)
                # ==========开始对一条记录进行处理==========
                if len(play.play) == 2 and 'Jump' in play.play[1]:  # 跳球记录    [客场队员、主场队员]、得球方
                    # print(play.play)
                    rp, hp, bp = play.jumpball()
                    bpsn = 0 if bp in plyrs[0] else 1  # 球权 0客1主     !!!得球球员部分可能有特殊情况，待改
                    if play.now() == '0:00.0':
                        record.insert(0, {'Q': qtr, 'T': play.now(), 'JB': [rp, hp], 'BP': bpsn})
                        if len(record) == 2 and 'TVL' in record[-1] and record[-1]['TVL'] == 'delay of game':
                            record[-1]['BP'] = record[0]['BP']
                    else:
                        record.append({'Q': qtr, 'T': play.now(), 'JB': [rp, hp], 'BP': bpsn})
                    if bp == '':
                        if len(record) > 1:    # 201612290UTA  42:49.0
                            record[-1]['BP'] = record[-2]['BP']
                        else:
                            # print('跳球存疑')
                            bpsn = -1
                            record[-1]['BP'] = -1
                            # print(record)
                    if gm == '201611120NOP' and play.now() == '12:44.0':    # 201611120NOP  12:44.0
                        record[-1]['BP'] = 1
                    if gm == '202001040CHI' and play.now() == '8:56.0':    # 跳球记录中得球者有误
                        record[-1]['BP'] = 0
                    if gm == '200612150LAL' and play.now() == '48:00.0':
                        record[-1]['BP'] = 0
                    if qtr == 0 and (len(record) == 1 or record[-1]['T'] == '0:00.0'):  # 201412170TOR
                        qtr_bp = bpsn
                    elif qtr == 0 and len(record) == 2 and \
                            ('TVL' in record[0] and record[0]['TVL'] == 'delay of game') or \
                            ('PVL' in record[0] and record[0]['PVL'] == 'delay of game'):
                        qtr_bp = bpsn
                    if len(record) > 2 and 'ORB' in record[-2] and record[-2]['ORB'] == 'Team' and 'SWT'in record[-3]:    # 纠正投篮不中-跳球前的Offensive rebound by Team对球权判断的影响 201802110ATL  8:43.0
                        record[-2]['BP'] = record[-3]['BP']
                    elif len(record) > 2 and 'TOV' in record[-2] and record[-2]['TOV'] == 'turnover' and 'MS'in record[-3]:    # 纠正投篮不中-出现失误-跳球前的失误对球权判断的影响 201801050DEN  32:04.0
                        record[-2]['BP'] = record[-3]['BP']
                    elif len(record) > 2 and 'DRB' in record[-2] and record[-2]['DRB'] == 'Team' and 'MS'in record[-3]:    # 纠正投篮不中-跳球前的Defensive rebound by Team对球权判断的影响 201802110ATL  8:43.0
                        record[-2]['BP'] = record[-3]['BP']
                    elif len(record) > 2 and 'PF' in record[-2] and 'PF'in record[-3]:    # 球在空中时的double foul需通过跳球决定球权，之前的球权暂时延续上一条记录的球权 201912280CHI  39:23.0  https://official.nba.com/rule-no-12-fouls-and-penalties/#doublefoul Double Fouls
                        record[-2]['BP'] = record[-4]['BP']
                        record[-3]['BP'] = record[-4]['BP']
                    if gm == '201702130DEN':    # 开场双方跳球违例（特殊情况）
                        record[1], record[0] = record[0], record[1]
                        record[1], record[2] = record[2], record[1]
                        record[0]['BP'] = 1
                        record[1]['BP'] = 1
                else:
                    rec, ind = play.record()  # 若非长度为6的正常比赛记录行，则返回'', -1
                    s = play.score(ind=ind)
                    # 有得分或投丢
                    if s:
                        if 'makes' in rec:  # 投进    [得分球员、得分]、球权转换
                            record.append(
                                {'Q': qtr, 'T': play.now(), 'MK': [rec.split(' ')[0], s], 'BP': 0 if ind == 5 else 1})
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
                                    record[-1]['BP'] = 0 if record[-1]['MK'][0] in plyrs[0] else 1
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        record[x - 1]['BP'] = record[-1]['BP']
                                        x -= 1
                                elif '1 of 1' in rec:  # 投篮命中追加罚球，期间球权暂不转换
                                    x = -1
                                    # if len(record) > 1 and 'PF' in record[-2] and record[-2]['PF'] == 'Away from play foul':
                                    #     record[-1]['BP'] = 0 if record[-1]['BP'] else 1
                                    # else:
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T'] and record[x]['Q'] == record[x - 1]['Q']:
                                        if 'MS' in record[x - 1] and record[x - 1]['MS'][1] > 1:
                                            break
                                        else:
                                            record[x - 1]['BP'] = 0 if record[-1]['BP'] else 1
                                        x -= 1
                                elif 'clear path' in rec:  # clear path罚球，球权不转换
                                    record[-1]['BP'] = 0 if record[-1]['MK'][0] in plyrs[0] else 1
                        else:  # 投失    [出手球员、得分]，球权暂时仍为进攻方所有
                            if rec.split(' ')[0] == 'misses':
                                continue
                            record.append({'Q': qtr, 'T': play.now(), 'MS': [rec.split(' ')[0], s], 'BP': 0 if ind == 1 else 1})
                            if len(record) == 2 and 'JB' in record[0] and record[0]['BP'] != record[1][
                                'BP']:  # 201910280SAS
                                record[0]['BP'] = record[1]['BP']
                                qtr_bp = record[0]['BP']
                            if 'block by' in rec:  # 盖帽    盖帽球员
                                record[-1]['BLK'] = rec.split(' ')[-1][:-1]
                            if s == 1:
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
                                # if '1 of 2' in rec or '1 of 3' in rec or '2 of 3' in rec:    #
                                #     record[-1]['BP'] = 0 if record[-1]['MK'][0] in plyrs[0] else 1
                                if 'technical' in rec:  # 技术罚球，球权不转换
                                    if len(record) > 1 and 'BP' in record[-2]:
                                        record[-1]['BP'] = record[-2]['BP']
                                elif 'flagrant' in rec:  # 恶犯罚球，球权不转换，继续为罚球球员所在球队所有
                                    record[-1]['BP'] = 0 if record[-1]['MS'][0] in plyrs[0] else 1
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        record[x - 1]['BP'] = record[-1]['BP']
                                        x -= 1
                                elif '1 of 1' in rec:  # 追加罚球，期间球权暂不转换
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        if ('TF' in record[x - 1] and record[x - 1]['TF'] == 'Technical') or \
                                                ('MS' in record[x - 1] and record[x - 1]['MS'][0] not in plyrs[record[-1]['BP']]) or \
                                                ('MK' in record[x - 1] and record[x - 1]['MK'][0] not in plyrs[record[-1]['BP']]):
                                            break
                                        else:
                                            record[x - 1]['BP'] = record[-1]['BP']
                                            x -= 1
                                    if gm == '201710230MIA' and play.now() == '27:37.0':
                                        record[-1]['BP'] = 1
                                if record[-1]['MS'][0] == 'allenja01' and record[-1]['T'] == record[-2]['T'] and \
                                        'TOV' in record[-2] and record[-2]['TOV'] == 'lane violation' and \
                                        record[-2]['plyr'] == 'kurucro01':    # 202008130BRK  31:07.0
                                    record[-2]['BP'] = 1
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and 'DRB' in record[-2] and \
                                    record[-1]['BP'] != record[-2]['BP'] and record[-1]['BP'] == record[-3]['BP'] and 'MK' in record[-3]:    # 纠正同一时间投篮命中-转换投篮不中-转换抢到防守篮板时后两条记录顺序错误问题    201903040LAL 39:01.0
                                record[-1], record[-2] = record[-2], record[-1]
                            if len(record) > 1 and record[-1]['T'] == record[-2]['T'] and 'DRB' in record[-2] and \
                                    record[-2]['DRB'] not in plyrs[record[-1]['BP']] and record[-2]['DRB'] != 'Team':    # 纠正对方防守篮板先于本方投丢的记录顺序错误问题    201902220CHO 14:36.0
                                record[-1], record[-2] = record[-2], record[-1]
                            if '2 of 2' in rec:
                                if 'MK' in record[-2] and record[-2]['MK'][1] == 1 and record[-1]['MS'][0] == record[-2]['MK'][0]:    # 纠正两罚第一罚记成1 of 1的错误    201803270SAC  47:40.0
                                    record[-2]['BP'] = record[-1]['BP']
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'ORB' in record[-2] and 'MK' in record[-3] and record[-2]['ORB'] == record[-3]['MK'][0]:    # 纠正同一时间投篮不中-进攻篮板-投篮命中时记录顺序错误问题    201212150CHI 31:12.0
                                record[-1], record[-3] = record[-3], record[-1]
                                record[-2]['BP'] = record[-3]['BP']
                            if len(record) > 3 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'ORB' in record[-2] and 'DRB' in record[-3] and 'MS' in record[-4] and record[-3]['DRB'] not in plyrs[record[-2]['BP']]:    # 纠正同一时间进攻篮板-投篮不中-对方防守篮板记录顺序错误问题    201204180POR  15:28.0
                                record[-2], record[-3] = record[-3], record[-2]
                                record[-2], record[-1] = record[-1], record[-2]
                    # 前场篮板    前板球员、球权
                    elif 'Offensive rebound' in rec:
                        if rec[-7:] != 'by Team':    # 球员篮板
                            record.append({'Q': qtr, 'T': play.now(), 'ORB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                            if play.now() == record[-2]['T'] and 'MK' in record[-2] and record[-2]['MK'][0] == rec.split(' ')[-1]:
                                record[-1]['BP'] = record[-2]['BP']
                            if record[-1]['T'] == record[-2]['T'] and 'TOV' in record[-2] and record[-1]['ORB'] == record[-2]['plyr']:    # 纠正同时间抢到篮板后失误的记录顺序错误问题    201911070LAC  7:08.0
                                record[-1], record[-2] = record[-2], record[-1]
                            if record[-1]['T'] == record[-2]['T'] and 'TOV' in record[-2] and record[-2]['TOV'] == 'shot clock':    # 纠正同时间抢到篮板后进攻到时记录顺序错误问题    201811240OKC  26:34.0
                                record[-1], record[-2] = record[-2], record[-1]
                            if len(record) > 3 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'MS' in record[-3] and 'DRB' in record[-2] and 'MS' in record[-4] and record[-2]['DRB'] not in plyrs[record[-1]['BP']]:  # 纠正投丢-进攻篮板-投丢-对方防守篮板记录顺序颠倒的情况(***已经被对方防守篮板先于本方投丢的记录顺序错误纠正过一次)    201901060CHI  35:58.0
                                record[-1], record[-3] = record[-3], record[-1]
                                record[-1], record[-2] = record[-2], record[-1]
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] != record[-3]['T'] and \
                                    'MK' in record[-2] and 'MS' in record[-3] and record[-3]['MS'][0] == record[-1]['ORB']:    # 纠正同一时间抢到进攻篮板-助攻队友投篮命中时记录顺序错误问题    201903190MIN 20:32.0
                                record[-1], record[-2] = record[-2], record[-1]
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'TOV' in record[-2] and record[-2]['TOV'] == 'offensive goaltending' and 'MS' in record[-3]:    # 纠正同一时间投失-抢到进攻篮板-进攻干扰球时记录顺序错误问题    201903190MIN 20:32.0
                                record[-1], record[-2] = record[-2], record[-1]
                            if len(record) > 3 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and record[-1]['T'] != record[-4]['T'] and \
                                    'DRB' in record[-2] and 'MS' in record[-3] and 'MS' in record[-4] and record[-4]['MS'][1] == 1:    # 纠正罚丢-进攻篮板-投篮不中-对方防守篮板记录顺序颠倒的情况    201812180ATL  28:49.0
                                record[-3], record[-2] = record[-2], record[-3]
                                record[-1], record[-3] = record[-3], record[-1]
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'MS' in record[-2] and 'MK' in record[-3] and record[-3]['MK'][0] == record[-1]['ORB']:    # 纠正同一时间投失-抢到进攻篮板-投进时记录顺序错误问题    201612170OKC 43:10.0
                                record[-1], record[-2] = record[-2], record[-1]
                                record[-1], record[-3] = record[-3], record[-1]
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'MS' in record[-3] and 'DRB' in record[-2] and record[-2]['DRB'] not in plyrs[record[-3]['BP']]:    # 纠正同一时间抢到进攻篮板-投失-对方抢到防守篮板记录顺序错误问题    201304170MEM  9:05.0
                                record[-1], record[-2] = record[-2], record[-1]
                                record[-2], record[-3] = record[-3], record[-2]
                            if len(record) > 3 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and record[-1]['T'] == record[-4]['T'] and \
                                    'DRB' in record[-3] and 'MS' in record[-2] and 'MS' in record[-4] and record[-4]['MS'][0] in plyrs[record[-2]['BP']]:    # 纠正两罚不中-篮板记录顺序颠倒的情况    201702030HOU  2:39.0
                                record[-1], record[-3] = record[-3], record[-1]
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'MS' in record[-2] and 'TOV' in record[-3] and record[-3]['plyr'] in plyrs[record[-2]['BP']]:    # 纠正同一时间抢到进攻篮板-投失-进攻失误记录顺序错误问题    201201040TOR  34:37.0
                                record[-1], record[-3] = record[-3], record[-1]
                                record[-2], record[-3] = record[-3], record[-2]
                        else:    # Offensive rebound by Team
                            record.append({'Q': qtr, 'T': play.now(), 'ORB': 'Team', 'BP': 0 if ind == 1 else 1})
                            if record[-1]['T'] == record[-2]['T'] and 'JB' in record[-2]:    # 纠正跳球出界后跳球记录中仍记有得球人的错误    201910240DET  44:48.0
                                record[-2]['BP'] = record[-1]['BP']
                            if record[-1]['T'] == record[-2]['T'] and 'TOV' in record[-2] and \
                                    record[-2]['TOV'] == 'shot clock':    # 纠正进攻时间到时后由Offensive rebound by Team确定球权的记录顺序错误问题
                                record[-1], record[-2] = record[-2], record[-1]
                            if record[-1]['T'] == record[-2]['T'] and 'MS' in record[-2] and \
                                    record[-2]['MS'][1] == 1:    # 纠正技术犯规罚球后Offensive rebound by Team确定球权有误的问题    201711190PHO  30:41.0
                                record[-1]['BP'] = record[-2]['BP']
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                'MS' in record[-2] and 'MK' in record[-3] and record[-3]['MK'][0] == record[-2]['MS'][0] and \
                                        record[-3]['MK'][1] == 1 and record[-2]['MS'][1] == 1:    # 纠正前一罚罚丢-后一罚罚进记录顺序颠倒的情况
                                    record[-3], record[-2] = record[-2], record[-3]
                                    record[-1], record[-2] = record[-2], record[-1]
                            if len(record) > 3 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and record[-1]['T'] == record[-4]['T'] and \
                                'DRB' in record[-2] and 'MS' in record[-3] and 'MS' in record[-4] and \
                                        record[-4]['MS'][1] == 1 and record[-3]['MS'][1] == 1:    # 纠正前一罚罚丢-后一罚罚丢记录顺序颠倒的情况    201710210MIA  32:20.0
                                    record[-3], record[-2] = record[-2], record[-3]
                                    record[-4], record[-2] = record[-2], record[-4]
                                    record[-1], record[-3] = record[-3], record[-1]
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'TOV' in record[-2] and record[-2]['TOV'] == 'turnover' and \
                                    'MS' in record[-3] and record[-3]['MS'][0] == record[-2]['plyr']:    # 纠正同一时间投失-抢到进攻篮板-失误时记录顺序错误问题    201802040OKC 34:43.0
                                record[-1], record[-2] = record[-2], record[-1]
                            if len(record) > 3 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and record[-1]['T'] == record[-4]['T'] and \
                                    'MK' in record[-2] and 'MS' in record[-3] and record[-2]['MK'][1] == 1 and record[-3]['MS'][1] == 1:    # 纠正一罚不中-二罚命中记录顺序颠倒的情况    201210310NOH  14:57.0
                                x = -3
                                while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                    if 'PF' in record[x - 1]:
                                        record[-1], record[-2] = record[-2], record[-1]
                                        break
                                    else:
                                        x -= 1
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'TOV' in record[-3] and record[-3]['TOV'] == 'shot clock' and \
                                    'MS' in record[-2] and record[-2]['MS'][0] in plyrs[record[-1]['BP']] and play.now() != '36:00.0':    # 纠正同一时间投失-抢到进攻篮板-进攻到时记录顺序错误问题    201802040OKC 34:43.0
                                record[-1], record[-3] = record[-3], record[-1]
                                record[-3], record[-2] = record[-2], record[-3]
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'MS' in record[-2] and 'TOV' in record[-3] and record[-3]['plyr'] in plyrs[record[-2]['BP']]:    # 纠正同一时间抢到进攻篮板-投失-进攻失误记录顺序错误问题    201201040TOR  34:37.0
                                record[-1], record[-3] = record[-3], record[-1]
                                record[-2], record[-3] = record[-3], record[-2]
                    # 后场篮板    后板球员、球权
                    elif 'Defensive rebound' in rec:
                        if rec[-7:] != 'by Team':
                            record.append(
                                {'Q': qtr, 'T': play.now(), 'DRB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                        else:
                            if play.now() != '36:00.0':
                                record.append({'Q': qtr, 'T': play.now(), 'DRB': 'Team', 'BP': 0 if ind == 1 else 1})
                            if len(record) > 2 and record[-1]['T'] == record[-2]['T'] and record[-1]['T'] == record[-3]['T'] and \
                                    'MS' in record[-2] and 'TF' in record[-3] and record[-3]['TF'] == 'Technical' and record[-2]['MS'][1] == 1:  # 纠正同一时间投失-抢到进攻篮板-失误时记录顺序错误问题    201802040OKC 34:43.0
                                record[-1]['BP'] = record[-2]['BP']
                    # 换人    [上场球员、下场球员、换人球队]
                    elif 'enters' in rec:
                        tmp = rec.split(' ')
                        record.append(
                            {'Q': qtr, 'T': play.now(), 'SWT': [tmp[0], tmp[-1], 0 if tmp[0] in plyrs[0] else 1]})
                        if len(record) > 1 and 'BP' in record[-2]:
                            record[-1]['BP'] = record[-2]['BP']
                    # 暂停
                    elif 'timeout' in rec:
                        tmp = rec.split(' ')
                        if tmp[0] == 'Official':  # 官方暂停
                            record.append({'Q': qtr, 'T': play.now(), 'OTO': ''})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        elif '20' in tmp:  # 短暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'STO': 0 if ind == 1 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        elif 'full' in tmp:  # 长暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'FTO': 0 if ind == 1 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        elif tmp[0] == 'Turnover':  # excessive timeout turnover    失误球队
                            record.append({'Q': qtr, 'T': play.now(), 'ETT': 0 if ind == 1 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        elif tmp[0] == 'Excess':  # Excess timeout    犯规球队（记录在对方球队位置）
                            record.append({'Q': qtr, 'T': play.now(), 'ETO': 0 if ind == 5 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        else:
                            if 'no' not in rec:
                                print(rec, gm)
                    # 犯规
                    elif 'foul' in rec and 'offensive' not in rec:  # 犯规（小写的进攻犯规实为失误统计）
                        # print(rec)
                        tmp = rec.split(' ')
                        ix = tmp.index('by') if 'by' in tmp else -1
                        if 'Turnover' == tmp[0]:
                            plyr = tmp[2]
                            if not plyr:
                                continue
                            record.append(
                                {'Q': qtr, 'T': play.now(), 'TOV': 'foul', 'plyr': plyr, 'BP': 0 if ind == 5 else 1})
                        if 'Technical' in rec:  # 技术犯规（不记入个人犯规）    技犯类型、技犯球员、球权和之前保持一致
                            # if tmp[-1] == 'Team':
                            #     record.append({'Q': qtr, 'T': play.now(), 'TF': 'Technical',
                            #                    'plyr': 'Team', 'BP': 0 if ind == 5 else 1})
                            # else:
                            record.append({'Q': qtr, 'T': play.now(), 'TF': 'Technical', 'plyr': tmp[-1]})
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
                                if gm == '201502060ORL' and record[-1]['D3S'] == 'ellinwa01' and play.now() == '25:40.0':
                                    record[-1]['BP'] = 0
                            continue
                        elif 'Clear path' in rec:  # clear path（计入个人犯规和球队犯规）    犯规球员
                            record.append({'Q': qtr, 'T': play.now(), 'PF': 'Clear path foul', 'plyr': tmp[ix + 1]})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            continue
                        elif 'Teamfoul' in rec:  # 2000赛季后无此项
                            if play.now() == record[-1]['T']:
                                if rec[-4:] != 'Team':
                                    record.append({'Q': qtr, 'T': play.now(), 'TOV': 'Offensive foul',
                                                   'plyr': tmp[-1], 'BP': record[-1]['BP']})
                            else:
                                record.append({'Q': qtr, 'T': play.now(), 'PF': 'Teamfoul', 'BP': 1 if ind == 1 else 0})
                            continue
                        elif 'Double technical foul' in rec:  # 双方技犯    [双方球员]
                            record.append({'Q': qtr, 'T': play.now(), 'DTF': [tmp[-3], tmp[-1]]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            continue
                        # assert 'drawn by' in rec
                        if 'Flagrant foul type 1' in rec:  # 一级恶意犯规（计入个人犯规和球队犯规）    犯规种类、犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF1': int(tmp[3]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            continue
                        if 'Flagrant foul type 2' in rec:  # 二级恶意犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF2': int(tmp[3]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
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
                            record.append({'Q': qtr, 'T': play.now(), 'PF': ' '.join(tmp[:ix]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            if not record[-1]['plyr']:
                                record[-1]['plyr'] = record[-1]['drawn']
                                record[-1]['drawn'] = ''
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            if record[-1]['PF'] == 'Away from play foul':  # 无球犯规追加罚球，之前进球后球权暂不转换
                                if len(record) > 1 and 'MK' in record[-2] and record[-2]['MK'][0] in plyrs[record[-1]['BP']]:
                                    record[-2]['BP'] = record[-1]['BP']
                            if record[-1]['PF'] == 'Shooting foul':  # 无球犯规追加罚球，之前进球后球权暂不转换
                                if len(record) > 1 and 'MK' in record[-2] and record[-2]['MK'][0] in plyrs[record[-1]['BP']]:
                                    record[-2]['BP'] = record[-1]['BP']
                            if ' '.join(tmp[:ix]) not in foultype:
                                foultype.append(' '.join(tmp[:ix]))
                            if (gm == '201512170LAL' and play.now() == '23:30.0' and record[-1]['plyr'] == 'howardw01') or \
                                    (gm == '201503220OKC' and play.now() == '21:44.0' and record[-1]['plyr'] == 'whiteha01') or \
                                    (gm == '201412150PHO' and play.now() == '25:08.0' and record[-1]['plyr'] == 'parkeja01'):
                                record[-1]['BP'] = 0
                    # 失误
                    elif 'Turnover' in rec:  # 失误    失误种类、失误球员、转换球权
                        tmp = rec.split(' ')
                        tp = rec[rec.index('(') + 1:rec.index(';')] if ';' in rec else rec[rec.index('(') + 1:-1]
                        plyr = 'Team' if 'by Team' in rec else tmp[2]
                        if not plyr:
                            continue
                        record.append({'Q': qtr, 'T': play.now(), 'TOV': tp, 'plyr': plyr, 'BP': 0 if ind == 5 else 1})
                        if 'steal by' in rec:  # 抢断    抢断球员
                            record[-1]['STL'] = tmp[-1][:-1]
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
                                if len(record) > 1 and record[-1]['T'] != record[-2]['T']:
                                    record.pop()
                                    # print(gm, '无效TVL:', rec)
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
                            elif gm == '201702140LAL':    # 46:56.0
                                record.pop()
                        else:  # 球员违例    违例种类、违例球员、转换球权
                            if 'jump ball' in rec:  # 跳球违例，明确初始球权
                                if not record:
                                    qtr_bp = 0 if ind == 5 else 1
                            record.append({'Q': qtr, 'T': play.now(), 'PVL': rec[rec.index('(') + 1:-1],
                                           'plyr': rec.split(' ')[2], 'BP': 0 if ind == 5 else 1})
                            if record[-1]['PVL'] == 'double lane':    # 罚球时双方同时提前进线则跳球决定球权
                                if len(record) > 1 and 'BP' in record[-2]:
                                    record[-1]['BP'] = record[-2]['BP']
                            elif record[-1]['PVL'] == 'def goaltending':  # 防守干扰球，球权不做多余转换    201710170GSW  16:53.0
                                if len(record) > 1 and 'MK' in record[-2] and record[-1]['plyr'] in plyrs[record[-2]['BP']]:
                                    record[-1]['BP'] = record[-2]['BP']
                            elif record[-1]['PVL'] == 'lane':  # 罚球提前进线，球权不做多余转换    201710180DET  29:56.0
                                if len(record) > 1 and 'MK' in record[-2] and record[-2]['MK'][1] == 1 and record[-1]['plyr'] in plyrs[record[-2]['BP']]:
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
                            print(play.play, gm)
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

    def find_time_series(self, gm, record):
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
                                    ('TOV' in tmp[ix] and tmp[ix]['plyr'] not in plyrs[bp] and tmp[ix][
                                        'plyr'] != 'Team') or \
                                    ('PF' in tmp[ix] and tmp[ix]['plyr'] not in plyrs[bp]) or \
                                    ('TVL' in tmp[ix] and 'tm' in tmp[ix] and tmp[ix]['tm'] != bp) or \
                                    ('PVL' in tmp[ix] and tmp[ix]['plyr'] not in plyrs[bp]) or \
                                    ('DRB' not in tmp[ix] and 'MK' not in tmp[ix] and 'TVL' not in tmp[ix] and
                                     'TOV' not in tmp[ix] and 'PF' not in tmp[ix] and 'JB' not in tmp[ix] and 'PVL' not in tmp[ix]):
                                flag = 1
                                if gm == '201903030DET.pickle':    # 极少数情况    201903030DET.pickle 33:33.0
                                    flag = 0
                            for r in range(ix, len(tmp)):
                                if tmp[r]['BP'] == bp:
                                    if 'MK' not in tmp[r] and 'TOV' not in tmp[r] and 'PVL' not in tmp[r] and \
                                            'DRB' not in tmp[r] and 'PF' not in tmp[r]:
                                        flag = 1
                                    break
                            # bp = 0 if bp else 1
                            # for r in tmp[ix:]:
                            #     if r['BP'] != bp:
                            #         flag = 1
                            #         break
                            if flag:
                                print('%s，连续%d条记录，时间点：%s' % (gm, len(tmp), time_series))
                                print('初始球权%d，球权转换index:' % bp, ix)
                                for r in tmp:
                                    print(r)
                                print()
                                qtr = int(i['Q']) + 1
                                now = MPTime(i['T'])
                                qtr_end = '%d:00.0' % (qtr * 12)
                                now = MPTime(qtr_end) - now
                                playbyplay_editor_window = GameDetailWindow(gm=gm[:-7], title='第%d节 剩余%s    %s' % (qtr, now, str(i)))
                                playbyplay_editor_window.loop()
                    tmp = [i]
                elif not tmp:
                    tmp.append(i)
                time_series = i['T']
                qtr = i['Q']

    def pace(self, gm, record):  # 回合数统计
        star_of_game = 0
        # 排除赛前的比赛延误警告和跳球违例
        for i in record:
            if ('TVL' in i and (i['TVL'] == 'delay of game' or i['TVL'] == 'jump ball')) or \
                    ('PVL' in i and (i['PVL'] == 'delay of game' or i['PVL'] == 'jump ball')):
                star_of_game += 1
            else:
                if len(i) != 3 and 'JB' not in i:  # 199612280SAC
                    print(gm, i)
                break
        exchange, bp = 0.5, record[star_of_game]['BP']
        rht = [0, 1] if record[star_of_game]['BP'] else [1, 0]
        # print(record[0])
        for i in record[star_of_game:]:
            # print(i, bp)
            if i['BP'] != bp or (len(i) == 3 and (i['T'] == '12:00.0'
                                                  or i['T'] == '24:00.0' or i['T'] == '36:00.0')) or \
                    ((i['T'] == '48:00.0' or i['T'] == '53:00.0'
                      or i['T'] == '58:00.0' or i['T'] == '63:00.0') and 'JB' in i):  # 球权交换或节初或加时赛初跳球:
                # try:
                #     if gm not in ['199611010NJN', '199611010ORL', '199611010VAN', '201910230PHO', '201910240DET'] and \
                #             not ((i['Q'] == 0 and i['T'] == '12:00.0') or (i['Q'] == 1 and i['T'] == '24:00.0') or
                #                  (i['Q'] == 2 and i['T'] == '36:00.0') or (i['Q'] == 3 and i['T'] == '48:00.0') or
                #                  (i['Q'] == 4 and i['T'] == '53:00.0') or (i['Q'] == 5 and i['T'] == '58:00.0') or
                #                  (i['Q'] == 6 and i['T'] == '63:00.0') or (i['Q'] == 7 and i['T'] == '68:00.0')):
                #         assert 'MS' not in i
                # except:
                #     print(gm, i, bp)
                #     raise KeyError
                if not ((i['Q'] == 0 and i['T'] == '12:00.0') or (i['Q'] == 1 and i['T'] == '24:00.0') or
                        (i['Q'] == 2 and i['T'] == '36:00.0') or (i['Q'] == 3 and i['T'] == '48:00.0') or
                        (i['Q'] == 4 and i['T'] == '53:00.0') or (i['Q'] == 5 and i['T'] == '58:00.0') or
                        (i['Q'] == 6 and i['T'] == '63:00.0') or (i['Q'] == 7 and i['T'] == '68:00.0')):  # 排除节末
                    exchange += 0.5
                    bp = i['BP']
                    rht[bp] += 1
                    # print(i, rht)
        print(exchange, rht)

    def game_analyser(self, gm, record):  # 球队、球员单场比赛技术统计，并与实际对比
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
                if i['plyr'] != 'Team':
                    sbtp[0 if i['plyr'] in plyrs[0] else 1][2] += 1
                    plyr_stats = self.plyrstats(self.pm2pn[i['plyr']], [15], plyr_stats)
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
            sum_score_error.append(gm)
        # 判断投篮分项数据
        for i in range(2):
            if sts[i][0] != int(ttl[i][8]) or sts[i][1] != int(ttl[i][9]) or \
                    sts[i][4] != int(ttl[i][5]) or sts[i][5] != int(ttl[i][6]) or \
                    sts[i][6] != int(ttl[i][2]) or sts[i][7] != int(ttl[i][3]):
                shootings_error.append(gm)
                break
        # 判断篮板助攻
        for i in range(2):
            if odta[i][0] != int(ttl[i][11]) or odta[i][1] != int(ttl[i][12]) or \
                    odta[i][2] != int(ttl[i][13]) or odta[i][3] != int(ttl[i][14]):
                odta_error.append(gm)
                break
        # 判断sbtp
        for i in range(2):
            if sbtp[i][0] != int(ttl[i][15]) or sbtp[i][1] != int(ttl[i][16]) or \
                    sbtp[i][2] != int(ttl[i][17]) or sbtp[i][3] != int(ttl[i][18]):
                sbtp_error.append(gm)
                # print(gm)
                # print(sbtp)
                # print(ttl[0])
                # print(ttl[1])
                # for j in plyr_stats:
                #     print(j, plyr_stats[j])
                break
        # print(odta)
        # print(sbtp)
        # print(ttl[0])
        # print(ttl[1])


class GameShooting(object):
    def __init__(self, gm, ROP, HOA=None):
        self.gamemark = gm
        self.gameflow = LoadPickle(gameMarkToDir(gm, ROP, shot=True))
        self.HOA = HOA if HOA != None else None

    def yieldPlay(self):
        if self.HOA != None:
            for p in self.gameflow[self.HOA]:
                yield p
        else:
            for i in range(2):
                for p in self.gameflow[i]:
                    yield p


class GameBoxScore(object):
    def __init__(self, gm, ROP):
        self.gamemark = gm
        self.boxes = LoadPickle(gameMarkToDir(gm, ROP, shot=True))
        self.quarters = len(self.boxes) - 5 if len(self.boxes) > 3 else 0


if __name__ == '__main__':
    regularOrPlayoffs = ['regular', 'playoffs']
    i = 1
    ft, to, vl = [], [], []
    count_games = 0
    for season in range(2006, 2020):
        ss = '%d_%d' % (season, season + 1)
        # print(ss)
        for i in range(2):
            gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
            for gm in tqdm(gms):
                count_games += 1
                # print('\t\t\t' + gm)
                game = Game(gm[:-7], regularOrPlayoffs[i])
                vltmp, totmp, fttmp, record = game.game_scanner(gm[:-7])
                game.find_time_series(gm, record)
                # game.pace(gm[:-7], record)

    #             vltmp, totmp, fttmp, record = game.game_scanner(gm[:-7])
    #             game.game_analyser(gm[:-7], record)
    #             for ix, r in enumerate(record):
    #                 if 'BP' not in r and 'EJT' not in r:
    #                     print(r, gm[:-7])
    #
    #             ft = list(set(ft + fttmp))
    #             to = list(set(to + totmp))
    #             vl = list(set(vl + vltmp))
    # print(len(sum_score_error))
    # print(len(shootings_error))
    # print(len(sbtp_error))
    # print(len(odta_error))
    # print(count_games)
    # print(ft)
    # print(to)
    # print(vl)

    # gm = '201404200HOU'
    # game = Game(gm, 'playoff')
    # _, _, _, record = game.game_scanner(gm)
    # for i in record:
    #     print(i)
    # # game.game_analyser(gm, record)
    # game.pace(gm, record)
    # game.find_time_series(gm, record)




