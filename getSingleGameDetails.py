import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import getCode, writeToPickle

for season in range(2020, 2021):
    # 赛季
    print('=' * 50)
    print('starting to record season %s_%s' % (str(season-1), str(season)))
    seasonDir = './data/seasons/%s_%s' % (str(season-1), str(season))
    if not os.path.exists(seasonDir):
        os.mkdir(seasonDir)
    if not os.path.exists(seasonDir + '/regular'):
        os.mkdir(seasonDir + '/regular')
    if not os.path.exists(seasonDir + '/playoffs'):
        os.mkdir(seasonDir + '/playoffs')
    
    seasonuRegularSmmary = []
    seasonuPlayoffSmmary = []
    seasonURL = 'https://www.basketball-reference.com/leagues/NBA_%s_games.html' % str(season)
    seasonGames = getCode(seasonURL, 'UTF-8')
    months = seasonGames.find_all('div', class_='filter')[0].find_all('a')
    monthURLs = ['https://www.basketball-reference.com' + x.attrs['href'] for x in months]
    
    regularOrPlayoff = 0
    for index, monthURL in enumerate(monthURLs):
        print(monthURL)
        # 月份
        print('\tstarting to record month %s' % monthURL.split('-')[-1][:-5])
        monthPage = getCode(monthURL, 'UTF-8')
        trs = monthPage.find('table', class_='stats_table').find_all('tr')
        
        colName = [x.get_text().strip() for x in trs[0].find_all('th')]
        colNumber = len(colName)
        if index == 0:
            seasonuRegularSmmary.append(colName)
            seasonuPlayoffSmmary.append(colName)
        
        #%%
        for tr in tqdm(trs[1:]):
            gameProcess = []
            qtr = -1
            tds = tr.find_all('td')
            #%%
            if len(tds) > 0:
                assert len(tds) == colNumber - 1
                # 比赛基本信息
                date = tr.find_all('th')[0].attrs['csk']
                gameDetails = [date] + [x.get_text().strip() for x in tds]
                # 判断比赛是否已保存
                if not (os.path.exists(seasonDir + '/playoffs/%s.pickle' % date) or
                        os.path.exists(seasonDir + '/regular/%s.pickle' % date)):
                    # 比赛详细过程
                    if not tds[-4].a:
                        continue
                    gameURL = 'https://www.basketball-reference.com' + '/boxscores/pbp/' + tds[-4].a.attrs['href'].lstrip('/boxscores')
                    gamePage = getCode(gameURL, 'UTF-8')
                    plays = gamePage.find('table', class_='stats_table').find_all('tr')
                    for play in plays:
                        thPlays = play.find_all('th')
                        tdPlays = play.find_all('td')
                        if len(thPlays) == 1:
                            # 定位节间
                            gameProcess.append([])
                            qtr += 1
                        elif len(tdPlays) == 2 or len(tdPlays) == 6:
                            pTmp = []
                            # 定位(start/end of quarter 或者 跳球) or 比赛记录中包含球员名的部分，替换成独一无二的球员代号
                            for p in tdPlays:
                                aa = p.find_all('a')
                                if aa:
                                    sentence_o = p.get_text().strip()
                                    for a in aa:
                                        # print(sentence_o, a.attrs['href'].split('/')[-1].rstrip('.html'), gameURL)
                                        if '/players/T/Team.html' != a.attrs['href'] and '/players/N/NULL.html' != a.attrs['href'] and 'Technical foul by' != sentence_o and 'ejected from game' != sentence_o:
                                            sentence_o = sentence_o.replace(a.string, a.attrs['href'].split('/')[-1].rstrip('.html'))
                                        elif 'Technical foul by' == sentence_o:
                                            sentence_o = sentence_o + a.attrs['href'].split('/')[-1].rstrip('.html')
                                        elif 'ejected from game' == sentence_o:
                                            sentence_o = a.attrs['href'].split('/')[-1].rstrip('.html') + sentence_o
                                    pTmp.append(sentence_o)
                                else:
                                    pTmp.append(p.get_text().strip())
                            gameProcess[qtr].append(pTmp)
                        else:
                            pass
                    # 保存单场比赛数据
                    if regularOrPlayoff:
                        writeToPickle(seasonDir + '/playoffs/%s.pickle' % date, gameProcess)
                    else:
                        writeToPickle(seasonDir + '/regular/%s.pickle' % date, gameProcess)
                # 更新赛季比赛列表
                if regularOrPlayoff:
                    seasonuPlayoffSmmary.append(gameDetails)
                else:
                    seasonuRegularSmmary.append(gameDetails)
            else:
                ths = tr.find_all('th')
                if len(ths) == 1 and ths[0].get_text().strip() == 'Playoffs':
                    # 找到季后赛分割线
                    print('switch to Playoffs')
                    regularOrPlayoff = 1
    writeToPickle(seasonDir + '/seasonRegularSummary.pickle', seasonuRegularSmmary)
    writeToPickle(seasonDir + '/seasonPlayoffSummary.pickle', seasonuPlayoffSmmary)      
print('=' * 50)
