import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import getCode, writeToPickle, LoadPickle
import re

url = 'https://www.basketball-reference.com/players/'
soup = getCode(url, 'UTF-8')

players = {}
letters = soup.find('ul', class_='page_index').find_all('li')
for index, letter in enumerate(letters):
    if index != 23:
        # 首字母URL
        letterURL = 'https://www.basketball-reference.com' + letter.a.attrs['href']
        letterPage = getCode(letterURL, 'UTF-8')
        trs = letterPage.find('table', class_='stats_table').find_all('tr')
        # 列名:
        # 'Player', 'Personal Page URL',
        # 'regularGames'常规赛总出场数, 'regularTime'常规赛总出场时间, 'playoffGames'季后赛总出场数, 'playoffTime'季后赛总出场时间
        # 'From'起始赛季, 'To'终结赛季, 'Pos'位置, 'Ht', 'Wt', 'Birth Date', 'Colleges'
        colName = [x.get_text().strip() for x in trs[0].find_all('th')]
        colName.insert(1, 'Personal Page URL')
        colName = colName[:2] + ['regularGames', 'regularTime', 'playoffGames', 'playoffTime'] + colName[2:]
        
        for tr in tqdm(trs[1:]):
            tds = tr.find_all('td')
            if len(tds) > 0:
                # 球员姓名
                player = tr.find_all('th')[0].a.text
                # player = player.replace(' ', '')
                # player = player.replace('-', '')
                # 球员主页URL
                playerURL = 'https://www.basketball-reference.com' + tr.find_all('th')[0].a.attrs['href']
                # playerPage = getCode(playerURL, 'UTF-8')
                # # 常规赛总出场数、总出场时间
                # rePage = str(playerPage)
                # rePage = rePage[rePage.find('Totals Table'):]
                # rePage = rePage[rePage.find('Career'):]
                # if rePage.find('<td class="left " data-stat="lg_id" >NBA</td>') != -1:
                #     rePage = rePage[rePage.find('<td class="left " data-stat="lg_id" >NBA</td>'):]
                #     re_games = re.compile('<td class="right " data-stat="g" >\d+</td>')
                #     re_minutes = re.compile('<td class="right " data-stat="mp" >\d+</td>')
                #     games_select = re.findall(re_games, rePage)
                #     games = games_select[0].lstrip('<td class="right " data-stat="g" >').rstrip('</td>') if games_select else ''
                #     minutes_select = re.findall(re_minutes, rePage)
                #     minutes = minutes_select[0].lstrip('<td class="right " data-stat="mp" >').rstrip('</td>') if minutes_select else ''
                # else:
                #     games, minutes = '', ''
                # # 季后赛总出场数、总出场时间
                # if rePage.find('Playoffs Totals') != -1:
                #     rePage = rePage[rePage.find('Playoffs Totals'):]
                #     rePage = rePage[rePage.find('Career'):]
                #     re_games = re.compile('<td class="right " data-stat="g" >\d+</td>')
                #     re_minutes = re.compile('<td class="right " data-stat="mp" >\d+</td>')
                #     games_selectP = re.findall(re_games, rePage)
                #     gamesP = games_selectP[0].lstrip('<td class="right " data-stat="g" >').rstrip('</td>') if games_selectP else ''
                #     minutes_selectP = re.findall(re_minutes, rePage)
                #     minutesP = minutes_selectP[0].lstrip('<td class="right " data-stat="mp" >').rstrip('</td>') if minutes_selectP else ''
                # else:
                #     gamesP, minutesP = '', ''

                pm = playerURL.split('/')[-1][:-5]
                players[pm] = [player] + [x.get_text().strip() for x in tds]
                players['reedpa01'] = ['Paul Reed', '2021', '2021', 'F', '6-9', '210', 'June 14, 1999', 'DePaul']
                players['mannini01'] = ['Nico Mannion', '2021', '2021', 'G', '6-2', '190', 'March 14, 2001', '']
                players['forretr01'] = ['Trent Forrest', '2021', '2021', 'G', '6-4', '210', 'June 12, 1998', '']
                players['leesa01'] = ['Saben Lee', '2021', '2021', 'G', '6-2', '183', 'June 23, 1999', '']
                players['sirvyde01'] = ['Deividas Sirvydis', '2021', '2021', 'G', '6-8', '190', 'June 10, 2000', '']
                players['jonesma05'] = ['Mason Jones', '2021', '2021', 'G', '6-4', '200', 'July 21, 1998', 'Connors State College, Arkansas']
                players['martike04'] = ['Kenyon Martin Jr.', '2021', '2021', 'F', '6-6', '215', 'January 6, 2001', '']
                players['harrija01'] = ['Jalen Harris', '2021', '2021', 'G', '6-5', '195', 'August 14, 1998', 'Louisiana Tech, Nevada']
                players['winstca01'] = ['Cassius Winston', '2021', '2021', 'G', '6-1', '185', '', '']
                players['beyty01'] = ['Tyler Bey', '2021', '2021', 'F', '6-7', '215', 'February 10, 1998', '']
                players['marshna01'] = ['Naji Marshall', '2021', '2021', 'F', '6-7', '220', 'January 24, 1998', '']
                players['okongon01'] = ['Onyeka Okongwu', '2021', '2021', 'C', '6-8', '235', 'December 11, 2000', '']
                players['haganas01'] = ['Ashton Hagans', '2021', '2021', 'G', '6-3', '190', 'July 8, 1999', '']
                players['whittgr01'] = ['Greg Whittington', '2021', '2021', 'F', '6-8', '210', 'February 7, 1993', 'Georgetown']
                players['magnawi01'] = ['Will Magnay', '2021', '2021', 'C', '6-10', '234', 'June 10, 1998', 'Tulsa']
                players['cannade01'] = ['Devin Cannady', '2021', '2021', 'G', '6-2', '183', 'May 21, 1996', 'Princeton']
                players['brookar01'] = ['Armoni Brooks', '2021', '2021', 'G', '6-3', '195', 'June 5, 1998', '']
                players['fittsma01'] = ['Malik Fitts', '2021', '2021', 'F', '6-8', '230', 'July 4, 1997', "South Florida, Saint Mary's"]
                players['gillefr01'] = ['Freddie Gillespie', '2021', '2021', 'F', '6-9', '245', 'June 14, 1997', 'Carleton College, Baylor']
                players['frankro01'] = ['Robert Franks', '2021', '2021', 'F', '6-7', '225', 'December 18, 1996', 'Washington State']
                players['oliveca01'] = ['Cameron Oliver', '2021', '2021', 'F', '6-8', '239', 'July 11, 1996', 'Nevada']
                players['louzama01'] = ['Didi Louzada', '2021', '2021', 'F', '6-5', '188', 'February 7, 1999', '']
                players['bryanel01'] = ['Elijah Bryant', '2021', '2021', 'G', '6-5', '210', 'April 19, 1995', 'Elon University, BYU']
writeToPickle('./data/playerBasicInformation.pickle', players)


#%%
pm2pn = {}
for k in list(players):
    pm2pn[k] = players[k][0]
writeToPickle('./data/playermark2playername.pickle', pm2pn)












