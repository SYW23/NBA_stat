import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import pickle
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import matplotlib.image as mpimg
import matplotlib.animation as animation
from PIL import Image
from operator import itemgetter


def plus_minus(r, s, RoH):
    '''
    :param r: 当前时间点
    :param s: 回溯时间点
    :param RoH: 主客场视角
    :return:
    '''
    return (r['S'][RoH] - s[RoH]) - (r['S'][RoH - 1] - s[RoH - 1])


def writeToExcel(file, colNames, content):
    output = open(file,'w',encoding='utf-8')
    if colNames:
        output.write(colNames)
    for i in range(len(content)):
        for j in range(len(content[i])):
            output.write(str(content[i][j]))
            output.write('\t')
        output.write('\n')
    output.close()


def yieldGames(gs):
    for i in range(gs.shape[0]):
        yield gs.iloc[i].values


def gameMarkToSeason(gm):
    season = gm[:4]
    month = gm[4:6]
    if int(month) > 9:
        ss = '%s_%s' % (season, str(int(season) + 1))
    else:
        ss = '%s_%s' % (str(int(season) - 1), season)
    if int(month) == 10 and ss == '2020_2021':
        ss = '2019_2020'
    return ss


# 由nba版gm推出bbr版gm
def gameMark_nba2bbr(gm, ss):
    ht = gm[-7:-4].upper()
    if ht == 'PHX':
        ht = 'PHO'
    elif ht == 'CHA' and (ss < '2004_2005' or ss > '2013_2014'):
        ht = 'CHO'
    elif ht == 'BKN':
        ht = 'BRK'
    elif ht == 'WAS' and ss < '1997_1998':
        ht = 'WSB'
    return gm[:4] + gm[5:7] + gm[8:10] + '0' + ht


# 由gameMark推导出比赛文件目录
def gameMarkToDir(gm, regularOrPlayoff, tp=0):
    '''
    :param gameMark: gm
    :param regularOrPlayoff: 'regular' or 'playoff(s)'
    :param tp: 0->game  1->shot  2->boxscore  3->scanned
    :return:
    '''
    if 'pickle' in gm:
        gm = gm[:-7]
    ss = gameMarkToSeason(gm)
    if tp == 1:
        gameDir = 'D:/sunyiwu/stat/data/seasons_shot/%s/%s/' % (ss, regularOrPlayoff) + gm + '_shot.pickle'
    elif tp == 2:
        gameDir = 'D:/sunyiwu/stat/data/seasons_boxscores/%s/%s/' % (ss, regularOrPlayoff) + gm + '_boxscores.pickle'
    elif tp == 3:
        gameDir = 'D:/sunyiwu/stat/data/seasons_scanned/%s/%s/' % (ss, regularOrPlayoff) + gm + '_scanned.pickle'
    else:
        gameDir = 'D:/sunyiwu/stat/data/seasons/%s/%s/' % (ss, regularOrPlayoff) + gm + '.pickle'
    return gameDir


def read_nba_pbp(file):
    # print('读取文件', file)
    game = ''.join(LoadText(file))
    if game and '[{"actionNumber"' in game:
        tmp = game[game.index('[{"actionNumber"'):game.index(',"source"')]
        tmp = tmp.replace('null', 'None', 3000)
        actionList = eval(tmp)
    else:
        actionList = None
    tmp = game[game.index('{"gameId":'):game.index(',"playByPlay":{')]
    tmp = tmp.replace('null', 'None', 100)
    gameInf = eval(tmp)
    # return sorted(actionList, key=itemgetter("actionNumber")), gameInf
    # return actionList, gameInf
    return actionList, gameInf


def playerMarkToDir(pm, regularOrPlayoff, tp=0):
    '''
    :param pm: pm
    :param regularOrPlayoff: 'regular' or 'playoff(s)'
    :param tp: 0->games  1->career
    :return:
    '''
    if os.path.exists('D:/sunyiwu/stat/data/players/%s/%sGames' % (pm, regularOrPlayoff)):
        if tp == 1:
            plyrDir = 'D:/sunyiwu/stat/data/players/%s/%sGames/%sSaCAaS.pickle' % (pm, regularOrPlayoff, regularOrPlayoff)
        else:
            plyrDir = 'D:/sunyiwu/stat/data/players/%s/%sGames/%sGameBasicStat.pickle' % (pm, regularOrPlayoff, regularOrPlayoff)
        return plyrDir
    else:
        return ''


# 计算当前比赛时间（精确到.1秒）
def nowTime(index, playTime):
    if index <= 3:    # 常规时间
        time = minusMinutes('%d:00.0' % ((index + 1) * 12), playTime)
    else:    # 加时赛
        time = minusMinutes('%d:00.0' % (48 + (index - 3) * 5), playTime)
    minute, second, miniSec = [int(x) for x in [time[:-5], time[-4:-2], time[-1]]]
    now = 60 * minute + second + 0.1 * miniSec
    return now


# 比较时间早晚（倒计时形态下判断A是否晚于B，A晚即数值更小时，返回True）
def notEarlierThan(A, B):
    Am, As, Ams = [int(x) for x in [A[:-5], A[-4:-2], A[-1]]]
    Bm, Bs, Bms = [int(x) for x in [B[:-5], B[-4:-2], B[-1]]]
    if Am > Bm:
        return False
    else:
        if Am == Bm:
            if As > Bs:
                return False
            else:
                if As == Bs:
                    if Ams > Bms:
                        return False
                    else:
                        return True
                else:
                    return True
        else:
            return True


# 列表加法
def addList(A, B):
    assert len(A) == len(B)
    for index, i in enumerate(A):
        B[index] += i
    return B


# 时间加法
def addMinutes(a, b):
    a = [int(x) for x in [a[:-5], a[-4:-2], a[-1]]]
    b = [int(x) for x in [b[:-5], b[-4:-2], b[-1]]]
    c = a[1] + b[1]
    d = a[2] + b[2]
    if d >= 10:
        c += 1
        d -= 10
    if c >= 60:
        a[0] += 1
        c -= 60
    return '%d:%02d.%d' % ((a[0] + b[0]), c, d)


# 时间减法
def minusMinutes(a, b):
    a = [int(x) for x in [a[:-5], a[-4:-2], a[-1]]]
    b = [int(x) for x in [b[:-5], b[-4:-2], b[-1]]]
    if a[0] - b[0] >= 0:
        if a[2] < b[2]:
            a[1] -= 1
            d = a[2] + 10 - b[2]
        else:
            d = a[2] - b[2]
        if a[1] < b[1]:
            a[0] -= 1
            c = a[1] + 60 - b[1]
        else:
            c = a[1] - b[1]
        return '%d:%02d.%d' % ((a[0] - b[0]), c, d)
    else:
        return ''


# print(addMinutes('4:52.2', '1:09.9'))
# print(minusMinutes('4:52.2', '3:52.9'))


# 保存pickle数据文件
def writeToPickle(fileName, content):
    '''
    :param fileName: 文件名
    :param content: 要写入的内容
    :return:
    '''
    f = open(fileName, 'wb')
    pickle.dump(content, f)
    f.close()


# 读取pickle数据文件
def LoadPickle(fileName):
    f = open(fileName, 'rb')
    content = pickle.load(f)
    f.close()
    return content


def LoadText(fileName):
    if os.path.exists(fileName):
        f = open(fileName, 'r', encoding='utf-8')
        content = f.readlines()
        f.close()
        return content
    else:
        print('文件不存在', fileName)


# 获取网页源代码
def getCode(url, encoding):
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
    response = requests.get(url, headers=headers)
    response.encoding = encoding
    return BeautifulSoup(response.text, 'html.parser')


# 创建球员个人文件夹并保存比赛基础数据
def save_gameBasicStat(playerMark, regularOrPlayoff, table):
    if not os.path.exists('./data/players/' + playerMark):
        os.mkdir('./data/players/' + playerMark)
    if not os.path.exists('./data/players/' + playerMark + '/%sGames' % regularOrPlayoff):
        os.mkdir('./data/players/' + playerMark + '/%sGames'% regularOrPlayoff)
    writeToPickle('./data/players/%s/%sGames/%sGameBasicStat.pickle' % (playerMark, regularOrPlayoff, regularOrPlayoff), table)


# 计算本条play记录中球员的得分和分差以及当前时间
def score_diff_time(play, game, max_diff):
    s = play.score()
    leader, d = play.leaderAndDiff()
    if d != 0 and leader != game.HOA:
            d = -d
    if d > max_diff:
        d = max_diff
    elif d < -max_diff:
        d = -max_diff
    t = play.nowtime()
    return s, d, t


# 处理边界时间（x.0s归在x-1秒内）
def tailTime(t, inter_s):
    if str(t)[-3:] == '0.0':
        t = int(t // inter_s) - 1
    else:
        t = int(t // inter_s)
    return t


# 分差按一定间隔分组
def groupDiff(d, max_diff, diff_inter):
    if d <= max_diff:
        return d // 5
    else:
        return math.ceil(d / 5)


# 获取球员常规赛数据
def scan_player_regularSeason(linkss):
    links = []
    listData = []
    
    for link in linkss:
        if link.a.string != 'Career Playoffs' and 'ABA' not in link.a.string:
            # 去除季后赛和ABA链接
            links.append(link)

    for i in tqdm(links):
        url= 'https://www.basketball-reference.com' + i.a.attrs['href']
        print(url)
        soupSeason = getCode(url, 'UTF-8')
        listDataTmp = []
        gameMarkListTmp = []
            
        title = soupSeason.find('div', class_='section_heading').find_all('span')
        if 'Playoffs' in title[0].attrs['data-label']:
            continue
        # .find定位到表格位置;.find_all查找所有的tr（表格行）
        trs = soupSeason.find('table', class_='stats_table').find_all('tr')
        # 表头
        colName = [x.get_text().strip() for x in trs[0].find_all('th')][1:]
        colNumber = len(colName)
        listDataTmp += [colName]
        # 遍历行
        for tr in trs:
            tds = tr.find_all('td')
            # 排除重复表头行（20场重复一次）以及缺席比赛行（inactivate）
            if len(tds) > 10:
                assert len(tds) == colNumber
                gameStat = [x.get_text().strip() for x in tds]
                # 将Date列置为比赛标志符
                gameStat[1] = tds[1].a.attrs['href'].lstrip('/boxscores/').rstrip('.html')
                
                listDataTmp += [gameStat]
        listData += [listDataTmp]
    return listData


# 获取球员季后赛数据
def scan_player_playoffSeason(links):
    listData = []
    if links[-1].a.string == 'Career Playoffs':
        links = links[-1]
    else:
        print('\n球员未参加过季后赛')
        return []
    url= 'https://www.basketball-reference.com' + links.a.attrs['href']
    soupSeason = getCode(url, 'UTF-8')
    
    seasonNumber = []
    trs = soupSeason.find('table', class_='stats_table').find_all('tr')
    colName = [x.get_text().strip() for x in trs[0].find_all('th')][1:]
    seasonNumber.append(colName[1])
    colName[1] = 'Playoffs'
    colNumber = len(colName)
    listData += [colName]
    
    ptr, series, seriesAppearance = 1, 0, 0    # 赛季数、系列赛数、系列赛出场次数
    listData.append([])
    listData[ptr].append([])
    
    for tr in trs[1:]:
        tds = tr.find_all('td')
        # 遇重复表头行赛季数+1；遇空行系列赛数+1
        if len(tds) > 10:
            assert len(tds) == colNumber
            gameStat = [x.get_text().strip() for x in tds]
            if gameStat == [''] * colNumber:
                # 新系列赛分割行
                if seriesAppearance == 0:
                    pass
                else:
                    seriesAppearance = 0
                    if series == 0:
                        # 新赛季首个系列赛
                        print('\n赛季%d\t系列赛%d' % (ptr, series+1), end='')
                    else:
                        # 赛季新一轮系列赛
                        print('\t系列赛%d' % (series+1), end='')
                    series += 1
                    listData[ptr].append([])
            else:
                gameStat[1] = tds[1].a.attrs['href'].lstrip('/boxscores/').rstrip('.html')
                listData[ptr][series].append(gameStat)
                seriesAppearance += 1
        elif len(tds) == 0:
            # 新赛季分割行
            seasonNumber.append(tr.find_all('th')[2].get_text().strip())
            if seriesAppearance == 0:
                listData[ptr].pop()
            else:
                seriesAppearance = 0
                if series != 0:
                    # 上赛季最后一轮系列赛
                    print('\t系列赛%d' % (series+1), end='')
                else:
                    # 上赛季只有一轮系列赛
                    print('\n赛季%d\t系列赛%d' % (ptr, series+1), end='')
            ptr += 1
            series = 0
            listData.append([])
            listData[ptr].append([])
        else:
            print('\n存在 inactivate or did-not-play', end='')
            continue
    if seriesAppearance == 0:
        listData[ptr].pop()
        if series == 0:
           listData.pop()
           print('\n', end='')
    else:
        seriesAppearance = 0
        if series == 0:
            # 最后一个赛季只有一轮系列赛
            print('\n赛季%d\t系列赛%d' % (ptr, series+1))
        else:
            # 最后一个赛季最后一轮系列赛
            print('\t系列赛%d' % (series+1))
    return listData, seasonNumber


# 球员随比赛走势在不同分差下的得分分布图
def playerGameScoreDistribution(playerName, playerMark, HomeOrAts, colors, inter, ROP):
    playerFileDir = './data/players/' + playerMark + '/%sGames/%sGameBasicStat.pickle' % (ROP, ROP)
    f = open(playerFileDir, 'rb')
    playerGames = pickle.load(f)
    f.close()
    # 球员表现统计表 [落后得分, 平局得分，领先得分]
    downLeadTie = [[0, 0, 0], [0, 0, 0]]
    goalOrMiss = np.zeros((2, 3, 101, 4080//inter))
    # 绘制关键时刻范围
    circles = [[], [], []]
    critical_regions = []
    for i in range(3):
        critical_regions.append(plt.Rectangle(xy=(516, -5),
                                             width=300, height=10,
                                             edgecolor='#FFFF00',
                                             fill=True, facecolor='#FFD700',
                                             linewidth=1, alpha=0.2))
    for season in playerGames:
        for game in yieldGames(ROP, season):
            gameMark = game[1]
            team = game[3]
            # 读取比赛文件
            gameDir = gameMarkToDir(gameMark, ROP)
            f = open(gameDir, 'rb')
            playerGame = pickle.load(f)
            f.close()
            # 判断主客场
            HOA = 1 if team == gameMark[-3:] else 0    # 0客1主
            HomeOrAt = HomeOrAts[HOA-1]
            # 扫描比赛表现
            for index, quarter in enumerate(playerGame):
                if index == 6:
                    print('三加时', gameMark)
                elif index == 5:
                    print('双加时', gameMark)
                for play in quarter:
                    if len(play) == 6:
                        if play[HomeOrAt[1]]:
                            playerPlayed = play[HomeOrAt[1]].split(' ')[0]
                            if playerPlayed == playerMark and (play[HomeOrAt[0]] or 'misses' in play[HomeOrAt[1]]):
                                # 此球员有得分/错失得分
                                # 计算时间
                                if play[0] == '0:00.0':
                                    play[0] = '0:00.1'
                                if index <= 3:
                                    # 常规时间
                                    time = minusMinutes('%d:00.0' % ((index + 1) * 12), play[0])
                                else:
                                    # 加时赛
                                    time = minusMinutes('%d:00.0' % (48 + (index - 3) * 5), play[0])
                                minute, second, miniSec = [int(x) for x in [time[:-5], time[-4:-2], time[-1]]]
                                score = 0
                                if play[HomeOrAt[0]]:
                                    # 球员得分
                                    DLT = 0
                                    score = int(play[HomeOrAt[0]])
                                    if score >= 4:
                                        if 'free throw' in play[HomeOrAt[1]]:
                                            score = 1
                                        elif '2-pt' in play[HomeOrAt[1]]:
                                            score = 2
                                        elif '3-pt' in play[HomeOrAt[1]]:
                                            score = 3
                                else:
                                    # 球员失手
                                    DLT = 1
                                    if 'free throw' in play[HomeOrAt[1]]:
                                        score = 1
                                    elif '2-pt' in play[HomeOrAt[1]]:
                                        score = 2
                                    elif '3-pt' in play[HomeOrAt[1]]:
                                        score = 3
                                    elif 'misses no shot' in play[HomeOrAt[1]]:
                                        continue
                                try:
                                    assert score in [1, 2, 3]
                                except:
                                    print(gameMark, play)
                                # 计算分差
                                scores = [int(x) for x in play[3].split('-')]
                                teamScore = scores[HOA] - score
                                opponentScore = scores[HOA-1]
                                diff = teamScore - opponentScore + 50
                                if diff > 100:
                                    diff = 100
                                elif diff < 0:
                                    diff = 0
                                # 生成数据点
                                circles[score-1].append(plt.Circle(((60*minute+second+0.1*miniSec)/5, teamScore-opponentScore), 0.3, color=colors[DLT][score-1], clip_on=False))
                                goalOrMiss[DLT][score-1][diff, int((60*minute+second+0.1*miniSec)//inter)] += 1
                                if (60*minute+second+0.1*miniSec)//inter == 58:
                                    print(gameMark)
                                if teamScore < opponentScore:
                                    downLeadTie[DLT][0] += score
                                elif teamScore > opponentScore:
                                    downLeadTie[DLT][2] += score
                                else:
                                    downLeadTie[DLT][1] += score
    
    # 画图
    if '1':
        fig, ax = plt.subplots(3, figsize=(60,27), sharex=True, sharey=True)
        xlabels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '第一节完',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '第二节完',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '第三节完',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '第四节完',
                   '1', '2', '3', '4', '加时1完', '1', '2', '3', '4', '加时2完',
                   '1', '2', '3', '4', '加时3完', '1', '2', '3', '4', '加时4完']
        ylabels = ['-50', '-40', '-30', '-20', '-10', '0', '10', '20', '30', '40', '50']
        for sub in range(3):
            ax[sub].add_patch(critical_regions[sub])
            ax[sub].set_xticks(np.arange(0, 828, 12))
            ax[sub].set_xticklabels(xlabels, fontsize=18)
            ax[sub].set_yticks(np.arange(-50, 60, 10))
            ax[sub].set_yticklabels(ylabels, fontsize=18)
            ax[sub].xaxis.grid(True, linestyle='--', color='#D3D3D3')
            ax[sub].yaxis.grid(True, linestyle='--', color='#D3D3D3')
            a = ax[sub].get_ygridlines()[5]
            a.set_linestyle('-')
            a.set_linewidth(2)
            a = ax[sub].get_xgridlines()
            b = [a[12], a[24], a[36], a[48], a[53], a[58], a[63]]
            for c in b:
                c.set_linestyle('-')
                c.set_linewidth(2)
            ax[sub].set_ylabel('分差', fontsize=30)
            axis = ['top', 'bottom', 'left', 'right']
            for axi in axis:
                ax[sub].spines[axi].set_visible(True)
                ax[sub].spines[axi].set_color('black')
            ax[sub].label_outer()
        
        for indexC, i in enumerate(circles):
            for cir in i:
                ax[indexC].add_artist(cir)
        ax[0].set_title('罚球', fontsize=30)
        ax[1].set_title('两分', fontsize=30)
        ax[2].set_title('三分', fontsize=30)
        ax[2].set_xlabel('比赛时长', fontsize=30)
        fig.subplots_adjust(hspace=0.08)
        fig.suptitle(playerName + '    总得分：%d' % sum(downLeadTie[0]), fontsize=36)
        plt.savefig('./%sResults/playerGameScoreDistribution/%s_%s.jpg' % (ROP, playerName, playerMark), dpi = 200)
        plt.close('all')
        
        # 饼图
        plt.figure(figsize=(12,9))
        #定义饼状图的标签，标签是列表
        labels = [u'落后时得分: %d' % downLeadTie[0][0],
                  u'平局时得分: %d' % downLeadTie[0][1],
                  u'领先时得分: %d' % downLeadTie[0][2]]
        #每个标签占多大，会自动去算百分比
        colors = ['red','lightskyblue','yellowgreen']
        #将某部分爆炸出来， 使用括号，将第一块分割出来，数值的大小是分割出来的与其他两块的间隙
        explode = (0.00,0.03,0.00)
        
        patches,l_text,p_text = plt.pie(downLeadTie[0], explode=explode, labels=labels,
                                        colors=colors, labeldistance=1.08, autopct='%3.2f%%',
                                        shadow=True, startangle=60, pctdistance=0.5)
        #改变文本的大小
        #方法是把每一个text遍历。调用set_size方法设置它的属性
        for t in l_text:
            t.set_size(16)
        for t in p_text:
            t.set_size(12)
        # 设置x，y轴刻度一致，这样饼图才能是圆的
        plt.axis('equal')
        plt.title(playerName + '    总得分：%d' % sum(downLeadTie[0]), fontsize=20)
        plt.legend(fontsize=16, loc='upper right')
        plt.savefig('./%sResults/playerDownLeadTie/%s_%s.jpg' % (ROP, playerName, playerMark), dpi = 200)
        plt.close('all')
    return goalOrMiss


# 关键时刻得分统计
def playerClutchScoreDistribution(playerName, playerMark, HomeOrAts, diffPlus, diffMinus, lastMins, ROP):
    playerFileDir = './data/players/' + playerMark + '/%sGames/%sGameBasicStat.pickle' % (ROP, ROP)
    f = open(playerFileDir, 'rb')
    playerGames = pickle.load(f)
    f.close()
    goalOrMiss = [[0, 0, 0], [0, 0, 0]]
    # print(playerGames)
    for game in yieldGames(playerGames):
        gameMark = game[1]
        if gameMark == '201606190CLE':
            continue
        team = game[3]
        # 读取比赛文件
        gameDir = gameMarkToDir(gameMark, ROP)
        f = open(gameDir, 'rb')
        playerGame = pickle.load(f)
        f.close()
        # 判断主客场
        HOA = 1 if team == gameMark[-3:] else 0    # 0客1主
        HomeOrAt = HomeOrAts[HOA-1]
        # 扫描比赛表现
        for index, quarter in enumerate(playerGame[3:]):
            for play in quarter:
                if len(play) == 6 and notEarlierThan(play[0], lastMins):
                    if play[HomeOrAt[1]]:
                        playerPlayed = play[HomeOrAt[1]].split(' ')[0]
                        if playerPlayed == playerMark and (play[HomeOrAt[0]] or 'misses' in play[HomeOrAt[1]]):
                            # 此球员有得分/错失得分
                            score = 0
                            if play[HomeOrAt[0]]:
                                # 球员得分
                                DLT = 1
                                score = int(play[HomeOrAt[0]])
                                if score >= 4:
                                    if 'free throw' in play[HomeOrAt[1]]:
                                        score = 1
                                    elif '2-pt' in play[HomeOrAt[1]]:
                                        score = 2
                                    elif '3-pt' in play[HomeOrAt[1]]:
                                        score = 3
                            else:
                                # 球员失手
                                DLT = 0
                                if 'free throw' in play[HomeOrAt[1]]:
                                    score = 1
                                elif '2-pt' in play[HomeOrAt[1]]:
                                    score = 2
                                elif '3-pt' in play[HomeOrAt[1]]:
                                    score = 3
                                elif 'misses no shot'in play[HomeOrAt[1]]:
                                    continue
                            try:
                                assert score in [1, 2, 3]
                            except:
                                print(gameMark, play)
                            if index > 2 and play[0] == '0:00.1' and 44 < diff < 56:
                                print(index, play, gameMark)
                            # 计算分差
                            scores = [int(x) for x in play[3].split('-')]
                            teamScore = scores[HOA] - DLT * score
                            opponentScore = scores[HOA-1]
                            diff = teamScore - opponentScore
                            if diffMinus <= diff <= diffPlus:
                                goalOrMiss[DLT-1][score-1] += 1
    
    attempts = goalOrMiss[0][1]+goalOrMiss[1][1]+goalOrMiss[0][2]+goalOrMiss[1][2]
    sumUp = goalOrMiss[0][0]+goalOrMiss[0][1]*2+goalOrMiss[0][2]*3
    fTPct = goalOrMiss[0][0]/(goalOrMiss[0][0]+goalOrMiss[1][0]) \
            if goalOrMiss[0][0]+goalOrMiss[1][0] > 0 else '/'
    twoPtPct = goalOrMiss[0][1]/(goalOrMiss[0][1]+goalOrMiss[1][1]) \
               if goalOrMiss[0][1]+goalOrMiss[1][1] > 0 else '/'
    threePtPct = goalOrMiss[0][2]/(goalOrMiss[0][2]+goalOrMiss[1][2]) \
                 if goalOrMiss[0][2]+goalOrMiss[1][2] > 0 else '/'
    fGPct = (goalOrMiss[0][1]+goalOrMiss[0][2])/attempts if attempts > 0 else '/'
    eFG = (goalOrMiss[0][1]+1.5*goalOrMiss[0][2])/attempts if attempts > 0 else '/'
    tS = sumUp/(2*(attempts+0.44*(goalOrMiss[0][0]+goalOrMiss[1][0]))) \
         if attempts+0.44*(goalOrMiss[0][0]+goalOrMiss[1][0]) > 0 else '/'
    res = [sumUp, playerName,
           fTPct, goalOrMiss[0][0], goalOrMiss[0][0]+goalOrMiss[1][0],
           twoPtPct, goalOrMiss[0][1], goalOrMiss[0][1]+goalOrMiss[1][1],
           threePtPct, goalOrMiss[0][2], goalOrMiss[0][2]+goalOrMiss[1][2],
           fGPct, goalOrMiss[0][1]+goalOrMiss[0][2], attempts,
           eFG, tS]
    return res


# 更新比赛中单项技术统计，用于playerPerformanceWithTime函数
def uploadStat(start, pP, gameStat, now, stat, index, accum=True):
    for ti in range(start[index], int(now)):
        pP[index][-1][ti] = gameStat[index]
    if accum:
        gameStat[index] += stat
    else:    # 分差不累计
        gameStat[index] = stat
    pP[index][-1][int(now)] = gameStat[index]
    start[index] = int(now + 1)


# 计算节初/末时间点，flag为True计算节初
def quarterStartOrEnd(index, flag=True, gameEnd=False):
    x = 0 if flag else 1
    if index < 4:
        quarter_ = (index + x) * 12 * 60 if not gameEnd else 2880
    else:
        quarter_ = 4 * 12 * 60 + (index + x - 4) * 5 * 60 if not gameEnd else 2880 + (index + x - 4) * 5 * 60
    return quarter_


# 更新比赛时间统计，用于playerPerformanceWithTime函数
def stopWatch(start, end, pP, gameStat):
    for ti in range(start[11], end):
        if ti < 4080:
            pP[11][-1][ti] = gameStat[11]
    start[11] = end - 1


# zero为True时考虑比赛开始的特殊情况
def runWatch(duration, gameStat, start, pP, zero=False):
    if not zero:
        start[11] += 1
    gameStat[11] += duration
    gameStat[11] = float('%.1f' % gameStat[11])
    if zero:
        pP[11][-1][0] = 0
        start[11] += 1
    while duration >= 1:
        pP[11][-1][start[11]] = pP[11][-1][start[11]-1] + 1
        start[11] += 1
        duration -= 1
    if duration > 0:    # 若duration有小数点残留，结算到下一秒上
        duration = float('%.1f' % duration)
        pP[11][-1][start[11]] += (pP[11][-1][start[11]-1] + duration)
        pP[11][-1][start[11]] = float('%.1f' % pP[11][-1][start[11]])
        start[11] += 1
    start[11] -= 1


# 扫描整节中球员是否有上场表现，用于playerPerformanceWithTime函数
def quarterPlayScanning(ss, ee, playerGame, playerMark):
    res = []
    for q in range(ss , ee):
        ques = 0
        for play_ in playerGame[q]:
            if len(play_) == 6 and (playerMark in play_[1] or playerMark in play_[5]):
                ques = 1
                break
        res.append([q, ques])
    return res


# 逐节扫描
def updateQuarters(ss, ee, playerGame, playerMark, gameStat, start, pP, startUp):
    OOF = -1
    for [q, ques] in quarterPlayScanning(ss+1, ee, playerGame, playerMark):
        OOF = ques
        if ques == 1:
            if q == 0:
                startUp += 1
            runWatch(720 if q < 4 else 300, gameStat, start, pP)
        else:
            stopWatch(start, start[11]+721, pP, gameStat)
    return OOF, startUp


# 计算分差
def diffNow(score, HOA):
    scores = [int(x) for x in score.split('-')]
    teamScore = scores[HOA]
    opponentScore = scores[HOA-1]
    return teamScore - opponentScore


# 统计得分方式，用于playerPerformanceWithTime函数
def scoreMethods(scoreMethod, playDisc, flag_GOMOA, flag_3=False):
    if flag_3:
        scoreMethod[flag_GOMOA][-1] += 1
        return
    if 'jump shot' in playDisc:
        scoreMethod[flag_GOMOA][0] += 1
    elif 'layup' in playDisc:
        scoreMethod[flag_GOMOA][1] += 1
    elif 'dunk' in playDisc:
        scoreMethod[flag_GOMOA][2] += 1
    elif 'hook shot' in playDisc:
        scoreMethod[flag_GOMOA][3] += 1
    elif 'tip-in' in playDisc:
        scoreMethod[flag_GOMOA][4] += 1
    else:
        scoreMethod[flag_GOMOA][5] += 1
        # print(playDisc)
    return


# 球员随比赛走势的得分等数据的（累积）趋势图
def playerPerformanceWithTime(playerName, playerMark, HomeOrAts, colors, ROP):
    playerFileDir = './data/players/' + playerMark + '/%sGames/%sGameBasicStat.pickle' % (ROP, ROP)
    f = open(playerFileDir, 'rb')
    playerGames = pickle.load(f)
    f.close()
    numStat = 12
    inter = 15
    # 球员表现统计表
    foulMethods = []    # 犯规种类
    scoreMethod = [[0, 0, 0, 0, 0, 0, 0],    # 0投进/1投失/2助攻得分
                   [0, 0, 0, 0, 0, 0, 0],    # 0jump shot 1layup 2dunk 3hook shot 4tip-in 5unknown 63pt
                   [0, 0, 0, 0, 0, 0, 0]]
    goalOrMiss = [[], []]    # 0投进/1投失
    for i in range(2):    # 0罚球、1两分、2三分
        for j in range(3):
            goalOrMiss[i].append([0] * (4080//inter))
    pP = []    # playerPerformance 0分差、1得分、2前板、3后板、4总板、5助攻、6助攻得分、7抢断、8盖帽、9失误、10犯规、11时间
    for i in range(numStat):
        pP.append([])
    startUp = 0    # 首发次数
    flag = 0
    for season in playerGames:
        for game in yieldGames(ROP, season):
            statSingleGame = [0] * numStat    # 单场比赛统计
            gameStat = [0] * numStat    # 单项实时统计
            start = [0] * numStat    # 单项统计实时更新时间
            for i in range(numStat):
                pP[i].append([0] * 4080)
            gameMark, team = game[1], game[3]
            # 读取比赛文件
            gameDir = gameMarkToDir(gameMark, ROP)
            f = open(gameDir, 'rb')
            playerGame = pickle.load(f)
            f.close()
            # 判断主客场
            HOA = 1 if team == gameMark[-3:] else 0    # 0客1主
            oppoHOA = 0 if HOA else 1
            oppoHomeOrAt = HomeOrAts[oppoHOA-1]
            HomeOrAt = HomeOrAts[HOA-1]
            onOrOff = -1    # 每场比赛开场，球员上场状态未知
            lastOnCourt = -1
            foulTime = []
            # 扫描比赛表现，index为节数-1
            for index, quarter in enumerate(playerGame):
                for indexPlay, play in enumerate(quarter):
                    if len(play) == 6:
                        # 计算当前时间
                        if play[0] == '0:00.0':
                            play[0] = '0:00.1'
                        now = nowTime(index, play[0])
                        playDisc = play[HomeOrAt[1]]
                        oppoPlayDisc = play[oppoHomeOrAt[1]]
                        if playDisc:    # 球队有动作
                            playerPlayed = playDisc.split(' ')[0]
                            if play[HomeOrAt[0]]:    # 球队有得分
                                playScore = 0
                                if play[HomeOrAt[0]]:
                                    if 'free throw' in playDisc:
                                        playScore = 1
                                    elif '2-pt' in playDisc:
                                        playScore = 2
                                    elif '3-pt' in playDisc:
                                        playScore = 3
                                if playerPlayed == playerMark:    # 此球员有得分
                                    try:
                                        assert playScore in [1, 2, 3]
                                    except:
                                        print(playScore, gameMark, play)
                                    if playScore == 2:
                                        scoreMethods(scoreMethod, playDisc, 0)
                                    elif playScore == 3:
                                        scoreMethods(scoreMethod, playDisc, 0, flag_3=True)
                                    uploadStat(start, pP, gameStat, now, playScore, 1)
                                    goalOrMiss[0][playScore-1][int(now)//inter] += 1
                                    # print(playScore, play)
                                elif 'assist by' in playDisc and playerMark in playDisc:    # 此球员有助攻
                                    uploadStat(start, pP, gameStat, now, 1, 5)
                                    try:
                                        assert playScore in [2, 3]
                                    except:
                                        print(playScore, gameMark, play)
                                    if playScore == 2:
                                        scoreMethods(scoreMethod, playDisc, 2)
                                    else:
                                        scoreMethods(scoreMethod, playDisc, 2, flag_3=True)
                                    uploadStat(start, pP, gameStat, now, playScore, 6)
                            elif 'rebound' in playDisc:    # 球队有篮板
                                if 'by %s' % playerMark in playDisc:    # 此球员有篮板
                                    if 'Offensive' in playDisc:
                                        uploadStat(start, pP, gameStat, now, 1, 2)
                                    elif 'Defensive' in playDisc:
                                        uploadStat(start, pP, gameStat, now, 1, 3)
                                    uploadStat(start, pP, gameStat, now, 1, 4)
                            elif playerPlayed == playerMark and 'misses' in playDisc:    # 球员失手
                                if 'free throw' in playDisc:
                                    missScore = 1
                                elif '2-pt' in playDisc:
                                    missScore = 2
                                    scoreMethods(scoreMethod, playDisc, 1)
                                elif '3-pt' in playDisc:
                                    missScore = 3
                                    scoreMethods(scoreMethod, playDisc, 1, flag_3=True)
                                elif 'misses no shot'in playDisc:
                                    continue
                                try:
                                    assert missScore in [1, 2, 3]
                                except:
                                    print(missScore, gameMark, play)
                                goalOrMiss[1][missScore-1][int(now)//inter] += 1
                            elif 'Turnover by %s' % playerMark in playDisc:    # 球员失误
                                uploadStat(start, pP, gameStat, now, 1, 9)
                                if 'offensive foul'  in playDisc:    # 球员进攻犯规
                                    nowTmp = nowTime(index, play[0])
                                    if (nowTmp + 1) != start[10] and \
                                       'Offensive foul' not in quarter[indexPlay-1][1] and \
                                       'Offensive foul' not in quarter[indexPlay-1][-1] and \
                                       'Offensive foul' not in quarter[indexPlay+1][1] and \
                                       'Offensive foul' not in quarter[indexPlay+1][-1] and \
                                       'Offensive charge foul' not in quarter[indexPlay-1][1] and \
                                       'Offensive charge foul' not in quarter[indexPlay-1][-1] and \
                                       'Offensive charge foul' not in quarter[indexPlay+1][1] and \
                                       'Offensive charge foul' not in quarter[indexPlay+1][-1]:
                                        if [index, play[0]] not in foulTime:
                                            if flag:
                                                print(play)
                                            uploadStat(start, pP, gameStat, now, 1, 10)
                                            foulTime.append([index, play[0]])
                            elif ('foul by' in playDisc or 'Flagrant foul' in playDisc) and \
                                 playerMark in playDisc and \
                                 'drawn by %s' % playerMark not in playDisc:    # 犯规（包括违体犯规）
                                if 'Hanging tech' not in playDisc and \
                                   'technical' not in playDisc and \
                                   'Technical' not in playDisc and \
                                   '3 sec' not in playDisc and  \
                                   'Ill def tech foul' not in playDisc and  \
                                   'Def 3 sec tech' not in playDisc:    # 排除技术犯规和防守三秒
                                    # 球员进攻或者防守犯规
                                    if [index, play[0]] not in foulTime:
                                        if flag:
                                            print(play)
                                        uploadStat(start, pP, gameStat, now, 1, 10)
                                        foulTime.append([index, play[0]])
                                    if 'Offensive foul' in playDisc:
                                        if 'Teamfoul by %s' % playerMark in quarter[indexPlay+1][1] or\
                                           'Teamfoul by %s' % playerMark in quarter[indexPlay+1][-1]:
                                               uploadStat(start, pP, gameStat, now, 1, 9)
                                if playerPlayed not in foulMethods:    # 统计犯规种类
                                    foulMethods.append(playerPlayed)
                            elif 'enters' in playDisc and playerMark in playDisc:    # 球员发生换人
                                if playerPlayed == playerMark:    # 球员替换上场
                                    lastOnCourt_, lastOnCourt = lastOnCourt, index
                                    if onOrOff == -1:    # 特殊：比赛开始到上一节末情况未知
                                        _, startUp = updateQuarters(-1, index, playerGame, playerMark, gameStat, start, pP, startUp)
                                    else:
                                        # 首先将最后有统计的一节延伸至节末
                                        if index - lastOnCourt_ > 0:    # 特殊：间隔节
                                            quarterEnd = quarterStartOrEnd(lastOnCourt_, flag=False)
                                            if onOrOff == 0:
                                                stopWatch(start, quarterEnd+1, pP, gameStat)
                                            else:
                                                runWatch(quarterEnd-start[11], gameStat, start, pP)
                                            updateQuarters(lastOnCourt_, index, playerGame, playerMark, gameStat, start, pP, startUp)
                                    stopWatch(start, int(now//1+1), pP, gameStat)
                                    if now % 1:    # 最后处理一下now中的小数点
                                        gameStat[11] += (1 - float('0.%s' % str(now).split('.')[1]))
                                        pP[11][-1][start[11]+1] = gameStat[11]
                                        start[11] += 1
                                    onOrOff = 1    # 统计完成，状态置为上场
                                else:    # 球员被换下
                                    lastOnCourt_, lastOnCourt = lastOnCourt, index
                                    if onOrOff == -1:    # 特殊：从比赛开始到当前情况未知
                                        if index != 0:
                                            _, startUp = updateQuarters(-1, index, playerGame, playerMark, gameStat, start, pP, startUp)
                                        else:    # 特殊：球员首发
                                            startUp += 1
                                    elif onOrOff == 0:    # 特殊：跨节间，上？节情况未知
                                        quarterStart = quarterStartOrEnd(lastOnCourt_+1)
                                        stopWatch(start, quarterStart+1, pP, gameStat)
                                        if index - lastOnCourt_ + 2 >= 1:    # 特殊：间隔？节情况未知
                                            updateQuarters(lastOnCourt_, index, playerGame, playerMark, gameStat, start, pP, startUp)
                                    else:    # 正常
                                        if index - lastOnCourt_ > 1:    # 特殊：间隔？节情况未知
                                            runWatch(quarterStartOrEnd(lastOnCourt_, flag=False)-start[11], gameStat, start, pP)
                                            updateQuarters(lastOnCourt_, index, playerGame, playerMark, gameStat, start, pP, startUp)
                                    runWatch(now-start[11], gameStat, start, pP, zero=(index==0))
                                    onOrOff = 0    # 统计完成，状态置为下场
                        elif oppoPlayDisc:    # 对手有动作
                            oppoPlayerPlayed = oppoPlayDisc.split(' ')[0]
                            if 'steal by %s' % playerMark in oppoPlayDisc:    # 球员抢断
                                uploadStat(start, pP, gameStat, now, 1, 7)
                            elif 'block by %s' % playerMark in oppoPlayDisc:    # 球员盖帽
                                uploadStat(start, pP, gameStat, now, 1, 8)
                            elif ('foul by' in oppoPlayDisc or 'Flagrant foul' in oppoPlayDisc) and \
                                 playerMark in oppoPlayDisc and \
                                 'drawn by %s' % playerMark not in oppoPlayDisc:    # 犯规（包括违体犯规）
                                if 'Hanging tech' not in oppoPlayDisc and \
                                   'technical' not in oppoPlayDisc and \
                                   'Technical' not in oppoPlayDisc and \
                                   '3 sec' not in oppoPlayDisc and \
                                   'Ill def tech foul' not in oppoPlayDisc and  \
                                   'Def 3 sec tech' not in oppoPlayDisc:    # 排除技术犯规和防守三秒
                                    # 球员进攻或者防守犯规
                                    if [index, play[0]] not in foulTime:
                                        if flag:
                                            print(play)
                                        uploadStat(start, pP, gameStat, now, 1, 10)
                                        foulTime.append([index, play[0]])
                                if oppoPlayerPlayed not in foulMethods:    # 统计犯规种类
                                    foulMethods.append(oppoPlayerPlayed)
                        # 计算分差
                        uploadStat(start, pP, gameStat, now, diffNow(play[3], HOA), 0, False)
            if lastOnCourt != len(playerGame) - 1 and lastOnCourt != -1:    # 比赛存在最后几节轮换不明
                # 首先统计本节至结束
                quarterEnd = quarterStartOrEnd(lastOnCourt, flag=False)
                if onOrOff == 0:
                    stopWatch(start, quarterEnd+1, pP, gameStat)
                else:
                    runWatch(quarterEnd-start[11], gameStat, start, pP)
                # 依次扫描余下的节次，判断球员是否上场
                onOrOff, _ = updateQuarters(lastOnCourt, len(playerGame), playerGame, playerMark, gameStat, start, pP, startUp)
            elif lastOnCourt == -1:    # 全场比赛无此球员轮换统计，即：打满全场
                _, startUp = updateQuarters(-1, len(playerGame), playerGame, playerMark, gameStat, start, pP, startUp)
            # 继续统计上场时间直到比赛结束
            if onOrOff == 1:
                runWatch(quarterStartOrEnd(index, flag=False, gameEnd=True)-start[11], gameStat, start, pP)
            stopWatch(start, len(pP[11][-1]), pP, gameStat)
            for i in range(1, 4080):
                if pP[11][-1][i] - pP[11][-1][i-1] > 1.01 or pP[11][-1][i] - pP[11][-1][i-1] < 0:
                    print(gameMark, i, pP[11][-1][i-1], pP[11][-1][i], pP[11][-1])
                    return
            
            # 维持分差与得分等数据直到比赛结束
            for i in range(numStat):
                statSingleGame[i] = gameStat[i]
                for ti in range(start[i], 4080):
                    pP[i][-1][ti] = gameStat[i]
            # 判断单场统计是否一致
            # 0分差、1得分、2前板、3后板、4总板、5助攻、6助攻得分、7抢断、8盖帽、9失误、10犯规、11时间
            rop = 0 if ROP == 'regular' else 1
            time = int(game[8+rop].split(':')[0]) * 60 + int(game[8+rop].split(':')[1])
            tmp = [int(game[6+rop][game[6+rop].index('(')+1:game[6+rop].index(')')]),
                   int(game[26+rop]), int(game[18+rop]), int(game[19+rop]),
                   int(game[20+rop]), int(game[21+rop]), 0, int(game[22+rop]),
                   int(game[23+rop]), int(game[24+rop]), int(game[25+rop]), time]
            try:
                for i in range(numStat):
                    if i != 6:
                        if i == 11 and statSingleGame[i] % 1 != 0 and str(statSingleGame[i])[-1] == '5':
                            assert int(str(statSingleGame[i]).split('.')[0])+1 == tmp[i]
                        else:
                            assert int(round(statSingleGame[i])) == tmp[i]
            except:
                print(i, statSingleGame[i], tmp[i], gameMark)
            # return
    # 计算生涯总数、分时段平均
    statMean = []
    statAll = [0] * numStat
    for ind_Mean in range(numStat):
        statMean.append([0] * 4080)
        for i in pP[ind_Mean]:
            statMean[ind_Mean] = addList(i, statMean[ind_Mean])
            statAll[ind_Mean] += i[-1]
        statMean[ind_Mean] = np.array(statMean[ind_Mean])
        statMean[ind_Mean] = statMean[ind_Mean] / len(pP[ind_Mean])
    statMean[11] /= 60
    statAll[11] /= 60
    print(statMean[11][0], statMean[11][-1], statAll[11], startUp)
    # 统计分时段命中率
    pct = [[], [], []]
    for method in range(3):
        for index in range(len(goalOrMiss[0][method])):
            FG = goalOrMiss[0][method][index]
            FGA = goalOrMiss[0][method][index] + goalOrMiss[1][method][index]
            if FGA:
                p = FG / FGA * 100
                pct[method].append([p, '%d/%d' % (FG, FGA), '%d:%d' % (index*inter//60, index*inter%60)])
            else:
                pct[method].append([None])
    # 画图
    if '1':
        if ROP == 'regular':
            plt.figure(figsize=(30, 20))
        else:
            plt.figure(figsize=(50, 30))
        legends = ['球队分差', '得分', '前场篮板', '后场篮板', '全场篮板', '助攻', '助攻得分', '抢断', '盖帽', '失误', '犯规', '时间']
        for i in range(numStat):
            legends[i] += ('  场均：%.2f，总数：%d' % (statMean[i][-1], statAll[i]))
        for i in range(numStat):
            plt.plot(list(range(4080)), statMean[i], linewidth=2,
                     label=legends[i], color=colors[i])
        
        plt.xlim(0, 4080)
        ylim = 40 if ROP == 'regular' else 45
        plt.ylim(0, ylim)
        xlabels = ['0',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
                   '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
                   '1', '2', '3', '4', '5', '1', '2', '3', '4', '5',
                   '1', '2', '3', '4', '5', '1', '2', '3', '4', '5']
        fontsizex = 18 if ROP == 'regular' else 30
        plt.xticks(np.arange(0, 4140, 60), xlabels, fontsize=fontsizex)
        plt.yticks(np.arange(0, ylim+1, 2), fontsize=30)
        plt.grid(axis='x', linestyle='--', color='#D3D3D3')
        plt.grid(axis='y', linestyle='--', color='#D3D3D3')
        ax = plt.gca()
        a = ax.get_ygridlines()
        for b in a:
            b.set_linestyle('-')
            b.set_linewidth(2)
        a = ax.get_xgridlines()
        a = [a[12], a[24], a[36], a[48], a[53], a[58], a[63]]
        for b in a:
            b.set_linestyle('-')
            b.set_linewidth(2)
        
        ss = ['跳投', '上篮', '扣篮', '勾手', '补篮', '其它', '三分']
        mets = ''
        for i in range(len(scoreMethod[0])):
            mets += (ss[i] + '：' + '%d/%d' % (scoreMethod[0][i], scoreMethod[0][i] + scoreMethod[1][i]) + '，助攻：%d' % scoreMethod[2][i] + '\n')
        mets = mets.rstrip()
        if ROP == 'regular':
            plt.text(1260, 32.75, mets, fontsize = 24, wrap=False,
                 bbox=dict(boxstyle='round, pad=0.5', fc='yellow', ec='k', lw=1 ,alpha=0.4))
            plt.xlabel('比赛时长', fontsize=30)
            plt.title('%s\t出场数：%d/%d' % (playerName, startUp, len(pP[0])), fontsize=36)
            plt.legend(fontsize=24)
        else:
            plt.text(1260, 36.25, mets, fontsize = 40, wrap=False,
                 bbox=dict(boxstyle='round, pad=0.5', fc='yellow', ec='k', lw=1 ,alpha=0.4))
            plt.xlabel('比赛时长', fontsize=40)
            plt.title('%s    出场数：%d/%d' % (playerName, startUp, len(pP[0])), fontsize=50)
            plt.legend(fontsize=40)

        plt.savefig('./%sResults/playerPerformanceWithTime/%s_%s.jpg' % (ROP, playerName, playerMark), dpi = 200)
        plt.close('all')
    return scoreMethod, statAll


# 统计一段时间内的正负值变化，用于playerOnOrOffPlusMinus函数
def spanPM(start, end, ):
    diff = diffNow(play[3], HOA)
    if diff < 0:
        if DLT != -1:
            teamTime[DLT] += (now - timePtr)
            timePtr, DLT = now, -1
    elif diff > 0:
        if DLT != 1:
            teamTime[DLT] += (now - timePtr)
            timePtr, DLT = now, 1
    else:
        if DLT != 0:
            teamTime[DLT] += (now - timePtr)
            timePtr, DLT = now, 0
    playDisc = play[HomeOrAt[1]]


# 统计球员场上场下正负值，用于playerOnOrOffPlusMinus函数
def offCourtPM(start, end, pP, gameStat):
    for ti in range(start[11], end):
        if ti < 4080:
            pP[11][-1][ti] = gameStat[11]
    start[11] = end - 1


# zero为True时考虑比赛开始的特殊情况
def onCourtPM(duration, gameStat, start, pP, zero=False):
    if not zero:
        start[11] += 1
    gameStat[11] += duration
    gameStat[11] = float('%.1f' % gameStat[11])
    if zero:
        pP[11][-1][0] = 0
        start[11] += 1
    while duration >= 1:
        pP[11][-1][start[11]] = pP[11][-1][start[11]-1] + 1
        start[11] += 1
        duration -= 1
    if duration > 0:    # 若duration有小数点残留，结算到下一秒上
        duration = float('%.1f' % duration)
        pP[11][-1][start[11]] += (pP[11][-1][start[11]-1] + duration)
        pP[11][-1][start[11]] = float('%.1f' % pP[11][-1][start[11]])
        start[11] += 1
    start[11] -= 1


# 球员上场和下场球队的正负值差异统计
def playerOnOrOffPlusMinus(playerName, playerMark, HomeOrAts):
    playerFileDir = './data/players/' + playerMark + '/regularGames/regularGameBasicStat.pickle'
    f = open(playerFileDir, 'rb')
    playerGames = pickle.load(f)
    f.close()
    plusMinusAll = [0, 0]    # 统计球员生涯累计正负值，0下场1上场
    teamTime = [0, 0, 0]    # 统计球队：0平局时间1领先时间2落后时间
    playerTime = [0, 0, 0]    # 统计球员：0平局时间1领先时间2落后时间
    timeAll = [0, 0]    # 0球队总时间1球员总时间
    startUp = 0
    for season in playerGames:
        for game in season[1:]:
            gameMark, team = game[1], game[3]
            # 读取比赛文件
            gameDir = gameMarkToDir(gameMark, 'regular')
            f = open(gameDir, 'rb')
            playerGame = pickle.load(f)
            f.close()
            # 判断主客场
            HOA = 1 if team == gameMark[-3:] else 0    # 0客1主
            HomeOrAt = HomeOrAts[HOA-1]
            onOrOff = -1    # 每场比赛开场，球员上场状态未知
            lastOnCourt = -1
            plusMinus = [0, 0]    # 统计球员正负值，0下场1上场
            timePtr = 0
            DLT = 0
            # 扫描比赛表现，index为节数-1
            gameLast = 2880 + 300 * (len(playerGame) - 4)
            timeAll[0] += gameLast
            for index, quarter in enumerate(playerGame):
                for indexPlay, play in enumerate(quarter):
                    if len(play) == 6:
                        # 计算当前时间
                        now = nowTime(index, play[0])
                        # 计算分差
                        diff = diffNow(play[3], HOA)
                        if diff < 0:
                            if DLT != -1:
                                teamTime[DLT] += (now - timePtr)
                                timePtr, DLT = now, -1
                        elif diff > 0:
                            if DLT != 1:
                                teamTime[DLT] += (now - timePtr)
                                timePtr, DLT = now, 1
                        else:
                            if DLT != 0:
                                teamTime[DLT] += (now - timePtr)
                                timePtr, DLT = now, 0
                        playDisc = play[HomeOrAt[1]]
#==============================================================================
#                         if playDisc:    # 球队有动作
#                             playerPlayed = playDisc.split(' ')[0]
#                             if 'enters' in playDisc and playerMark in playDisc:    # 球员发生换人
#                                 if playerPlayed == playerMark:    # 球员替换上场
#                                     lastOnCourt_, lastOnCourt = lastOnCourt, index
#                                     if onOrOff == -1:    # 特殊：比赛开始到上一节末情况未知
#                                         _, startUp = updateQuarters(-1, index, playerGame, playerMark, gameStat, start, pP, startUp)
#                                     else:
#                                         # 首先将最后有统计的一节延伸至节末
#                                         if index - lastOnCourt_ > 0:    # 特殊：间隔节
#                                             quarterEnd = quarterStartOrEnd(lastOnCourt_, flag=False)
#                                             if onOrOff == 0:
#                                                 stopWatch(start, quarterEnd+1, pP, gameStat)
#                                             else:
#                                                 runWatch(quarterEnd-start[11], gameStat, start, pP)
#                                             updateQuarters(lastOnCourt_, index, playerGame, playerMark, gameStat, start, pP, startUp)
#                                     stopWatch(start, int(now//1+1), pP, gameStat)
#                                     if now % 1:    # 最后处理一下now中的小数点
#                                         gameStat[11] += (1 - float('0.%s' % str(now).split('.')[1]))
#                                         pP[11][-1][start[11]+1] = gameStat[11]
#                                         start[11] += 1
#                                     onOrOff = 1    # 统计完成，状态置为上场
#                                 else:    # 球员被换下
#                                     lastOnCourt_, lastOnCourt = lastOnCourt, index
#                                     if onOrOff == -1:    # 特殊：从比赛开始到当前情况未知
#                                         if index != 0:
#                                             _, startUp = updateQuarters(-1, index, playerGame, playerMark, gameStat, start, pP, startUp)
#                                         else:    # 特殊：球员首发
#                                             startUp += 1
#                                     elif onOrOff == 0:    # 特殊：跨节间，上？节情况未知
#                                         quarterStart = quarterStartOrEnd(lastOnCourt_+1)
#                                         stopWatch(start, quarterStart+1, pP, gameStat)
#                                         if index - lastOnCourt_ + 2 >= 1:    # 特殊：间隔？节情况未知
#                                             updateQuarters(lastOnCourt_, index, playerGame, playerMark, gameStat, start, pP, startUp)
#                                     else:    # 正常
#                                         if index - lastOnCourt_ > 1:    # 特殊：间隔？节情况未知
#                                             runWatch(quarterStartOrEnd(lastOnCourt_, flag=False)-start[11], gameStat, start, pP)
#                                             updateQuarters(lastOnCourt_, index, playerGame, playerMark, gameStat, start, pP, startUp)
#                                     runWatch(now-start[11], gameStat, start, pP, zero=(index==0))
#                                     onOrOff = 0    # 统计完成，状态置为下场
#             if lastOnCourt != len(playerGame) - 1 and lastOnCourt != -1:    # 比赛存在最后几节轮换不明
#                 # 首先统计本节至结束
#                 quarterEnd = quarterStartOrEnd(lastOnCourt, flag=False)
#                 if onOrOff == 0:
#                     stopWatch(start, quarterEnd+1, pP, gameStat)
#                 else:
#                     runWatch(quarterEnd-start[11], gameStat, start, pP)
#                 # 依次扫描余下的节次，判断球员是否上场
#                 onOrOff, _ = updateQuarters(lastOnCourt, len(playerGame), playerGame, playerMark, gameStat, start, pP, startUp)
#             elif lastOnCourt == -1:    # 全场比赛无此球员轮换统计，即：打满全场
#                 _, startUp = updateQuarters(-1, len(playerGame), playerGame, playerMark, gameStat, start, pP, startUp)
#             # 继续统计上场时间直到比赛结束
#             if onOrOff == 1:
#                 runWatch(quarterStartOrEnd(index, flag=False, gameEnd=True)-start[11], gameStat, start, pP)
#             stopWatch(start, len(pP[11][-1]), pP, gameStat)
#==============================================================================
            assert DLT != 0
            teamTime[DLT] += (gameLast - timePtr)
    print(timeAll, teamTime)


# 绘制球员常规赛投篮点分布图
def playerShootingSpots(playerName, playerMark, marginX, marginY, colors, ROP):
    playerFileDir = './data/players/' + playerMark + '/%sGames/%sGameBasicStat.pickle' % (ROP, ROP)
    playerGames = LoadPickle(playerFileDir)
    radius = 0.4 if ROP == 'regular' else 0.5
    seasons = []
    circles = [[], []]    # 0投中1投失
    for season in playerGames:
        teams = []
        if season and season[0] != 'G':
            circles[0].append([])
            circles[1].append([])
            if ROP == 'regular':
                year, month = int(season[1][1][:4]), int(season[1][1][4:6])
            else:
                year, month = int(season[0][0][1][:4]), int(season[0][0][1][4:6])
            if month < 8:
                year -= 1
        for game in yieldGames(ROP, season):
            gameMark, team = game[1], game[3]
            if team not in teams:
                teams.append(team)
            # 读取比赛文件
            gameDir = gameMarkToDir(gameMark, ROP, shot=True)
            playerGame = LoadPickle(gameDir)
            # 判断主客场
            HOA = 1 if team == gameMark[-3:] else 0    # 0客1主
            for play in playerGame[HOA]:
                inf = play[2]
                if playerMark in inf[2]:
                    cors = play[0].split(';')
                    x = int(cors[1].split(':')[1].rstrip('px')) + marginX
                    y = int(cors[0].split(':')[1].rstrip('px')) + marginY
                    if year >= 2013:
                        y += 20
                    if inf[3] == 'make':
                        circles[0][-1].append(plt.Circle((x, y), 0.4, color=colors[team], clip_on=False))
                    else:
                        circles[1][-1].append(plt.Circle((x, y), 0.4, color=colors[team], alpha=0.3, clip_on=False))
        if season and season[0] != 'G' and [year, teams] not in seasons:
            seasons.append([year, teams])
    if 1:
        court = mpimg.imread('nbahalfcourt.png')
        plt.figure()
        plt.imshow(court)
        ax = plt.gcf().gca()
        plt.axis('off')
        for season in range(len(seasons)):
            for index, cir in enumerate(circles[0][season]):
                ax.add_artist(cir)
        plt.title('%s' % playerName)
        plt.savefig('./%sResults/playerShootingSpots/%s_%s.jpg' % (ROP, playerName, playerMark), dpi = 500)
        plt.close('all')
    return circles, seasons
        

    
    
    

