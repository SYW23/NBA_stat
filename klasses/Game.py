import pickle
import sys
sys.path.append('../')
from util import minusMinutes, gameMarkToDir


class Play:
    # 构造参数：本条play的list，本节序号，主要关注球员唯一识别号，球员主客场
    def __init__(self, lst, ind, pm=None, HOA=None, HomeOrAts=[[4, 5], [2, 1]]):
        self.play = lst
        self.quarter = ind
        self.HOA = HOA
        self.pm = pm
        self.HomeOrAt = HomeOrAts[HOA-1] if HOA != None else None

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
                return 'road', diff
            else:
                return 'home', diff
    
    def playerMadeShoot(self):    # 判断球员是否得分
        if len(self.play) == 6:    # 是一条完整比赛记录
            if self.play[self.HomeOrAt[1]]:    # play的1或5索引下有比赛情况记录
                if self.play[self.HomeOrAt[1]].split(' ')[0] == self.pm and\
                   self.play[self.HomeOrAt[0]]:    # 球员匹配且有得分纪录
                    return True
        return False
    
    def playerMissShoot(self):    # 判断球员是否投失
        if len(self.play) == 6:    # 是一条完整比赛记录
            if self.play[self.HomeOrAt[1]]:    # play的1或5索引下有比赛情况记录
                if self.play[self.HomeOrAt[1]].split(' ')[0] == self.pm and\
                   'misses no shot' not in self.play[self.HomeOrAt[1]] and\
                   'misses' in self.play[self.HomeOrAt[1]]:    # 球员匹配且无得分纪录
                    return True
        return False

    def score(self, ind):    # 返回得分或投失分数值
        statement = self.play[ind]
        if 'free throw' in statement:
            return 1
        elif '2-pt' in statement:
            return 2
        elif '3-pt' in statement:
            return 3


class Game:
    # 构造参数：比赛唯一识别号，球员本队，常规赛or季后赛，对手球队简写
    def __init__(self, gm, team, ROP, op, HomeOrAts=[[4, 5], [2, 1]]):
        self.gamemark = gm    # 比赛唯一识别号
        f = open(gameMarkToDir(gm, ROP), 'rb')
        self.gameflow = pickle.load(f)    # 比赛过程详细记录
        f.close()
        self.HOA = 1 if team == gm[-3:] else 0    # 0客1主
        self.hometeam = team if self.HOA else op
        self.roadteam = op if self.HOA else team
        self.quarters = len(self.gameflow)
    
    def ps(self):
        pass
        
