import os
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import getCode, writeToPickle
import re

for season in range(2020, 2021):
    # 赛季
    print('=' * 50)
    print('starting to record season %s_%s' % (str(season-1), str(season)))
    seasonDir = './data/seasons_boxscores/%s_%s' % (str(season-1), str(season))
    if not os.path.exists(seasonDir):
        os.mkdir(seasonDir)
    if not os.path.exists(seasonDir + '/regular'):
        os.mkdir(seasonDir + '/regular')
    if not os.path.exists(seasonDir + '/playoffs'):
        os.mkdir(seasonDir + '/playoffs')

    seasonURL = 'https://www.basketball-reference.com/leagues/NBA_%s_games.html' % str(season)
    seasonGames = getCode(seasonURL, 'UTF-8')
    months = seasonGames.find_all('div', class_='filter')[0].find_all('a')
    monthURLs = ['https://www.basketball-reference.com' + x.attrs['href'] for x in months]
    
    regularOrPlayoff = 0
    for index, monthURL in enumerate(monthURLs):
        # 月份
        print('\tstarting to record month %s' % monthURL.split('-')[2].rstrip('.html'))
        monthPage = getCode(monthURL, 'UTF-8')
        if monthPage.find('table', class_='stats_table'):
            trs = monthPage.find('table', class_='stats_table').find_all('tr')
        else:
            continue
        
        for tr in tqdm(trs[1:]):
            boxscores = []
            tds = tr.find_all('td')
            if len(tds) > 0:
                # date = gamemark
                date = tr.find_all('th')[0].attrs['csk']
                # print(date)
                # 判断比赛是否已保存
                if not (os.path.exists(seasonDir + '/playoffs/%s_boxscores.pickle' % date) or
                        os.path.exists(seasonDir + '/regular/%s_boxscores.pickle' % date)):
                    # 比赛详细过程
                    if not tds[-4].a:    # 尚无比赛记录
                        continue
                    gameURL = 'https://www.basketball-reference.com/boxscores/%s.html' % date
                    gamePage = getCode(gameURL, 'UTF-8')
                    # 比赛结果信息（球队、比分、战绩）
                    scores = gamePage.find('div', class_='scorebox')
                    teams = [x.a.attrs['href'].split('/')[2] for x in scores.find_all('strong')]    # 客主队
                    ss = [int(x.text) for x in scores.find_all('div', class_='score')]    # 比赛最终比分
                    
                    wl_re = re.compile('<div>\d+-\d+</div>')
                    wl = [x[5:-6] for x in re.findall(wl_re, str(scores))]    # 当场比赛结束后球队战绩
                    # if not wl:    # 处理202008150POR特殊情况
                    #     wl = ['34-39', '35-39']
                    if not wl:
                        wl = ['', '']
                    boxscores.append(dict({teams[0]: [ss[0], wl[0]],
                                           teams[1]: [ss[1], wl[1]]}))
                    # 球员数据（整场比赛、进阶、分节、上下半场、加时）
                    for j in ['game-basic', 'game-advanced', 'q1-basic',
                              'q2-basic', 'h1-basic', 'q3-basic',
                              'q4-basic', 'h2-basic', 'ot1-basic',
                              'ot2-basic', 'ot3-basic', 'ot4-basic']:
                        cs = []
                        for i in range(2):
                            chart = []
                            tb = gamePage.find('table', id='box-%s-%s' % (teams[i], j))
                            if not tb:
                                continue
                            charts = tb.find_all('tr')
                            # 表头
                            items = [x.text for x in charts[1].find_all('th')]
                            items[0] = 'players'
                            chart.append(items)
                            for row in charts[2:]:
                                stats = row.find_all('td')
                                if len(stats) > 0:
                                    if row.find('th').a:
                                        pm = row.find('th').a.attrs['href'].split('/')[-1][:-5]
                                    else:
                                        if 'game' not in j:
                                            continue
                                        pm = row.find('th').text
                                    chart.append([pm] + [x.text for x in stats])
                            cs.append(chart)
                        if cs:
                            boxscores.append(cs)
                    # 保存单场比赛数据
                    if regularOrPlayoff:
                        writeToPickle(seasonDir + '/playoffs/%s_boxscores.pickle' % date, boxscores)
                    else:
                        writeToPickle(seasonDir + '/regular/%s_boxscores.pickle' % date, boxscores)
            else:
                ths = tr.find_all('th')
                if len(ths) == 1 and ths[0].get_text().strip() == 'Playoffs':
                    # 找到季后赛分割线
                    print('switch to Playoffs')
                    regularOrPlayoff = 1
   
print('=' * 50)
