#!/usr/bin/python
# -*- coding:utf8 -*-

from util import LoadPickle, writeToPickle
from klasses.Player import Player
from klasses.miscellaneous import MPTime
from tqdm import tqdm


class playerRAT(object):
    def __init__(self, RoP):
        self.dir = './data/seasons_RAT/'
        self.plyrs = LoadPickle('./data/playerBasicInformation.pickle')
        self.RoP = RoP

    def seasonfile(self, sn):
        file = './data/seasons_RAT/%s.pickle' % sn
        return LoadPickle(file)

    def singleplayer(self, pm):
        player = Player(pm, self.RoP)
        if not player.exists or isinstance(player.data, list):
            return '', ''
        pres = {}    # 球员结果
        atds = 0    # 总人数
        for ss, yy in player.yieldSeasons():
            yy = yy.replace('-', '_' + yy[:2] if yy[2:4] != '99' else '_20')
            try:
                sf = self.seasonfile(yy)
            except:
                continue
            sgn = sf.shape[0]
            ig = 0
            for game in player.yieldGames(ss):
                gm, wol, diff = game['Date' if self.RoP == 'regular' else 'Playoffs'],\
                                game['WoL'][0], int(game['WoL'][3:-1])
                while sf['gm'][ig] != gm and ig < sgn - 1:
                    ig += 1
                gb = sf.loc[ig]
                refs, atd, tog = gb['Referees'].split(', '),\
                                 gb['Attendance'] if gb['Attendance'] != -1 else 0, gb['Time of Game']
                if atd:
                    atds += atd    # 球馆观众人数
                tog = MPTime(tog, reverse=False) if tog else MPTime('0:00.0', reverse=False)
                if refs[0]:
                    for r in refs:    # 执法裁判
                        if r not in pres:
                            pres[r] = [0, 0, 0, 0, MPTime('0:00.0', reverse=False)]    # 胜率、胜场数、总场数、分差、比赛时长
                        if wol == 'W':
                            pres[r][1] += 1
                        pres[r][2] += 1
                        pres[r][3] += diff
                        pres[r][4] += tog

        for i in pres:
            pres[i][0] = '%.1f%%' % (pres[i][1] / pres[i][2] * 100)
            pres[i][4] = pres[i][4].average(pres[i][2])
            pres[i][3] = '%.1f' % (pres[i][3] / pres[i][2])
        return sorted(pres.items(), key=lambda x: x[1][1], reverse=True), atds / player.games

    def players(self):
        allres = {}
        for p in tqdm(self.plyrs[1:]):
            ix, ming = 2 if self.RoP == 'regular' else 4, 500 if self.RoP == 'regular' else 50
            if p[ix] and int(p[ix]) > ming:
                pm = p[1].split('/')[-1][:-5]
                # print(pm)
                tmp, atds = self.singleplayer(pm)
                if tmp:
                    allres[pm] = [tmp, atds]
        writeToPickle('./data/playerRATs_%s.pickle' % self.RoP, allres)


if __name__ == '__main__':
    regularOrPlayoffs = ['regular', 'playoff']
    RoP = regularOrPlayoffs[0]
    rat = playerRAT(RoP)
    # rat.singleplayer('jamesle01')
    rat.players()
