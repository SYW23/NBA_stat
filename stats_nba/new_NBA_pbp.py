import sys
sys.path.append('../')
from util import writeToPickle, LoadPickle, gameMark_nba2bbr, LoadText


# 1610612737 ATL
# 1610612747 LAL
# actionList = LoadPickle('new_type.pickle')


# for i in actionList:
#     if i['actionType'] == 'stoppage':
#         print(i)

pm2pn = LoadPickle('../data/playermark2playername.pickle')
print(pm2pn['martike04'])
print(pm2pn['diakima01'])
