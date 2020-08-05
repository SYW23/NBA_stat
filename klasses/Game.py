import pickle
import sys
sys.path.append('../')
from util import minusMinutes, gameMarkToDir, LoadPickle


class Play:
    # 构造参数：本条play的list，本节序号，主要关注球员唯一识别号，球员主客场
    def __init__(self, lst, ind, pm=None, HOA=None, HomeOrAts=[[4, 5], [2, 1]]):
        self.play = lst
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
        

    def time(self):    # 当前时间（本节倒计时）
        return self.play[0]
    
    def now(self):    # 比赛经过时间（字符串形式：'%d:%02d.%d'）
        if self.quarter <= 3:    # 常规时间
            return minusMinutes('%d:00.0' % ((self.quarter + 1) * 12), self.play[0])
        else:    # 加时赛
            return minusMinutes('%d:00.0' % (48 + (self.quarter - 3) * 5), self.play[0])
    
    def nowtime(self):    # 精确至0.1秒的比赛经过时间（数字）
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
    
    def playRecord(self):
        if len(self.play) == 6:    # 是一条完整比赛记录
            return True
        return False
    
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
    
    
            
class Shooting:
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


class Game:
    # 构造参数：比赛唯一识别号，球员本队，常规赛or季后赛，对手球队简写
    def __init__(self, gm, team, ROP, op, HomeOrAts=[[4, 5], [2, 1]]):
        self.gamemark = gm    # 比赛唯一识别号
        self.gameflow = LoadPickle(gameMarkToDir(gm, ROP))    # 比赛过程详细记录
        self.HOA = 1 if team == gm[-3:] else 0    # 0客1主
        self.hometeam = team if self.HOA else op
        self.roadteam = op if self.HOA else team
        self.quarters = len(self.gameflow)
        self.playFoulTime = []
    
    def yieldPlay(self, qtr):
        for p in self.gameflow[qtr]:
            yield p
        

class GameShooting:
    def __init__(self, gm, ROP, HOA=None):
        self.gamemark = gm
        self.gameflow = LoadPickle(gameMarkToDir(gm, ROP, shot=True))
        self.HOA = HOA
        
    def yieldShooting(self):
        for p in self.gameflow[self.HOA]:
            yield p



