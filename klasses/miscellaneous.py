import math
import numpy as np
import re


class MPTime(object):
    def __init__(self, strtime, reverse=True, qtr=-1):    # reverse为True为倒计时模式，qtr为节次
        ans = re.findall('\d+', strtime)
        if len(ans) == 3:
            if ans[2] == '00':
                self.strtime = strtime[:-3]
            else:
                self.strtime = strtime
            [self.min, self.sec, self.msc] = [int(x) for x in ans]
        else:
            self.strtime = strtime
            [self.min, self.sec] = [int(x) for x in ans]
            self.msc = 0
        self.reverse = reverse
        self.qtr = qtr

    def __repr__(self):
        return '%d:%02d.%d' % (self.min, self.sec, self.msc)

    def __sub__(self, other):
        a = [self.min, self.sec, self.msc]
        b = [other.min, other.sec, other.msc]
        if a[0] - b[0] >= 0:
            if a[2] < b[2]:
                a[1] -= 1
                d = a[2] + 10 - b[2]
            else:
                d = a[2] - b[2]
            if a[1] < b[1]:
                a[0] -= 1
                c = a[1] + 60 - b[1]
            else:
                c = a[1] - b[1]
            return MPTime('%d:%02d.%d' % ((a[0] - b[0]), c, d), reverse=self.reverse)
        else:
            return ''

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

    def __le__(self, other):    # 倒计时形式的早晚比较（越小越晚）
        '''
        a = MPTime('46:09.2')
        b = MPTime('47:09.1')
        print(a <= b)    # True
        '''
        if self.min > other.min:
            return False
        elif self.min < other.min:
            return True
        else:
            if self.sec > other.sec:
                return False
            elif self.sec < other.sec:
                return True
            else:
                if self.msc > other.msc:
                    return False
                else:
                    return True

    def average(self, n):    # 返回精确到秒"mm:ss"
        ss = eval(str(self.min) + '*60+' + str(self.sec))
        ss /= (60 * n)
        ss = math.modf(ss)
        return '%d:%02d' % (ss[1], round(ss[0] * 60))

    def average_acc(self, n):    # 返回精确到秒"mm:ss"
        ss = eval(str(self.min) + '*60+' + str(self.sec))
        ss /= (60 * n)
        ss = math.modf(ss)
        return '%d:%.1f' % (ss[1], ss[0] * 60)

    def secs(self):
        return self.min * 60 + self.sec

    def mf(self):
        return self.min + self.sec / 60


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
        return '%dW/%dL (%d)' % (self.wl[0], self.wl[1], self.diff) if self.diff < 0\
               else '%dW/%dL (+%d)' % (self.wl[0], self.wl[1], self.diff)

    def __add__(self, other):
        self.counter += 1
        self.diff += other.diff
        self.wl += other.wl
        return self

    def average(self):
        # print(self.diff, self.counter)
        diff_ave = self.diff / self.counter
        return '%dW/%dL (' % (self.wl[0], self.wl[1]) +\
               ('+%.1f)' % diff_ave if diff_ave > 0 else '%.1f)' % diff_ave)

    def repr(self):
        return '%dW/%dL (%d)' % (self.wl[0], self.wl[1], self.diff) if self.diff < 0\
               else '%dW/%dL (+%d)' % (self.wl[0], self.wl[1], self.diff)
