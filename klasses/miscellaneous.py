import math
import numpy as np


class MPTime(object):
    def __init__(self, strtime, reverse=True, qtr=-1):    # reverse为True为倒计时模式，qtr为节次
        if strtime.count(':') == 2:
            assert strtime[-3:] == ':00'
            strtime = strtime[:-3]
        tmp = strtime.index(':')
        self.strtime = strtime
        self.min = int(strtime[:tmp])
        self.sec = int(strtime[tmp+1:tmp+3])
        self.msc = int(strtime[-1]) if '.' in strtime else 0
        self.reverse = reverse
        self.qtr = qtr

    def __repr__(self):
        return '%d:%02d.%d' % (self.min, self.sec, self.msc)

    def __add__(self, other):
        a = [self.min, self.sec, self.msc]
        b = [other.min, other.sec, other.msc]
        c = a[1] + b[1]
        d = a[2] + b[2]
        if d >= 10:
            c += 1
            d -= 10
        if c >= 60:
            a[0] += 1
            c -= 60
        return MPTime('%d:%02d.%d' % ((a[0] + b[0]), c, d), reverse=self.reverse)

    def average(self, n):    # 返回精确到秒"mm:ss"
        ss = eval(str(self.min) + '*60+' + str(self.sec))
        ss /= (60 * n)
        ss = math.modf(ss)
        return '%d:%02d' % (ss[1], round(ss[0] * 60))


class WinLoseCounter(object):
    def __init__(self, single, strwl=''):
        if single:
            self.counter = 1
            self.diff = int(strwl[3:-1])
            self.wl = np.array([1, 0]) if strwl[0] == 'W' else np.array([0, 1])
        else:
            self.counter = 0
            self.diff = 0
            self.wl = np.array([0, 0])

    def __repr__(self):
        return '%d/%d (%d)' % (self.wl[0], self.wl[1], self.diff) if self.diff < 0\
               else '%d/%d (+%d)' % (self.wl[0], self.wl[1], self.diff)

    def __add__(self, other):
        self.counter += 1
        self.diff += other.diff
        self.wl += other.wl
        return self

    def average(self):
        diff_ave = self.diff / self.counter
        return '%d/%d (' % (self.wl[0], self.wl[1]) +\
               ('+%.1f)' % diff_ave if diff_ave > 0 else '%.1f)' % diff_ave)

    def repr(self):
        return '%d/%d (%d)' % (self.wl[0], self.wl[1], self.diff) if self.diff < 0\
               else '%d/%d (+%d)' % (self.wl[0], self.wl[1], self.diff)
