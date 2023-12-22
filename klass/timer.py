import math
import re
from klass.order import total_ordering


@total_ordering
class MPTime(object):
    def __init__(self, str_time, reverse=True, quarter=-1):    # reverse为True为倒计时模式，qtr为节次
        ans = re.findall("\\d+", str_time)
        if len(ans) == 3:
            if ans[2] == '00':
                self.str_time = str_time[:-3]
            else:
                self.str_time = str_time
            self.min, self.sec, self.msc = [int(x) for x in ans]
        else:
            self.str_time = str_time
            self.min, self.sec = [int(x) for x in ans]
            self.msc = 0
        self.reverse = reverse
        self.quarter = quarter

    def __repr__(self):
        return f"{self.min}:{self.sec:02d}.{self.msc}"

    def __sub__(self, other):
        if self.min - other.min >= 0:
            if self.msc < other.msc:
                self.sec -= 1
                d = self.msc + 10 - other.msc
            else:
                d = self.msc - other.msc
            if self.sec < other.sec:
                self.min -= 1
                c = self.sec + 60 - other.sec
            else:
                c = self.sec - other.sec
            return MPTime(f"{self.min - other.min}:{c:02d}.{d}", reverse=self.reverse)
        else:
            return ''

    def __add__(self, other):
        c = self.sec + other.sec
        d = self.msc + other.msc
        if d >= 10:
            c += 1
            d -= 10
        if c >= 60:
            self.min += 1
            c -= 60
        return MPTime(f"{self.min + other.min}:{c:02d}.{d}", reverse=self.reverse)

    def __eq__(self, other):
        return self.min == other.min and self.sec == other.sec and self.msc == other.msc

    def __lt__(self, other):    # 倒计时形式的早晚比较（越小越晚）
        """
        a = MPTime('46:09.2')
        b = MPTime('47:09.1')
        print(a <= b)    # True
        """
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
                if self.msc >= other.msc:
                    return False
                else:
                    return True

    def average(self, n):  # 返回精确到秒"mm:ss"
        ss = eval(str(self.min) + '*60+' + str(self.sec))
        ss /= (60 * n)
        ss = math.modf(ss)
        return '%d:%02d' % (ss[1], round(ss[0] * 60))

    def average_acc(self, n):  # 返回精确到秒"mm:ss"
        ss = eval(str(self.min) + '*60+' + str(self.sec))
        ss /= (60 * n)
        ss = math.modf(ss)
        return '%d:%.1f' % (ss[1], ss[0] * 60)

    def secs(self):
        return self.min * 60 + self.sec + float('%.1f' % (self.msc / 10))

    def mf(self):
        return self.min + (self.sec + self.msc / 10) / 60


if __name__ == "__main__":
    t1 = MPTime('0:16.5')
    t2 = MPTime('0:32.5')
    print(t1)
    print(t2)
    print(t1 + t2)
    print(t1 - t2)
    print(t2 - t1)
    print(t1 == t2)
    print(t1 > t2)
    print(t1 < t2)
