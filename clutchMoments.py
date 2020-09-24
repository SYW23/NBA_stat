#!/usr/bin/python
# -*- coding:utf8 -*-

from tqdm import tqdm
import numpy as np
import pandas as pd
from util import LoadPickle
from klasses.Game import Game, Play
from klasses.miscellaneous import MPTime
import os


class ClutchMomentsDetector(object):
    def __init__(self, RoP, start_season, end_season, diffplus=5, diffminus=-5, lastmins='5:00.0'):
        self.ss = start_season
        self.es = end_season
        self.dp = diffplus
        self.dm = diffminus
        self.lm = lastmins
        self.RoP = 0 if RoP == 'regular' else 'playoff'
        self.pm2pn = LoadPickle('./data/playermark2playername.pickle')
        self.columns = ['score',
                        'freeThrowPct', 'freeThrowMade', 'freeThrowAttempts',
                        'twoPtPct', 'twoPtMade', 'twoPtAttempts',
                        'threePtPct', 'threePtMade', 'threePtAttempts',
                        'fieldGoalPct', 'fieldGoalMade', 'fieldGoalAttempts',
                        'twoPtAsted', 'threePtAsted', 'fieldGoalAsted',
                        'eFG%', 'TS%']

    def calpct(self, res):
        res['fieldGoalMade'] = res['twoPtMade'] + res['threePtMade']
        res['fieldGoalAttempts'] = res['twoPtAttempts'] + res['threePtAttempts']
        for i in ['freeThrow', 'twoPt', 'threePt', 'fieldGoal']:
            res['%sPct' % i] = res['%sMade' % i] / res['%sAttempts' % i]
        res['twoPtAsted'] = res['twoPtAsted'] / res['twoPtMade']
        res['threePtAsted'] = res['threePtAsted'] / res['threePtMade']
        res['fieldGoalAsted'] = res['fieldGoalAsted'] / res['fieldGoalMade']
        res['eFG%'] = (res['fieldGoalMade'] + 0.5 * res['threePtMade']) / res['fieldGoalAttempts']
        res['eFG%'].round(decimals=3)
        res['TS%'] = res['score'] / (2 * (res['fieldGoalAttempts'] + 0.44 * res['freeThrowAttempts']))
        res['TS%'].round(decimals=3)
        return res

    def dict2df(self, dct):
        res = pd.DataFrame(np.zeros((len(dct), len(self.columns))), columns=self.columns)
        for ix, p in enumerate(dct):
            res.iloc[ix] = dct[p]
        res.insert(0, 'player', list(dct.keys()))
        return res

    def detectgame(self, gm, playeres, season=0):
        game = Game(gm[:-7], 'playoff' if self.RoP else 'regular')
        for qtr in range(3, game.quarters):
            for ply in game.yieldPlay(qtr):
                play = Play(ply, qtr)
                if play.time() <= MPTime(self.lm):  # 在规定时间内
                    rec, ind = play.record()
                    s = play.score(ind=ind)
                    if s and play.diffbeforescore(s) <= self.dp:
                        try:
                            p = self.pm2pn[rec.split(' ')[0]]
                        except KeyError:
                            p = rec.split(' ')[0]
                        if season:
                            p += ' %d_%d' % (season, season + 1)
                        if p not in playeres:
                            playeres[p] = np.zeros((1, len(self.columns)))
                        if 'makes' in rec:
                            playeres[p][0, 0] += s
                            playeres[p][0, s * 3 - 1] += 1
                            if 'assist' in rec:
                                playeres[p][0, s + 11] += 1
                                playeres[p][0, 15] += 1
                        playeres[p][0, s * 3] += 1
                        # if 'Jamal Murray' in p and s == 3:
                        #     print(s, play.play, gm)
        return playeres

    def singleseason(self, season, playeres, all_time=False):
        print('%d_%d' % (season, season + 1))
        games = os.listdir('./data/seasons/%d_%d/%s/' % (season, season + 1, 'playoffs' if self.RoP else 'regular'))
        for gm in tqdm(games):
            if all_time:
                playeres = self.detectgame(gm, playeres)
            else:
                playeres = self.detectgame(gm, playeres, season=season)
        return playeres

    def detect_by_season(self):
        res = pd.DataFrame(columns=['player'] + self.columns)
        for season in range(self.ss, self.es + 1):
            playeres = {}
            playeres = self.singleseason(season, playeres)
            tmp = self.dict2df(playeres)
            res = res.append(tmp, ignore_index=True)

        res = self.calpct(res)
        res.sort_values(by=['score', 'TS%'], inplace=True, ascending=[False, False])
        tmp = res['player'].str[-9:]
        res['player'] = res['player'].str[:-10]
        res.insert(1, 'season', tmp)
        # res.to_csv('clutch_moments_%d_to_%d.csv' % (self.ss, self.es), index=None)
        res.to_excel('./clutch_moments/%s/clutch_moments_%d_to_%d_by_season.xlsx' % ('playoff' if self.RoP else 'regular', self.ss, self.es), sheet_name='%d_to_%d' % (self.ss, self.es), index=False)

    def detector_all_time(self):
        res = pd.DataFrame(columns=['player'] + self.columns)
        playeres = {}
        for season in range(self.ss, self.es + 1):
            playeres = self.singleseason(season, playeres, all_time=True)
        playeres = self.dict2df(playeres)
        res = res.append(playeres, ignore_index=True)
        res = self.calpct(res)
        res.sort_values(by=['score', 'TS%'], inplace=True, ascending=[False, False])
        res.to_excel('./clutch_moments/%s/clutch_moments_%d_to_%d_all_time.xlsx' % ('playoff' if self.RoP else 'regular', self.ss, self.es), sheet_name='%d_to_%d' % (self.ss, self.es), index=False)


if __name__ == '__main__':
    regularOrPlayoffs = ['regular', 'playoff']
    RoP = regularOrPlayoffs[0]
    cmd = ClutchMomentsDetector(RoP, 1996, 2019)
    cmd.detect_by_season()
    # cmd.detector_all_time()


