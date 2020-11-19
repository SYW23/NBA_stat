#!/usr/bin/python
# -*- coding:utf8 -*-
from util import LoadPickle, getCode, writeToPickle
import os

RoFs = ['regular', 'playoffs']

for season in range(2014, 2020):
    ss = '%d_%d' % (season, season + 1)
    print(ss)
    for i in range(2):
        season_dir = './data/seasons/%s/%s/' % (ss, RoFs[i])
        gms = os.listdir(season_dir)
        for gm in gms:
            c = LoadPickle(season_dir + gm)
            for q, qtr in enumerate(c):
                for ix, r in enumerate(qtr):
                    if len(r) == 6 and 'enters' in (r[1] if r[1] else r[-1]):
                        ind = 1 if r[1] else 5
                        tmp = r[ind].split(' ')
                        pm1, pm2 = tmp[0], tmp[-1]
                        if pm1 == pm2:
                            print(gm, c[q][ix][ind])
                            url = 'https://www.basketball-reference.com/boxscores/pbp/%s.html' % gm[:-7]
                            plays = getCode(url, 'UTF-8')
                            plays = plays.find('table', class_='stats_table').find_all('tr')
                            for play in plays:
                                tdPlays = play.find_all('td')
                                if len(tdPlays) == 6:
                                    for p in tdPlays:
                                        if p.find_all('a'):
                                            s = p.get_text().strip()
                                            if 'enters' in s:
                                                ps = s.split(' enters the game for ')
                                                if len(ps) > 1 and ps[0] == ps[1]:
                                                    pms = []
                                                    for a in p.find_all('a'):
                                                        pms.append(a.attrs['href'].split('/')[-1].split('.')[0])
                                                    correct = '%s enters the game for %s' % (pms[0], pms[1])
                                                    c[q][ix][ind] = correct
                                                    print(c[q][ix][ind])
                                                    writeToPickle(season_dir + gm, c)
