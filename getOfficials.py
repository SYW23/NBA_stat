# 85-86赛季开始由执法裁判记录
# 94-95赛季开始记录比赛总时长
import os
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import getCode, writeToPickle, LoadPickle
import re
import time


for season in range(2020, 2021):
    refs = LoadPickle('./data/refereeURLs.pickle')
    res = []    # [gm, Referees, Attendance, Time of Game]
    ss = '%d_%d' % (season-1, season)
    # 赛季
    print('=' * 50 + '\nstarting to record season %s' % ss)
    seasondir = './data/seasons/%s/' % ss
    for RoP in ['Regular', 'Playoff']:
        tb = LoadPickle(seasondir + 'season%sSummary.pickle' % RoP)
        for gm in tqdm(tb[1:]):
            if gm[0] in ['195101140PHW']:
                res.append([gm[0], '', 6665, ''])
            elif gm[0] in ['197511260LAL']:
                continue
            else:
                gameURL = 'https://www.basketball-reference.com/boxscores/%s.html' % gm[0]
                gamePage = getCode(gameURL, 'UTF-8')
                # s = time.time())
                # q = gamePage.find('div', id='content').find_all('strong')
                # print(time.time() - s)
                infmtns = [x.parent\
                           for x in gamePage.find('div', id='content').find_all('strong')\
                           if 'Off' in x.text or 'Att' in x.text or 'Time' in x.text]
                # print(time.time() - s)
                reftmp = []
                gtmp = {}
                for i in infmtns:
                    if 'Off' in i.text:
                        rs = i.find_all('a')
                        if rs != None:
                            for r in rs:
                                url, rn = r.attrs['href'], r.text
                                if rn not in refs:
                                    refs[rn] = url
                                reftmp.append(rn)       
                        else:    # 裁判无个人URL
                            reftmp = i.text.split('\xa0')[1].split(', ')
                    elif 'Att' in i.text:
                        gtmp['A'] = int(i.text.split('\xa0')[1].replace(',', ''))
                    else:
                        gtmp['T'] = i.text.split('\xa0')[1]
                
                if reftmp or gtmp:
                    res.append([gm[0], ', '.join(reftmp),
                                gtmp['A'] if 'A' in gtmp else -1,
                                gtmp['T'] if 'T' in gtmp else ''])
                # print(time.time() - s)

    if res:
        df = pd.DataFrame(res, columns=['gm', 'Referees', 'Attendance', 'Time of Game'])
        writeToPickle('./data/seasons_RAT/%s.pickle' % ss, df)
    writeToPickle('./data/refereeURLs.pickle', refs)






