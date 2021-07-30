import sys
sys.path.append('../')
from klasses.miscellaneous import MPTime


class Play_nba(object):
    def __init__(self, ac):
        self.ac = ac

    def now(self):
        tmp = self.ac['clock']
        min = int(tmp[2:4])
        sec = int(tmp[5:7])
        msc = int(tmp[8:10])
        if len(str(msc)) == 2:
            msc = msc // 10
        return '%d:%02d.%d' % (min, sec, msc)

    def plyr(self):
        return {self.ac['personId']: self.ac['playerNameI']} if self.ac['playerName'] else {}
