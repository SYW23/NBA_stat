import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import getCode, writeToPickle
import re

url = 'https://www.basketball-reference.com/players/'
soup = getCode(url, 'UTF-8')

players = []
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
                playerPage = getCode(playerURL, 'UTF-8')
                # 常规赛总出场数、总出场时间
                rePage = str(playerPage)
                rePage = rePage[rePage.find('Totals Table'):]
                rePage = rePage[rePage.find('Career'):]
                if rePage.find('<td class="left " data-stat="lg_id" >NBA</td>') != -1:
                    rePage = rePage[rePage.find('<td class="left " data-stat="lg_id" >NBA</td>'):]
                    re_games = re.compile('<td class="right " data-stat="g" >\d+</td>')
                    re_minutes = re.compile('<td class="right " data-stat="mp" >\d+</td>')
                    games_select = re.findall(re_games, rePage)
                    games = games_select[0].lstrip('<td class="right " data-stat="g" >').rstrip('</td>') if games_select else ''
                    minutes_select = re.findall(re_minutes, rePage)
                    minutes = minutes_select[0].lstrip('<td class="right " data-stat="mp" >').rstrip('</td>') if minutes_select else ''
                else:
                    games, minutes = '', ''
                # 季后赛总出场数、总出场时间
                if rePage.find('Playoffs Totals') != -1:
                    rePage = rePage[rePage.find('Playoffs Totals'):]
                    rePage = rePage[rePage.find('Career'):]
                    re_games = re.compile('<td class="right " data-stat="g" >\d+</td>')
                    re_minutes = re.compile('<td class="right " data-stat="mp" >\d+</td>')
                    games_selectP = re.findall(re_games, rePage)
                    gamesP = games_selectP[0].lstrip('<td class="right " data-stat="g" >').rstrip('</td>') if games_selectP else ''
                    minutes_selectP = re.findall(re_minutes, rePage)
                    minutesP = minutes_selectP[0].lstrip('<td class="right " data-stat="mp" >').rstrip('</td>') if minutes_selectP else ''
                else:
                    gamesP, minutesP = '', ''
                
                players.append([player, playerURL, games, minutes, gamesP, minutesP] + [x.get_text().strip() for x in tds])
writeToPickle('./data/playerBasicInformation.pickle', [colName] + players)












