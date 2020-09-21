from util import getCode, writeToPickle
import pickle
import os
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from klasses.Player import Player
from klasses.stats_items import regular_items_en, playoff_items_en

regularOrPlayoffs = ['regular', 'playoff']
# ========更新常规赛历史得分榜前250名=========================================================
# url= 'https://www.basketball-reference.com/leaders/pts_career.html'
# soup = getCode(url, 'UTF-8')
# players = soup.find_all('table', class_='suppress_glossary')[2].find_all('tr')
# ll = []
# for p in players[1:]:
#     td = p.find_all('td')
#     ll.append(td[1].a.attrs['href'].split('/')[-1].rstrip('.html'))
# f = open('top250.txt', 'w')
# f.write(str(ll))
# f.close()
# =============================================================================

f = open('./data/playerBasicInformation.pickle', 'rb')
playerInf = pickle.load(f)
f.close()

#%%
for i in playerInf[::-1]:    # james 2067
    url = i[1]
    print(url)
    last_season = int(i[7])
    if last_season > 2018:
        # 获取网页源代码
        playerPage = getCode(url, 'UTF-8')
        if not playerPage.find_all('h1', itemprop="name"):
            continue
        # 球员英文名
        playerEnglishName = playerPage.find_all('h1', itemprop="name")[0].string
        pm = url.split('/')[-1][:-5]
        pn = i[1].split('/')[-1][:-5]
        
        # -----常规赛-----
        seasonAVE = []
        singleGAMES = []
        seasonURLs = []
        seasons = playerPage.find('table', id='per_game').find_all('tr')    # 赛季平均
        # 赛季表表头
        items = [x.text for x in seasons[0].find_all('th')]
            # ----逐赛季扫描----
        for ind, season in enumerate(seasons[1:]):
            if season.find_all('th'):
                th = season.find_all('th')[0]
                # print(th)
            else:
                continue
            tds = season.find_all('td')
            if th.text != 'Career':
                if tds[2].text != 'NBA':    # 只记录NBA比赛
                    continue
                seasonSTR = th.text[:4]
                seasonSTR += '-' + str(int(seasonSTR) + 1)
                if season.find_all('th')[0].find('span', class_='sr_star'):
                    seasonSTR += ' *'
                seasonAVE.append([seasonSTR] + [x.text for x in tds])
                # ----单赛季每场比赛详细数据----
                seasonURL = 'https://www.basketball-reference.com/' + th.a.attrs['href']
                if seasonURL not in seasonURLs:
                    seasonURLs.append(seasonURL)
                    print(seasonURL[-5:-1])
                    seasonPage = getCode(seasonURL, 'UTF-8')
                    title = seasonPage.find('div', class_='section_heading').find_all('span')    # 表格标题，用于排除季后赛
                    if 'Playoffs' not in title[0].attrs['data-label']:
                        if not seasonPage.find('table', class_='stats_table'):
                            continue
                        trs = seasonPage.find('table', class_='stats_table').find_all('tr')
                        # if seasonURL[-5:-1] >= str(last_season):    # 检查最后一个赛季
                        # 遍历行
                        for tr in trs:
                            tds = tr.find_all('td')
                            if len(tds) > 1:
                                gm = tds[1].a.attrs['href'].lstrip('/boxscores/').rstrip('.html')    # 日期
                                # if gm > last_game:    # 检查日期
                                if len(tds) > 10:    # 排除重复表头行（20场重复一次）以及缺席比赛行（inactivate）
                                    gameStat = [x.get_text().strip() for x in tds]
                                    gameStat[1] = gm    # 将Date列置为比赛标志符
                                    singleGAMES.append(gameStat)
                                elif len(tds) > 1:    # 缺席比赛行（inactivate）
                                    gameStat = [x.get_text().strip() for x in tds]
                                    gameStat[1] = gm
                                    gameStat += [''] * (29 - len(gameStat))    # 用''补全剩余单元格
                                    singleGAMES.append(gameStat)
            else:
                break
        # ----生涯及分队场均----
        for ss in seasons[ind+1:]:
            th = ss.find_all('th')[0].text
            tds = ss.find_all('td')
            if (th or tds[2].text == 'NBA') and\
               not (th == 'Career' and tds[2].text == 'TOT') and\
               tds[2].text == 'NBA':
                if not th:
                    th = 'Career'
                seasonAVE.append([th] + [x.text for x in tds])
        # 写入csv文件
        if seasonAVE:
            if not os.path.exists('./data/players/%s' % pm):
                os.mkdir('./data/players/%s' % pm)
            if not os.path.exists('./data/players/%s/regularGames' % pm):
                os.mkdir('./data/players/%s/regularGames'% pm)
            df = pd.DataFrame(seasonAVE, columns=items)
            writeToPickle('./data/players/%s/regularGames/seasonAVE.pickle' % pm, df)
            
            df = pd.DataFrame(singleGAMES, columns=regular_items_en.keys())
            df[df == ''] = np.nan
            for col in df.columns:
                df[col] = df[col].astype('category')
            writeToPickle('./data/players/%s/regularGames/regularGameBasicStat.pickle' % pm, df)
        else:
            print('球员未参加过NBA常规赛')    
    #%%
    # -----季后赛----- 
    if last_season > 2018:
        seasonAVE = []
        singleGAMES = []
        links = playerPage.find_all('div', class_='section_content')[-1].find_all('ul')[0].find_all('li')
        if links[-1].a.string == 'Career Playoffs':
            playoffURL = 'https://www.basketball-reference.com' + links[-1].a.attrs['href']
            print('playoff')
        else:
            print('球员未参加过NBA季后赛')
            continue
        playoffPage = getCode(playoffURL, 'UTF-8')
        if not playoffPage.find('table', class_='stats_table'):
            continue
        trs = playoffPage.find('table', class_='stats_table').find_all('tr')
        # ----逐场扫描----
        for tr in trs[1:]:
            tds = tr.find_all('td')
            if len(tds) > 0 and tds[1].a:
                gm = tds[1].a.attrs['href'].lstrip('/boxscores/').rstrip('.html')
                # if gm > last_game:
                if len(tds) > 10:
                    gameStat = [x.get_text().strip() for x in tds]
                    if gameStat[0] and 'aba' not in tds[2].a.attrs['href']:    # 排除ABA比赛记录
                        gameStat[1] = gm
                        singleGAMES.append(gameStat)
                elif len(tds) > 1:    # 缺席比赛行（inactivate）
                    gameStat = [x.get_text().strip() for x in tds]
                    gameStat[1] = gm
                    gameStat += [''] * (30 - len(gameStat))
                    singleGAMES.append(gameStat)
        # ----赛季场均----
        text = str(playerPage)
        try:
            ppg = text.index('<div class="overthrow table_container" id="div_playoffs_per_game">')
        except:
            continue
        text = text[ppg:]
        seasons = BeautifulSoup(text).find('table', class_='stats_table').find_all('tr')
        items = [x.text for x in seasons[0].find_all('th')]
        for ind, season in enumerate(seasons[1:]):
            if season.find_all('th'):
                th = season.find_all('th')[0]
            else:
                continue
            tds = season.find_all('td')
            if th.text != 'Career':
                if tds[2].text != 'NBA':    # 只记录NBA比赛
                    continue
                seasonSTR = th.text[:4]
                seasonSTR += '-' + str(int(seasonSTR) + 1)
                if season.find_all('th')[0].find('span', class_='sr_star'):
                    seasonSTR += ' *'
                seasonAVE.append([seasonSTR] + [x.text for x in tds])
            else:
                break
        # ----生涯及分队场均----
        for ss in seasons[ind+1:]:
            th = ss.find_all('th')[0].text
            tds = ss.find_all('td')
            if (th or tds[2].text == 'NBA') and\
               not (th == 'Career' and tds[2].text == 'TOT') and\
               tds[2].text == 'NBA':
                if not th:
                    th = 'Career'
                seasonAVE.append([th] + [x.text for x in tds])
        
        # 写入csv文件
        if seasonAVE:
            if not os.path.exists('./data/players/%s' % pm):
                os.mkdir('./data/players/%s' % pm)
            if not os.path.exists('./data/players/%s/playoffGames' % pm):
                os.mkdir('./data/players/%s/playoffGames'% pm)
            df = pd.DataFrame(seasonAVE, columns=items)
            writeToPickle('./data/players/%s/playoffGames/seasonAVE.pickle' % pm, df)
            df = pd.DataFrame(singleGAMES, columns=playoff_items_en.keys())
            df[df == ''] = np.nan
            for col in df.columns:
                df[col] = df[col].astype('category')
            writeToPickle('./data/players/%s/playoffGames/playoffGameBasicStat.pickle' % pm, df)
        else:
            print('球员未参加过NBA季后赛')

# =============================================================================
#     if i[2] and i[3]:
#         links = playerPage.find_all('div', class_='section_content')[-1].find_all('ul')[0].find_all('li')
#         
#         # 常规赛所有单场比赛
#         print('starting to scan: ' + playerEnglishName + '\'s regular seasons')
#         listData = scan_player_regularSeason(links)
#         if listData:
#             save_gameBasicStat(playerMark, regularOrPlayoffs[0], listData)
#         else:
#             print('该球员无详细比赛页面')
#         
#     if i[4] and i[5]:
#         # 季后赛所有单场比赛
#         print('tstarting to scan: ' + playerEnglishName + '\'s playoff seasons', end='')
#         listData, seasonNumber = scan_player_playoffSeason(links)
#         # 判断是否有ABA季后赛经历
#         if listData:
#             for link in links:
#                 if 'ABA' in link.a.string:
#                     for ind, ss in enumerate(seasonNumber):
#                         if int(ss.split(' ')[0]) > 1976:
#                             break
#                     listData = [listData[0]] + listData[ind+1:]
#                     print('前%d个赛季为ABA赛季季后赛' % (ind))
#                     break
#         # print(playoffTable)
#         if len(listData) > 0:
#             save_gameBasicStat(playerMark, regularOrPlayoffs[1], listData)
#         print('%s\tScanned' % playerEnglishName, end='\n\n')
#         
#     else:
#         print('\n球员未参加过季后赛')
# =============================================================================

