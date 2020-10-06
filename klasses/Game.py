import sys
sys.path.append('../')
from util import minusMinutes, gameMarkToDir, LoadPickle
from klasses.miscellaneous import MPTime
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
        self.play = lst    # 0:时间, 1:客队描述, 2:客队加分, 3:比分, 4:主队加分, 5:主队描述
        self.quarter = ind
        self.HOA = HOA
        self.pm = pm
        self.HomeOrAt = HomeOrAts[HOA-1] if HOA != None else None
        oppoHOA = None if HOA == None else 0 if HOA else 1
        self.oppoHomeOrAt = HomeOrAts[oppoHOA-1] if oppoHOA != None else None
        self.playDisc = self.play[self.HomeOrAt[1]]\
            if len(self.play) == 6 and self.HomeOrAt != None else None
        self.oppoPlayDisc = self.play[self.oppoHomeOrAt[1]]\
            if len(self.play) == 6 and self.oppoHomeOrAt != None else None
        
    # 无偏方法（无主客队之分）
    def time(self):    # 当前时间（本节倒计时）
        return MPTime(self.play[0])
    
    def now(self):    # 比赛经过时间（字符串形式：'%d:%02d.%d'）
        if self.quarter <= 3:    # 常规时间
            return minusMinutes('%d:00.0' % ((self.quarter + 1) * 12), self.play[0])
        else:    # 加时赛
            return minusMinutes('%d:00.0' % (48 + (self.quarter - 3) * 5), self.play[0])
    
    def nowtime(self):    # 精确至0.1秒的比赛经过时间（数字，单位秒）
        t = self.now()
        minute, second, miniSec = [int(x) for x in [t[:-5], t[-4:-2], t[-1]]]
        now = 60 * minute + second + 0.1 * miniSec
        return now
    
    def leaderAndDiff(self):    # 返回领先球队并计算分差（计算了本条play记录的计分之后）
        scores = [int(x) for x in self.play[3].split('-')]
        diff = abs(scores[0] - scores[1])
        if scores[0] == scores[1]:
            return 'tie', diff
        else:
            if scores[0] > scores[1]:
                return 0, diff    # 0客1主
            else:
                return 1, diff    # 0客1主

    def diffbeforescore(self, score):
        scores = [int(x) for x in self.play[3].split('-')]
        if self.play[2] or self.play[4]:
            if self.play[2]:
                scores[0] -= score
            else:
                scores[1] -= score
        return abs(scores[0] - scores[1])
    
    def playRecord(self):
        if len(self.play) == 6:    # 是一条完整比赛记录
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
        return j[2], j[4], j[5][1:]    # 客队跳球球员、主队跳球球员、得球球员

    def record(self):    # 返回本条记录主要内容
        if self.playRecord():
            return self.play[1] if self.play[1] else self.play[5],\
                   1 if self.play[1] else 5
        else:
            return '', -1

    # 有/无偏方法
    def score(self, ind=None):    # 返回得分或投失分数值
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
        if self.playDisc:    # 主队有比赛情况记录
            return True
        return False
    
    def oppoPlay(self):
        if self.play[self.oppoHomeOrAt[1]]:    #  对手有比赛情况记录
            return True
        return False
    
    def playerMadeShoot(self):    # 判断球员是否得分，前提：playRecord、teamPlay
        if self.playDisc.split(' ')[0] == self.pm and\
           self.play[self.HomeOrAt[0]]:    # 球员匹配且有得分纪录
            return True
        return False
    
    def playerMissShoot(self):    # 判断球员是否投失，前提：playRecord、teamPlay
        if self.playDisc.split(' ')[0] == self.pm and\
           'misses no shot' not in self.playDisc and\
           'misses' in self.playDisc:    # 球员匹配且无得分纪录
            return True
        return False
    
    def playerOffReb(self):    # 判断球员是否有进攻篮板，前提：playRecord、teamPlay
        if 'by %s' % self.pm in self.playDisc and 'Offensive' in self.playDisc:
            return True
        return False

    def playerDefReb(self):    # 判断球员是否有防守篮板，前提：playRecord、teamPlay
        if 'by %s' % self.pm in self.playDisc and 'Defensive' in self.playDisc:
            return True
        return False

    def playerAst(self):    # 判断球员是否助攻，前提：playRecord、teamPlay
        if self.playDisc.split(' ')[0] != self.pm and\
        'assist by' in self.playDisc and self.pm in self.playDisc:
            return True
        return False
    
    def playerTO(self):    # 判断球员是否助攻，前提：playRecord、teamPlay
        if 'Turnover by %s' % self.pm in self.playDisc:
            return True
        return False
    
    def playerStl(self):    # 判断球员是否抢断，前提：playRecord、oppoPlay
        if 'steal by %s' % self.pm in self.oppoPlayDisc:
            return True
        return False
    
    def playerBlk(self):    # 判断球员是否盖帽，前提：playRecord、oppoPlay
        if 'block by by %s' % self.pm in self.oppoPlayDisc:
            return True
        return False
    
    
            
class Shooting(object):
    def __init__(self, lst):
        self.record = lst
        self.marginX = 5
        self.marginY = 10
        
    def posi(self, season):    # 投篮点坐标
        cors = self.record[0].split(';')
        x = int(cors[1].split(':')[1].rstrip('px')) + self.marginX
        y = int(cors[0].split(':')[1].rstrip('px')) + self.marginY
        if season >= 2013:
            y += 20
        return x, y
    
    def quarter(self):    # 节次
        return int(self.record[2][1][-1])
    
    def nowtime(self):    # 时间
        return self.record[1].split(' ')[2]
    
    def score(self):    # 分数
        return 2 if '2-pointer' in self.record[1] else 3
    
    def distance(self):    # 距离
        return int(self.record[1].split('<br>')[-2].split(' ')[-2])
    
    def TTL(self):    # 领先/打平/落后
        if 'leads' in self.record[1]:
            return 'lead'
        elif 'trails' in self.record[1]:
            return 'trail'
        elif 'tied' in self.record[1]:
            return 'tie'
        return ''
    
    def diff(self):    # 分差（以主/客场球队视角）
        ss = self.record[1].split(' ')[-1].split('-')
        return ss[0] - ss[1]
    
    def pm(self):    # playermark
        return self.record[2][2].split('-')[1]
    
    def MM(self):
        return 1 if self.record[2][3] == 'make' else 0


class Game(object):
    # 构造参数：比赛唯一识别号，球员本队，常规赛or季后赛，对手球队简写
    def __init__(self, gm, ROP, team=None, op=None, HomeOrAts=[[4, 5], [2, 1]]):
        self.gm = gm    # 比赛唯一识别号
        self.gameflow = LoadPickle(gameMarkToDir(gm, ROP))    # 比赛过程详细记录
        if team:
            self.HOA = 1 if team == gm[-3:] else 0    # 0客1主
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
        foultype = []
        totype = []
        qtr_bp, qtr_ = -1, 1
        for qtr in range(self.quarters):
            if 0 < qtr < 4 and qtr == qtr_:
                if qtr == 1 or qtr == 2:
                    record.append({'Q': qtr, 'T': '12:00.0' if qtr == 1 else '24:00.0', 'BP': 0 if qtr_bp else 1})
                else:
                    record.append({'Q': qtr, 'T': '36:00.0', 'BP': qtr_bp})
                qtr_ += 1
            for ply in self.yieldPlay(qtr):
                play = Play(ply, qtr)
                if len(play.play) == 2 and 'Jump' in play.play[1]:    # 跳球记录    [客场队员、主场队员]、得球方
                    # print(play.play)
                    rp, hp, bp = play.jumpball()
                    bpsn = 0 if bp in plyrs[0] else 1    # 球权 0客1主
                    record.append({'Q': qtr, 'T': play.now(), 'JB': [rp, hp], 'BP': bpsn})    # 得球球员部分可能有特殊情况，待改
                    if qtr == 0 and len(record) == 1:
                        qtr_bp = bpsn
                else:
                    rec, ind = play.record()    # 若非长度为6的正常比赛记录行，则返回'', -1
                    s = play.score(ind=ind)
                    # 有得分或投丢
                    if s:
                        if 'makes' in rec:    # 投进    [得分球员、得分]、球权转换
                            record.append({'Q': qtr, 'T': play.now(), 'MK': [rec.split(' ')[0], s], 'BP': 0 if ind == 5 else 1})
                            if 'assist' in rec:    # 助攻    助攻球员
                                record[-1]['AST'] = rec.split(' ')[-1][:-1]
                            if s == 1:
                                if '1 of 2' in rec or '1 of 3' in rec or '2 of 3' in rec:
                                    record[-1]['BP'] = 0 if record[-1]['MK'][0] in plyrs[0] else 1
                                if 'technical' in rec:    # 技术罚球，球权不转换
                                    if len(record) > 1 and 'BP' in record[-2]:
                                        record[-1]['BP'] = record[-2]['BP']
                                elif 'flagrant' in rec:    # 恶犯罚球，球权不转换，继续为罚球球员所在球队所有
                                    record[-1]['BP'] = 0 if record[-1]['MK'][0] in plyrs[0] else 1
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        record[x - 1]['BP'] = record[-1]['BP']
                                        x -= 1
                                elif '1 of 1' in rec:    # 投篮命中追加罚球，期间球权暂不转换
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        record[x - 1]['BP'] = 0 if record[-1]['BP'] else 1
                                        x -= 1
                        else:    # 投失    [出手球员、得分]，球权暂时仍为进攻方所有
                            if rec.split(' ')[0] == 'misses':
                                continue
                            record.append({'Q': qtr, 'T': play.now(), 'MS': [rec.split(' ')[0], s], 'BP': 0 if ind == 1 else 1})
                            if 'block by' in rec:    # 盖帽    盖帽球员
                                record[-1]['BLK'] = rec.split(' ')[-1][:-1]
                            if s == 1:
                                if 'flagrant' in rec:    # 恶犯罚球，球权不转换，继续为罚球球员所在球队所有
                                    record[-1]['BP'] = 0 if record[-1]['MS'][0] in plyrs[0] else 1
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        record[x - 1]['BP'] = record[-1]['BP']
                                        x -= 1
                                elif '1 of 1' in rec:    # 追加罚球，期间球权暂不转换
                                    x = -1
                                    while len(record) >= 1 - x and record[x]['T'] == record[x - 1]['T']:
                                        record[x - 1]['BP'] = record[-1]['BP']
                                        x -= 1
                    # 前场篮板    前板球员、球权
                    elif 'Offensive rebound' in rec:
                        if rec[-7:] != 'by Team':
                            record.append({'Q': qtr, 'T': play.now(), 'ORB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                    # 后场篮板    后板球员、球权
                    elif 'Defensive rebound' in rec:
                        if rec[-7:] != 'by Team':
                            record.append({'Q': qtr, 'T': play.now(), 'DRB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                        else:
                            record.append({'Q': qtr, 'T': play.now(), 'DRB': 'Team', 'BP': 0 if ind == 1 else 1})
                    # 换人    [上场球员、下场球员、换人球队]
                    elif 'enters' in rec:
                        tmp = rec.split(' ')
                        record.append({'Q': qtr, 'T': play.now(), 'SWT': [tmp[0], tmp[-1], 0 if tmp[0] in plyrs[0] else 1]})
                        if len(record) > 1 and 'BP' in record[-2]:
                            record[-1]['BP'] = record[-2]['BP']
                    # 暂停
                    elif 'timeout' in rec:
                        tmp = rec.split(' ')
                        if tmp[0] == 'Official':    # 官方暂停
                            record.append({'Q': qtr, 'T': play.now(), 'OTO': ''})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        elif '20' in tmp:    # 短暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'STO': 0 if ind == 1 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        elif 'full' in tmp:    # 长暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'FTO': 0 if ind == 1 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        elif tmp[0] == 'Turnover':    # excessive timeout turnover    失误球队
                            record.append({'Q': qtr, 'T': play.now(), 'ETT': 0 if ind == 1 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        elif tmp[0] == 'Excess':    # Excess timeout    犯规球队（记录在对方球队位置）
                            record.append({'Q': qtr, 'T': play.now(), 'ETO': 0 if ind == 5 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                        else:
                            if 'no' not in rec:
                                print(rec, gm)
                    # 犯规
                    elif 'foul' in rec and 'offensive' not in rec:    # 犯规（小写的进攻犯规实为失误统计）
                        # print(rec)
                        tmp = rec.split(' ')
                        ix = tmp.index('by') if 'by' in tmp else -1
                        if 'Turnover' == tmp[0]:
                            plyr = tmp[2]
                            if not plyr:
                                continue
                            record.append({'Q': qtr, 'T': play.now(), 'TOV': 'foul', 'plyr': plyr, 'BP': 0 if ind == 5 else 1})
                        if 'Technical' in rec and rec[-4:] != 'Team':    # 技术犯规（不记入个人犯规）    技犯类型、技犯球员、球权和之前保持一致
                            record.append({'Q': qtr, 'T': play.now(), 'TF': 'Technical', 'plyr': tmp[-1]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = 1 if record[-2]['BP'] == 0 else 0
                            continue
                        elif 'tech foul' in rec or 'Taunting technical' in rec:    # 技术犯规（不记入个人犯规）    技犯类型、技犯球员、球权和之前保持一致
                            record.append({'Q': qtr, 'T': play.now(), 'TF': ' '.join(tmp[:ix]), 'plyr': tmp[-1]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = 1 if record[-2]['BP'] == 0 else 0
                            continue
                        elif 'Def 3 sec' in rec:    # 防守3秒违例    违例球员、球权不变
                            record.append({'Q': qtr, 'T': play.now(), 'D3S': tmp[-1]})
                            record[-1]['BP'] = 1 if record[-1]['D3S'] in plyrs[0] else 0
                            continue
                        elif 'Clear path' in rec:    # clear path（计入个人犯规和球队犯规）    犯规球员
                            record.append({'Q': qtr, 'T': play.now(), 'PF': 'Clear path foul', 'plyr': tmp[ix + 1]})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            continue
                        elif 'Teamfoul' in rec:    # 2000赛季后无此项
                            if play.now() == record[-1]['T']:
                                if rec[-4:] != 'Team':
                                    record.append({'Q': qtr, 'T': play.now(), 'TOV': 'Offensive foul',
                                                   'plyr': tmp[-1], 'BP': record[-1]['BP']})
                            else:
                                record.append({'Q': qtr, 'T': play.now(), 'PF': 'Teamfoul', 'BP': 1 if ind == 1 else 0})
                            continue
                        elif 'Double technical foul' in rec:    # 双方技犯    [双方球员]
                            record.append({'Q': qtr, 'T': play.now(), 'DTF': [tmp[-3], tmp[-1]]})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = record[-2]['BP']
                            continue
                        # assert 'drawn by' in rec
                        if 'Flagrant foul type 1' in rec:    # 一级恶意犯规（计入个人犯规和球队犯规）    犯规种类、犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF1': int(tmp[3]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            continue
                        if 'Flagrant foul type 2' in rec:    # 二级恶意犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF2': int(tmp[3]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            continue
                        if 'Double personal foul' in rec:    # 双方犯规    犯规种类、犯规球员、造犯规球员、球权待定
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
                        if 'foul by' in rec:    # 其他犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            if rec[-2:] == 'by':
                                continue
                            record.append({'Q': qtr, 'T': play.now(), 'PF': ' '.join(tmp[:ix]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            record[-1]['BP'] = 1 if record[-1]['plyr'] in plyrs[0] else 0
                            if ' '.join(tmp[:ix]) not in foultype:
                                foultype.append(' '.join(tmp[:ix]))
                    # 失误
                    elif 'Turnover' in rec:    # 失误    失误种类、失误球员、转换球权
                        tmp = rec.split(' ')
                        tp = rec[rec.index('(') + 1:rec.index(';')] if ';' in rec else rec[rec.index('(') + 1:-1]
                        plyr = 'Team' if 'by Team' in rec else tmp[2]
                        if not plyr:
                            continue
                        record.append({'Q': qtr, 'T': play.now(), 'TOV': tp, 'plyr': plyr, 'BP': 0 if ind == 5 else 1})
                        if 'steal by' in rec:    # 抢断    抢断球员
                            record[-1]['STL'] = tmp[-1][:-1]
                        if tp not in totype:
                            totype.append(tp)
                    # 违例
                    elif 'Violation by' in rec:
                        if 'Team' in rec:    # 球队违例    违例种类、违例球队、转换球权
                            record.append({'Q': qtr, 'T': play.now(), 'TVL': rec[rec.index('(') + 1:-1],
                                           'tm': 0 if ind == 1 else 1, 'BP': 0 if ind == 5 else 1})
                        else:    # 球员违例    违例种类、违例球员、转换球权
                            record.append({'Q': qtr, 'T': play.now(), 'PVL': rec[rec.index('(') + 1:-1],
                                           'plyr': rec.split(' ')[2], 'BP': 0 if ind == 5 else 1})
                    # 回放
                    elif 'Instant' in rec:    # 若录像回放之后改判会是什么情况
                        if 'Challenge' in rec:    # 教练挑战    挑战球队0客1主
                            record.append({'Q': qtr, 'T': play.now(), 'CCH': 0 if ind == 1 else 1})
                        else:    # 录像回放    0客1主
                            record.append({'Q': qtr, 'T': play.now(), 'IRP': 0 if ind == 1 else 1})
                        if len(record) > 1 and 'BP' in record[-2]:
                            record[-1]['BP'] = record[-2]['BP']
                    # 驱逐
                    elif 'ejected' in rec:    # 驱逐出场    被驱逐球员
                        record.append({'Q': qtr, 'T': play.now(), 'EJT': rec.split(' ')[0]})
                        if len(record) > 1 and 'BP' in record[-2]:
                            record[-1]['BP'] = record[-2]['BP']
                    # 防守三秒（违例）
                    elif 'Defensive three seconds' in rec:    # 防守三秒    违例球员
                        record.append({'Q': qtr, 'T': play.now(), 'D3S': rec.split(' ')[-1]})
                        record[-1]['BP'] = 1 if record[-1]['D3S'] in plyrs[0] else 0
                    # 例外情况（应无）
                    else:
                        if rec:
                            print(play.play, gm)
        return sorted(totype), sorted(foultype), record

    @ staticmethod
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

    def game_analyser(self, gm, record):
        plyrs = self.teamplyrs()
        ttl = [self.bxscr[1][0][-1], self.bxscr[1][1][-1]]
        plyr_stats = {}
        ss = [0, 0]
        exchange, bp = 0, record[0]['BP']
        rht = [0, 1] if record[0]['BP'] else [1, 0]
        # print(record[0])
        sts = np.zeros((2, 8))    # 0罚进1罚球出手2两分进3两分出手4三分进5三分出手6运动进7运动出手
        odta = np.zeros((2, 4))    # 0前板1后板2篮板3助攻
        sbtp = np.zeros((2, 4))    # 0抢断1盖帽2失误3犯规
        for i in record:
            # 回合数
            if i['BP'] != bp:
                # print(i)
                exchange += 0.5
                bp = i['BP']
                rht[bp] += 1
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
            elif 'ORB' in i:
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
        # print(exchange)
        # print(rht)


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
    ft, to = [], []
    count_games = 0
    for season in range(1996, 2020):
        ss = '%d_%d' % (season, season + 1)
        # print(ss)
        for i in range(2):
            gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
            for gm in tqdm(gms):
                count_games += 1
                # print('\t\t\t' + gm)
                game = Game(gm[:-7], regularOrPlayoffs[i])
                totmp, fttmp, record = game.game_scanner(gm[:-7])
                game.game_analyser(gm[:-7], record)
                for ix, r in enumerate(record):
                    if 'BP' not in r and 'EJT' not in r:
                        print(r, gm[:-7])

                ft = list(set(ft + fttmp))
                to = list(set(to + totmp))
    print(len(sum_score_error))
    print(len(shootings_error))
    print(len(sbtp_error))
    print(len(odta_error))
    print(count_games)
    print(ft)
    print(to)
    # game = Game('202009260LAL', 'playoffs')
    # _, _, record = game.game_scanner('202009260LAL')
    # # for i in record:
    # #     print(i)
    # game.game_analyser('202009260LAL', record)




