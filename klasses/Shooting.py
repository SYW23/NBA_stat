#!/usr/bin/python
# -*- coding:utf8 -*-
import sys
sys.path.append('../')
from util import gameMarkToDir, LoadPickle


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

