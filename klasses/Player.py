import pickle
import sys
sys.path.append('../')
from util import minusMinutes, gameMarkToDir

class Player():
    def __init__(self, pm, ROP):    # 构造参数：球员唯一识别号，常规赛or季后赛
        self.playerFileDir = './data/players/' + pm + '/%sGames/%sGameBasicStat.pickle' % (ROP, ROP)
        f = open(self.playerFileDir, 'rb')
        self.playerGames = pickle.load(f)
        f.close()
        self.seasons = len(self.playerGames)\
                          if ROP == 'regular'\
                          else len(self.playerGames) - 1
