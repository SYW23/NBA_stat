#!/usr/bin/python
# -*- coding:utf8 -*-
import os
import sys
from operator import itemgetter
sys.path.append('../')
from util import LoadText, writeToPickle


#%%
seasonsdir = 'D:/sunyiwu/stat/data_nba/origin/'
seasons = os.listdir(seasonsdir)

# ks = ['shotResult', 'isFieldGoal', 'location', 'actionType', 'subType', 'videoAvailable']
# d = {'shotResult': [], 'isFieldGoal': [], 'location': [], 'actionType': [], 'subType': [], 'videoAvailable': []}
# sts = {}
plyrNo = {}
teamNo = {}

for ss in seasons:
    print('赛季', ss)
    gms = [x for x in os.listdir(seasonsdir + ss) if '_003' not in x]
    print('\t', '总比赛数', len(gms))
    print()
    for gm in gms:
        pbp = ''.join(LoadText(seasonsdir + ss + '/' + gm))
        if '[{"actionNumber"' in pbp:
            # print(gm)
            actionList = eval(pbp[pbp.index('[{"actionNumber"'):pbp.index(',"source"')])
            # actionList = sorted(actionList, key=itemgetter("actionNumber"))
            
            for ix, ac in enumerate(actionList):
                if ac['personId'] and ac['playerName'] and ac['personId'] not in plyrNo:
                    plyrNo[ac['personId']] = [ac['playerName'], ac['playerNameI']]
                if ac['teamId'] and ac['teamTricode'] and ac['teamId'] not in teamNo:
                    teamNo[ac['teamId']] = ac['teamTricode']
# =============================================================================
#                 if ix == 1 and ac['actionType'] != 'Jump Ball                               ':
#                     if actionList[0]['actionType'] != 'Jump Ball                               ' and actionList[2]['actionType'] != 'Jump Ball                               ' and actionList[3]['actionType'] != 'Jump Ball                               ':
#                         print('\t', '无跳球记录', gm)
#                 for k in ks:
#                     if ac[k] not in d[k]:
#                         d[k].append(ac[k])
#                     if k == 'actionType':
#                         if ac[k] not in sts:
#                             sts[ac[k]] = []
#                         if ac['subType'] not in sts[ac[k]]:
#                             sts[ac[k]].append(ac['subType'])
# =============================================================================
        else:
            print('\t', '无pbp记录', gm)
    print()

#%%
# writeToPickle('notions.pickle', sts)
writeToPickle('plyrNo_NBA.pickle', plyrNo)
