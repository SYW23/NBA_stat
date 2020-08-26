import sys
sys.path.append('../')
from util import minusMinutes, LoadPickle

class Season():
    def __init__(self, startYear, ROP):
        self.ROP = 'playoffs' if ROP == 'playoff' else ROP
        filename = 'seasonRegularSummary.pickle'\
                   if ROP == 'regular'\
                   else 'seasonPlayoffSummary.pickle'
        self.gamelist = LoadPickle('./data/seasons/%d_%d/%s'
                                   % (startYear, startYear + 1, filename))
        self.gameNos = len(self.gamelist) - 1
        
    def yieldGM(self):
        # 返回gamemark和game文件路径
        for i in self.gamelist[1:]:
            startYear = int(i[0][:4])
            month = int(i[0][4:6])
            if month < 9:
                startYear -= 1
            yield i[0], './data/seasons/%d_%d/%s/%s.pickle'\
                        % (startYear, startYear + 1, self.ROP, i[0])
            
    