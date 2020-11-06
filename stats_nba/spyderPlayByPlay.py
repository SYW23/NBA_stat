#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
sys.path.append('../')
from util import gameMarkToDir, writeToPickle, getCode
from klasses.miscellaneous import MPTime
import os
import requests
from bs4 import BeautifulSoup

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
season = 1996
ss = '%d_%d' % (season, season + 1)
cg = 11
gmn = '002%s0%04d' % (str(season)[2:], cg)
tms = 'sea-vs-uta'
URL = 'https://smetrics.global.nba.com/b/ss/nbasitesprod/10/JS-2.22.0-LAWA/s65654762369094?'
# URL = 'https://www.nba.com/game/%s-%s/play-by-play' % (tms, gmn)
filename = '%s-%s.pickle' % (tms, gmn)
params = 'AQB=1&ndh=1&pf=1&callback=s_c_il[1].doPostbacks&et=1&t=6%2F10%2F2020%209%3A24%3A52%205%20-480&d.&nsid=0&jsonv=1&.d&mid=36791509609666118453415520844677909266&aamlh=11&ce=UTF-8&pageName=nba%3Agames%3Agame-details%3Aplay-by-play&g=https%3A%2F%2Fwww.nba.com%2Fgame%2Fsea-vs-uta-0029600011%2Fplay-by-play&cc=USD&server=www.nba.com&events=event22%2Cevent406&c30=nba%3Agames%3Agame-details%3Aplay-by-play%3Aquarter%3Atab&c31=tab&c32=2&c38=Q3&c39=SEA%20%40%20UTA%2C%201996-11-01&v50=D%3Dc30&pe=lnk_o&pev2=nba%3Agames%3Agame-details%3Aplay-by-play%3Aquarter%3Atab&c.&a.&activitymap.&page=nba%3Agames%3Agame-details%3Aplay-by-play&link=Q2&region=__next&pageIDType=1&.activitymap&.a&.c&pid=nba%3Agames%3Agame-details%3Aplay-by-play&pidt=1&oid=functionsn%28%29%7B%7D&oidt=2&ot=BUTTON&s=1920x1080&c=24&j=1.6&v=N&k=Y&bw=789&bh=1007&mcorgid=248F210755B762187F000101%40AdobeOrg&lrt=513&AQE=1'
# URL = 'https://www.nba.com/games?date=1996-11-01'
# URL = 'https://www.nba.com/game/sea-vs-uta-0029600011/play-by-play'

# page = requests.get(URL, params=params, headers=headers)
# page = getCode(URL, 'UTF-8')
# page.raise_for_status()
# print(page.text)

# formdata = {'eventDate': '1996-11-01', 'sort': 'eventDate'}
# page = requests.get(URL, data=formdata, verify=False)
# print(page)

dldir = 'D:/sunyiwu/stat/data_nba/origin/'
dlfn = '%s-%s.txt' % (tms, gmn)
f = open(dldir + dlfn, encoding='utf-8')
text = f.readlines()
f.close()

text = ''.join(text)
# res = [[]]
page = BeautifulSoup(text, features='lxml')

actionList = eval(text[text.index('[{"actionNumber"'):text.index(',"source"')])




#%%
res = [[]]
table = page.find('div', class_='md:p-5')
records = table.find_all('article')
# print(len(records))
for i in records:
    # 获取一行记录
    s = i.find('div').contents
    # 判断中间记录栏是否包含比分纪录（包含则bf有两个元素，否则只有一个，即时间）
    bf = s[0].find_all('span')
    if len(bf) > 1:
        s = bf + s[1:]
    ts = [x.text for x in s]
    if len(bf) == 1:
        ts.insert(1, '')
    # 判断是否包含头像，如包含则获取图像编号用于唯一确定球员（双方可能存在last name相同的球员）
    img = s[-1].find_all('img')
    if img:
        pmn = img[0].attrs['src']
        pmn = pmn.split('/')[-1][:-4]
        ts.append(pmn)
    else:
        ts.append('')
    # 判断是否新增一节
    if res[-1]:
        if '.' in res[-1][-1][0] and ':' in ts[0]:
            res.append([])
    res[-1].append(ts)
assert 3 < len(res) < 8

# writeToPickle('../data_nba/play_by_play/%s/%s' % (ss, filename), res)
    
