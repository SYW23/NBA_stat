import sys
sys.path.append('../')
import os
from util import read_nba_pbp, gameMark_nba2bbr
from stats_nba.Play_nba import Play_nba
from klasses.miscellaneous import MPTime
from tqdm import tqdm
import math

subTypes = {}


class Game_nba(object):
    def __init__(self, gm, ss):
        self.gm = gm.split('/')[-1]
        self.loc_tm = {'v': 0, 'h': 1}
        self.ss = ss
        if '/' not in gm:
            gm = 'D:/sunyiwu/stat/data_nba/origin/%s/%s' % (ss, gm)
        if gm != '2017-10-20_0021700025_gsw-vs-nop.txt' and gm != '2004-02-18_0020300778_was-vs-noh.txt':
            self.nba_actions, inf = read_nba_pbp(gm)
        else:
            _, inf = read_nba_pbp(gm)
            self.nba_actions = None
        if self.nba_actions or self.gm == '2017-10-20_0021700025_gsw-vs-nop.txt' or self.gm == '2004-02-18_0020300778_was-vs-noh.txt':
            # # 根据period, actionNumber, clock排序pbp记录
            # self.nba_actions = [actions[0]]
            # # print(actions[0])
            # assert self.nba_actions[0]['period'] == 1
            # for i in actions[1:]:
            #     if i['actionNumber'] >= self.nba_actions[-1]['actionNumber']:
            #         if i['actionNumber'] == self.nba_actions[-1]['actionNumber'] and not i['actionType']:
            #             self.nba_actions.insert(-1, i)
            #         else:
            #             self.nba_actions.append(i)
            #     else:
            #         if i['clock'] < self.nba_actions[-1]['clock']:
            #             assert i['period'] == self.nba_actions[-1]['period']
            #             self.nba_actions.append(i)
            #         else:
            #             x = -1
            #             try:
            #                 while len(self.nba_actions) > -x and self.nba_actions[x]['actionNumber'] > i['actionNumber']:
            #                     x -= 1
            #                 self.nba_actions.insert(x + 1, i)
            #             except:
            #                 print(self.gm, self.nba_actions)
            #                 raise KeyError
            # 整理比赛主要信息
            self.qtrs = inf['period']
            self.rtID = inf['awayTeamId']
            self.htID = inf['homeTeamId']
            self.rtTri = inf['awayTeam']['teamTricode']
            self.htTri = inf['homeTeam']['teamTricode']
            self.duration = inf['duration']
            self.attendance = inf['attendance']
            self.arena = inf['arena']
            self.officials = inf['officials']
            self.stats = {'awayTeam': inf['awayTeam'], 'homeTeam': inf['homeTeam']}
            self.gameRecap = inf['gameRecap']

            plyrs = [self.stats['awayTeam']['players'], self.stats['homeTeam']['players']]
            self.plyrs = [[[x['personId'], x['firstName'], x['familyName']] for x in plyrs[0]],
                          [[x['personId'], x['firstName'], x['familyName']] for x in plyrs[1]]]
            self.record = []

    def game_scanner(self):
        rebs = {}
        for ac in self.nba_actions:
            try:
                play = Play_nba(ac)
                plyr = play.plyr()
                if self.record and 'S' not in self.record[-1]:    # 处理球队初始得分及累计得分
                    if len(self.record) == 1:
                        self.record[0]['S'] = [0, 0]
                    else:
                        self.record[-1]['S'] = self.record[-2]['S']
                act = ac['actionType']
                # print(act)
                if act and act != 'period' and len(act) != 40:
                    act += (' ' * (40 - len(act)))
                # 统计actionType及类别下的subType
                if act and act not in subTypes:
                    subTypes[act] = []
                if act and ac['subType'] not in subTypes[act]:
                    subTypes[act].append(ac['subType'])
                # =========================跳球===================================
                if act == 'Jump Ball                               ':
                    # print(ac)
                    if ac['description'] and 'Coach Challenge' not in ac['description']:
                        tmp = ac['description'].split(' vs. ')
                        if tmp != [' ']:
                            rp, hp, bp = tmp[0].split('Jump Ball ')[-1], tmp[1].split(' ')[0][:-1], tmp[1].split(' ')[-1]
                        else:
                            rp, hp, bp = '', '', ''
                        if bp == 'to':
                            bp = ''
                        # if not self.record and not bp:    # 开场跳球无tip to
                        #     print(self.gm, ac)
                        self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'JB': [rp, hp, bp]})
                # =========================运动战出手（in or out）===================================
                elif 'Shot' in act:
                    # print(ac)
                    s = 3 if '3PT' in ac['description'] else 2    # 出手分数
                    D = math.sqrt(ac['xLegacy'] ** 2 + ac['yLegacy'] ** 2) / 10  # D出手距离
                    M = ac['subType'].strip()  # M出手类型
                    self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'MK' if 'Made' in act else 'MS': [plyr, s, 0 if ac['location'] == 'v' else 1], 'D': D, 'M': M})
                    self.record[-1]['C'] = [ac['xLegacy'], ac['yLegacy']]
                    # =========================运动战进球===================================
                    if act == 'Made Shot                               ':
                        self.record[-1]['S'] = [int(ac['scoreAway']), int(ac['scoreHome'])]    # 出手后比分
                        # =========================助攻===================================
                        if 'AST' in ac['description']:
                            self.record[-1]['AST'] = ac['description'].split(' ')[-3][1:] if '. ' not in ac['description'].split('(')[-1] else ac['description'].split(' ')[-3]
                    # =========================运动战投失===================================
                # =========================罚球（in or out）===================================
                elif act == 'Free Throw                              ':
                    # 罚球进度D（1/1 1/2 1/3 2/2 2/3 3/3）和种类M（Technical Flagrant Clear_Path）
                    tmp = ac['subType'].strip().split(' ')
                    if 'of' in tmp:
                        D = [int(tmp[-3]), int(tmp[-1])]
                        if len(tmp) == 5:
                            M = ''
                        else:
                            M = ' '.join(tmp[2:-3])
                    else:
                        D = [1, 1]
                        M = ' '.join(tmp[2:])
                    self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'MS' if 'MISS' in ac['description'] else 'MK': [plyr, 1, 0 if ac['location'] == 'v' else 1], 'D': D, 'M': M})
                    # =========================罚球进球===================================
                    if 'MISS' not in ac['description']:
                        S = self.record[-2]['S'].copy() if len(self.record) > 1 else [0, 0]
                        S[0 if ac['location'] == 'v' else 1] += 1
                        self.record[-1]['S'] = S
                # =========================篮板===================================
                elif act == 'Rebound                                 ':
                    # print(ac['description'])
                    if ac['personId']:
                        if len(str(ac['personId'])) == 10:
                            pass
                        else:
                            tmp = ac['description'].split(' ')
                            if ac['personId'] in rebs:
                                # print(rebs[ac['personId']])
                                # print(ac['description'])
                                assert rebs[ac['personId']][0] <= tmp[-2][-1] or rebs[ac['personId']][1] <= tmp[-1][-2] or self.gm == '2017-10-20_0021700025_gsw-vs-nop.txt'
                                r = 'ORB' if rebs[ac['personId']][0] != tmp[-2][-1] else 'DRB'
                                # print(r)
                                self.record.append({'Q': ac['period'] - 1, 'T': play.now(), r: plyr})
                            else:
                                assert tmp[-2][-1] > '0' or tmp[-1][-2] > '0'
                                r = 'ORB' if tmp[-2][-1] == '1' else 'DRB'
                                # print(r)
                                self.record.append({'Q': ac['period'] - 1, 'T': play.now(), r: plyr})
                            rebs[ac['personId']] = [tmp[-2][-1], tmp[-1][-2]]
                # =========================抢断or盖帽===================================
                elif not act:
                    # =========================盖帽===================================
                    if 'BLOCK' in ac['description']:
                        x = -1
                        while 'MS' not in self.record[x]:
                            x -= 1
                        # assert 'MS' in self.record[-1]
                        assert self.record[x]['T'] == play.now() and self.record[x]['MS'][1] > 1
                        self.record[x]['BLK'] = plyr
                    # =========================抢断===================================
                    elif 'STEAL' in ac['description']:
                        assert 'TOV' in self.record[-1]
                        self.record[-1]['STL'] = plyr
                # =========================失误===================================
                elif act == 'Turnover                                ':
                    self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'TOV': ac['subType'].strip(), 'plyr': plyr})
                # =========================犯规===================================
                elif act == 'Foul                                    ':
                    # print(ac)    # ['PF', 'D3S', 'TF', 'FF1', 'FF2', 'DTF']
                    if 'Technical' in ac['subType']:
                        self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'TF': plyr})
                    elif 'Defense 3 Second' in ac['subType']:
                        self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'D3S': plyr})
                    elif 'Flagrant Type 1' in ac['subType']:
                        self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'FF1': plyr})
                    elif 'Flagrant Type 2' in ac['subType']:
                        self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'FF2': plyr})
                    else:
                        self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'PF': ac['subType'], 'plyr': plyr})
                elif act == 'Violation                               ':
                    if len(str(ac['personId'])) == 10:
                        self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'TVL': ac['subType'].strip()})
                    else:
                        self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'PVL': ac['subType'].strip(), 'plyr': plyr})
                elif act == 'Substitution                            ':
                    # print(ac)
                    on_plyr = ac['description'][ac['description'].index(': ') + 2:ac['description'].index('FOR') - 1]
                    side = 0 if ac['teamId'] == self.rtID else 1
                    fi = []
                    for ix, pn in enumerate(self.plyrs[side]):
                        if on_plyr == pn[2]:
                            fi.append(ix)
                    if len(fi) == 1:
                        on_plyr = {self.plyrs[side][ix][0]: self.plyrs[side][ix][1][0] + '. ' + self.plyrs[side][ix][2]}
                    else:
                        pass
                        # print('换人球员匹配有误', self.gm, ac)
                        # print(self.plyrs)
                    # for
                    self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'SWT': [on_plyr, plyr, side]})
                elif act == 'Timeout                                 ':
                    self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'TOT': 0 if ac['personId'] == self.rtID else 1})
                elif act == 'Ejection                                ':
                    self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'EJT': plyr})
                # elif act == 'Instant Replay                          ':
                #     self.record.append({'Q': ac['period'] - 1, 'T': play.now(), 'IRP': 0 if ac['personId'] == self.rtID else 1})
                else:
                    if act not in ['period', 'Instant Replay                          ']:
                        print(ac)
            except:
                print(self.gm, gameMark_nba2bbr(self.gm, self.ss), ac)
                raise KeyError
        for ix, rec in enumerate(self.record):
            if ix and rec['Q'] == self.record[ix - 1]['Q'] and MPTime(rec['T']) > MPTime(self.record[ix - 1]['T']):
                self.record[ix], self.record[ix - 1] = self.record[ix - 1], self.record[ix]
                # print('时间混乱！', self.gm, rec)
                # break


if __name__ == '__main__':
    predir = 'D:/sunyiwu/stat/data_nba/origin/'
    for season in range(2000, 2021):
        ss = '%d_%d' % (season, season + 1)
        gms = os.listdir(predir + ss)
        for gm in tqdm(gms):
            # print(gm)
            game = Game_nba(gm, ss)
            if game.nba_actions:
                game.game_scanner()
            # print(game.plyrs)
            # print('\n')
            # for i in game.stats['awayTeam']['players']:
            #     tmp = list(i['statistics'].values())[1:-1]
            #     tmp = tmp[0:2] + tmp[3:5] + tmp[6:8] + tmp[9:]
            #     print(tmp)
            #     print()

    # for i in game.record:
    #     print(i)
    print('\n')
    for k in subTypes:
        print(k, len(subTypes[k]))
        print('\t', subTypes[k])
