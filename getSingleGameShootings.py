import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import getCode, writeToPickle

for season in range(2021, 2022):
    # 赛季
    print('=' * 50)
    print('starting to record season %s_%s' % (str(season-1), str(season)))
    seasonDir = './data/seasons_shot/%s_%s' % (str(season-1), str(season))
    if not os.path.exists(seasonDir):
        os.mkdir(seasonDir)
    if not os.path.exists(seasonDir + '/regular'):
        os.mkdir(seasonDir + '/regular')
    if not os.path.exists(seasonDir + '/playoff'):
        os.mkdir(seasonDir + '/playoff')

    seasonURL = 'https://www.basketball-reference.com/leagues/NBA_%s_games.html' % str(season)
    seasonGames = getCode(seasonURL, 'UTF-8')
    months = seasonGames.find_all('div', class_ ='filter')[0].find_all('a')
    monthURLs = ['https://www.basketball-reference.com' + x.attrs['href'] for x in months]
    
    regularOrPlayoff = 0
    for index, monthURL in enumerate(monthURLs):
        # 月份
        print('\tstarting to record month %s' % monthURL.split('-')[-1][:-5])
        monthPage = getCode(monthURL, 'UTF-8')
        trs = monthPage.find('table', class_='stats_table').find_all('tr')
        
        for tr in tqdm(trs[1:]):
            gameProcess = []
            tds = tr.find_all('td')
            if len(tds) > 0:
                # 比赛基本信息
                date = tr.find_all('th')[0].attrs['csk']
                # 判断比赛是否已保存
                if not (os.path.exists(seasonDir + '/playoff/%s_shot.pickle' % date) or
                        os.path.exists(seasonDir + '/regular/%s_shot.pickle' % date)):
                    # 比赛详细过程
                    if not tds[-4].a:
                        continue
                    gameURL = 'https://www.basketball-reference.com' + '/boxscores/shot-chart/' + tds[-4].a.attrs['href'].lstrip('/boxscores')
                    gamePage = getCode(gameURL, 'UTF-8')
                    charts = gamePage.find_all('div', class_='shot-area')
                    try:
                        assert len(charts) == 2
                    except:
                        print('%s：本场比赛缺失投篮点数据！' % date)
                        continue
                    shootings = [[], []]
                    for i in range(2):
                        shoots = charts[i].find_all('div')
                        for shoot in shoots:
                            shootings[i].append([shoot.attrs['style'], shoot.attrs['tip'], shoot.attrs['class']])
                    # 保存单场比赛数据
                    if regularOrPlayoff:
                        writeToPickle(seasonDir + '/playoff/%s_shot.pickle' % date, shootings)
                    else:
                        writeToPickle(seasonDir + '/regular/%s_shot.pickle' % date, shootings)
            else:
                ths = tr.find_all('th')
                if len(ths) == 1 and ths[0].get_text().strip() == 'Playoffs':
                    # 找到季后赛分割线
                    print('switch to Playoffs')
                    regularOrPlayoff = 1
   
print('=' * 50)
