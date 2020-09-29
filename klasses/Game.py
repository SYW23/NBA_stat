import sys
sys.path.append('../')
from util import minusMinutes, gameMarkToDir, LoadPickle
from klasses.miscellaneous import MPTime
import os
from tqdm import tqdm


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
        self.bxscr = LoadPickle(gameMarkToDir(gm, ROP, tp=2))
    
    def yieldPlay(self, qtr):
        for p in self.gameflow[qtr]:
            yield p

    def teamplyrs(self):
        plyrs = [[], []]
        for i, tm in enumerate(self.bxscr[1]):
            assert tm[0][0] == 'players'
            assert tm[-1][0] == 'Team Totals'
            for p in tm[1:-1]:
                plyrs[i].append(p[0])
        return plyrs

    def game_scanner(self, gm):
        record = []
        plyrs = self.teamplyrs()
        foultype = []
        totype = []
        for qtr in range(self.quarters):
            for ply in self.yieldPlay(qtr):
                play = Play(ply, qtr)
                if len(play.play) == 2 and 'Jump' in play.play[1]:    # 跳球记录    [客场队员、主场队员]、得球方
                    # print(play.play)
                    rp, hp, bp = play.jumpball()
                    bpsn = 0 if bp in plyrs[0] else 1    # 球权 0客1主
                    record.append({'Q': qtr, 'T': play.now(), 'JB': [rp, hp], 'BP': bpsn})    # 得球球员部分可能有特殊情况，待改
                else:
                    rec, ind = play.record()    # 若非长度为6的正常比赛记录行，则返回'', -1
                    s = play.score(ind=ind)
                    if s:    # 有得分或投丢
                        if 'makes' in rec:    # 投进    [得分球员、得分]、球权转换
                            record.append({'Q': qtr, 'T': play.now(), 'MK': [rec.split(' ')[0], s], 'BP': 0 if ind == 5 else 1})
                            if 'assist' in rec:    # 助攻    助攻球员
                                record[-1]['AST'] = rec.split(' ')[-1][:-1]
                        else:    # 投失    [出手球员、得分]，球权暂时仍为进攻方所有
                            record.append({'Q': qtr, 'T': play.now(), 'MS': [rec.split(' ')[0], s], 'BP': 0 if ind == 1 else 1})
                            if 'block by' in rec:    # 盖帽    盖帽球员
                                record[-1]['BLK'] = rec.split(' ')[-1][:-1]
                    elif 'Offensive rebound' in rec:    # 前场篮板    前板球员、球权
                        record.append({'Q': qtr, 'T': play.now(), 'ORB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                    elif 'Defensive rebound' in rec:    # 后场篮板    后板球员、球权
                        record.append({'Q': qtr, 'T': play.now(), 'DRB': rec.split(' ')[-1], 'BP': 0 if ind == 1 else 1})
                    elif 'enters' in rec:    # 换人    [上场球员、下场球员、换人球队]
                        tmp = rec.split(' ')
                        record.append({'Q': qtr, 'T': play.now(), 'SWT': [tmp[0], tmp[1], 0 if tmp[0] in plyrs[0] else 1]})
                        if len(record) > 1 and 'BP' in record[-2]:
                            record[-1]['BP'] = 1 if record[-2]['BP'] == 1 else 0
                    elif 'timeout' in rec:
                        tmp = rec.split(' ')
                        if tmp[0] == 'Official':    # 官方暂停
                            record.append({'Q': qtr, 'T': play.now(), 'OTO': ''})
                        elif '20' in tmp:    # 短暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'STO': 0 if ind == 1 else 1})
                        elif 'full' in tmp:    # 长暂停    暂停球队
                            record.append({'Q': qtr, 'T': play.now(), 'FTO': 0 if ind == 1 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = 1 if record[-2]['BP'] == 1 else 0
                        elif tmp[0] == 'Turnover':    # excessive timeout turnover    失误球队
                            record.append({'Q': qtr, 'T': play.now(), 'ETT': 0 if ind == 1 else 1})
                        elif tmp[0] == 'Excess':    # Excess timeout    犯规球队（记录在对方球队位置）
                            record.append({'Q': qtr, 'T': play.now(), 'ETO': 0 if ind == 5 else 1})
                        else:
                            if 'no' not in rec:
                                print(rec, gm)
                    elif 'foul' in rec and 'offensive' not in rec:    # 犯规（小写的进攻犯规实为失误统计）
                        # print(rec)
                        if 'Technical' in rec:    # 技术犯规    犯规球员
                            record.append({'Q': qtr, 'T': play.now(), 'TF': rec.split(' ')[-1]})
                            continue
                        elif 'Def 3 sec' in rec:    # 防守3秒    犯规球员
                            record.append({'Q': qtr, 'T': play.now(), 'D3T': rec.split(' ')[-1]})
                            continue
                        elif 'Clear path' in rec:    # clear path    犯规球员
                            record.append({'Q': qtr, 'T': play.now(), 'CPH': rec.split(' ')[-1]})
                            continue
                        # assert 'drawn by' in rec
                        tmp = rec.split(' ')
                        ix = tmp.index('by')
                        if tmp[0] == 'Flagrant foul type 1':    # 一级恶意犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF1': int(tmp[3]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            continue
                        if tmp[0] == 'Flagrant foul type 2':    # 二级恶意犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            record.append({'Q': qtr, 'T': play.now(), 'FF2': int(tmp[3]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            continue
                        elif 'foul by' in rec:    # 犯规    犯规种类、犯规球员、造犯规球员、球权待定
                            if rec[-2:] == 'by':
                                continue
                            record.append({'Q': qtr, 'T': play.now(), 'PF': ' '.join(tmp[:ix]), 'plyr': tmp[ix + 1],
                                           'drawn': rec.split(' ')[-1][:-1] if 'drawn by' in rec else ''})
                            if record[-1]['PF'] in ['Offensive foul']:    # 转换球权
                                if len(record) > 1 and 'BP' in record[-2]:
                                    record[-1]['BP'] = 1 if record[-2]['BP'] == 0 else 0
                            elif record[-1]['PF'] in ['Shooting foul', 'Personal take foul', 'Personal foul']:    # 球权不变
                                if len(record) > 1 and 'BP' in record[-2]:
                                    record[-1]['BP'] = 1 if record[-2]['BP'] == 1 else 0
                            elif record[-1]['PF'] in ['Loose ball foul']:
                                record[-1]['BP'] = 0 if ind == 5 else 1
                            if ' '.join(tmp[:ix]) not in foultype:
                                foultype.append(' '.join(tmp[:ix]))
                    elif 'Turnover' in rec:    # 失误    失误种类、失误球员、转换球权
                        tmp = rec.split(' ')
                        tp = rec[rec.index('(') + 1:rec.index(';')] if ';' in rec else rec[rec.index('(') + 1:-1]
                        record.append({'Q': qtr, 'T': play.now(), 'TOV': tp, 'plyr': tmp[2], 'BP': 0 if ind == 5 else 1})
                        if 'steal by' in rec:    # 抢断    抢断球员
                            record[-1]['STL'] = rec.split(' ')[-1][:-1]
                        if tp not in totype:
                            totype.append(tp)
                    elif 'Violation by' in rec:
                        if 'Team' in rec:    # 球队违例    违例种类、违例球队、转换球权
                            record.append({'Q': qtr, 'T': play.now(), 'TVL': rec[rec.index('(') + 1:-1],
                                           'tm': 0 if ind == 1 else 1, 'BP': 0 if ind == 5 else 1})
                        else:    # 球员违例    违例种类、违例球员、转换球权
                            record.append({'Q': qtr, 'T': play.now(), 'PVL': rec[rec.index('(') + 1:-1],
                                           'plyr': rec.split(' ')[2], 'BP': 0 if ind == 5 else 1})
                    elif 'Instant' in rec:    # 若录像回放之后改判会是什么情况
                        if 'Challenge' in rec:    # 教练挑战    挑战球队0客1主
                            record.append({'Q': qtr, 'T': play.now(), 'CCH': 0 if ind == 1 else 1})
                        else:    # 录像回放    0客1主
                            record.append({'Q': qtr, 'T': play.now(), 'IRP': 0 if ind == 1 else 1})
                            if len(record) > 1 and 'BP' in record[-2]:
                                record[-1]['BP'] = 1 if record[-2]['BP'] == 1 else 0
                    elif 'ejected' in rec:    # 驱逐出场    被驱逐球员
                        record.append({'Q': qtr, 'T': play.now(), 'EJT': rec.split(' ')[0]})
                    elif 'Defensive three seconds' in rec:    # 防守三秒    违例球员
                        record.append({'Q': qtr, 'T': play.now(), 'D3S': rec.split(' ')[-1]})
                    else:
                        if rec:
                            print(play.play, gm)
        return sorted(totype), sorted(foultype), record

    def game_analyser(self, gm, record):
        ss = [0, 0]
        sum_score_error = []
        for i in record:
            if 'MK' in i:
                ss[i['BP'] - 1] += i['MK'][1]
            # elif 'MS' in i:
            #     ss[i['BP']] += i['MS'][1]
        if ss != [x[0] for x in self.bxscr[0].values()]:
            sum_score_error.append(gm)



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
    for season in range(1996, 2020):
        ss = '%d_%d' % (season, season + 1)
        # print(ss)
        for i in range(2):
            gms = os.listdir('D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoffs[i]))
            for gm in tqdm(gms):
                # print('\t\t\t' + gm)
                game = Game(gm[:-7], regularOrPlayoffs[i])
                totmp, fttmp, record = game.game_scanner(gm[:-7])
                game.game_analyser(gm[:-7], record)

                ft = list(set(ft + fttmp))
                to = list(set(to + totmp))
    print(ft)
    print(to)
    for i in record:
        print(i)
    # game.game_analyser(record)




