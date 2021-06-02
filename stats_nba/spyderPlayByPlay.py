#!/usr/bin/python
# -*- coding:utf8 -*-

import sys
sys.path.append('../')
from util import gameMarkToDir, writeToPickle, getCode
from klasses.miscellaneous import MPTime
import os
import requests
from bs4 import BeautifulSoup
import datetime
import time

date = datetime.datetime.strptime('2021-05-08', '%Y-%m-%d')
delta = datetime.timedelta(days=1)
today = time.strftime("%Y-%m-%d", time.localtime())
today = str(datetime.datetime.strptime(today, '%Y-%m-%d') - delta)
while str(date) <= today:
    datestr = date.strftime('%Y-%m-%d')
    # 日期页
    dateurl = 'https://www.nba.com/games?date=%s' % datestr
    datepage = getCode(dateurl, 'UTF-8')
    # 当日所有比赛链接
    URLs = datepage.find('div', class_='md:px-0')
    while not URLs:
        print('md:px-0')
        time.sleep(10)
        datepage = getCode(dateurl, 'UTF-8')
        URLs = datepage.find('div', class_='md:px-0')
    # URLs = URLs.find_all('section')
    # print(URLs)
    if URLs:
        print(dateurl)
        URLs = URLs.find_all('div', class_='md:w-7/12')
        URLs = [x.a.attrs['href'] for x in URLs]
        # print(URLs)
        for URL in URLs:
            # 001季前赛 002常规赛 003全明星 004季后赛
            if '-001' not in URL:
                # print(URL)
                cg = int(URL[-4:])
                gmn = URL[-10:]
                tms = URL.split('/')[-1][:-11]
                season = URL[-7:-5]
                season = int(('19' + season) if season > '95' else ('20' + season))
                ss = '%d_%d' % (season, season + 1)
                oldfn = 'D:/sunyiwu/stat/data_nba/origin/%s/%s-%s.txt' % (ss, gmn, tms)
                newfn = 'D:/sunyiwu/stat/data_nba/origin/%s/%s_%s_%s.txt' % (ss, datestr, gmn, tms)
                if os.path.exists(oldfn):
                    os.rename(oldfn, newfn)
                elif not os.path.exists(newfn):
                    time.sleep(2)
                    if not os.path.exists('D:/sunyiwu/stat/data_nba/origin/%s' % ss):
                        os.mkdir('D:/sunyiwu/stat/data_nba/origin/%s' % ss)
                    gameURL = 'https://www.nba.com%s' % URL
                    y = ''
                    while len(y) < 100000:
                        if '-003' in newfn:
                            y = ''
                            break
                        time.sleep(1)
                        page = getCode(gameURL, 'UTF-8')

                        nr = page.find_all('div', id='__next')
                        if nr:
                            x = page.contents
                            y = str(x[1])
                            # print(len(y))
                        else:
                            print('无内容', newfn)
                            break
                    if len(y) > 1:
                        f = open(newfn, 'w', encoding='utf-8')
                        f.writelines(y)
                        f.close()
    time.sleep(3)
    date = date + delta
# page.raise_for_status()
# print(page.text)

# formdata = {'eventDate': '1996-11-01', 'sort': 'eventDate'}
# page = requests.get(URL, data=formdata, verify=False)
# print(page)

# dldir = 'D:/sunyiwu/stat/data_nba/origin/'
# dlfn = '%s-%s.txt' % (tms, gmn)
# f = open(dldir + dlfn, encoding='utf-8')
# text = f.readlines()
# f.close()

# text = ''.join(text)
# res = [[]]
# page = BeautifulSoup(text, features='lxml')

# actionList = eval(text[text.index('[{"actionNumber"'):text.index(',"source"')])




#%%
# res = [[]]
# table = page.find('div', class_='md:p-5')
# records = table.find_all('article')
# # print(len(records))
# for i in records:
#     # 获取一行记录
#     s = i.find('div').contents
#     # 判断中间记录栏是否包含比分纪录（包含则bf有两个元素，否则只有一个，即时间）
#     bf = s[0].find_all('span')
#     if len(bf) > 1:
#         s = bf + s[1:]
#     ts = [x.text for x in s]
#     if len(bf) == 1:
#         ts.insert(1, '')
#     # 判断是否包含头像，如包含则获取图像编号用于唯一确定球员（双方可能存在last name相同的球员）
#     img = s[-1].find_all('img')
#     if img:
#         pmn = img[0].attrs['src']
#         pmn = pmn.split('/')[-1][:-4]
#         ts.append(pmn)
#     else:
#         ts.append('')
#     # 判断是否新增一节
#     if res[-1]:
#         if '.' in res[-1][-1][0] and ':' in ts[0]:
#             res.append([])
#     res[-1].append(ts)
# assert 3 < len(res) < 8

# writeToPickle('../data_nba/play_by_play/%s/%s' % (ss, filename), res)
    
