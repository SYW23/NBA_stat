#!/usr/bin/python
# -*- coding:utf8 -*-
import sys
sys.path.append('../')
from util import minusMinutes
from klasses.miscellaneous import MPTime
import re


class Play(object):
    # 构造参数：本条play的list，本节序号，主要关注球员唯一识别号，球员主客场
    def __init__(self, lst, ind, pm=None, HOA=None, HomeOrAts=[[4, 5], [2, 1]]):
        self.play = lst  # 0:时间, 1:客队描述, 2:客队加分, 3:比分, 4:主队加分, 5:主队描述
        self.quarter = ind
        self.HOA = HOA
        self.pm = pm
        self.HomeOrAt = HomeOrAts[HOA - 1] if HOA != None else None
        self.r = None
        self.i = None
        if len(self.play) == 6:
            self.i = 1 if self.play[1] else 5
            self.r = self.play[self.i]
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

    def scoreType(self):    # 罚球时返回d = [第x罚, 共y罚]  m = 罚球类型    运动战时返回d = 距离  m = 投篮类型
        s = self.score(ind=self.i)
        if s == 1:
            if ' of ' in self.r:
                if 'n of x' in self.r:
                    d = [1, 1]
                else:
                    r = re.compile('\d+ of \d+')
                    try:
                        r = re.findall(r, self.r)[0]
                    except:
                        print(self.r)
                        raise KeyError
                    d = [int(r[0]), int(r[-1])]
            else:
                d = [1, 1]
            if 'clear path' in self.r:
                m = 'clear path'
            elif 'technical' in self.r:
                m = 'technical'
            elif 'flagrant' in self.r:
                m = 'flagrant'
            else:
                m = ''
        else:
            if ' ft' in self.r:
                r = re.compile('from \d+ ft')
                r = re.findall(r, self.r)
                d = int(r[0].split(' ')[1])
            else:
                d = -1    # 篮下无距离
            if s == 2:
                if 'jump shot' in self.r:
                    m = 'jump shot'
                elif 'layup' in self.r:
                    m = 'layup'
                elif 'dunk' in self.r:
                    m = 'dunk'
                elif 'hook shot' in self.r:
                    m = 'hook shot'
                elif 'tip-in' in self.r:
                    m = 'tip-in'
                else:
                    m = 'shot'
            else:
                m = 'jump shot'    # 三分默认跳投
        return d, m

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

