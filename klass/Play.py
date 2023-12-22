from klass.timer import MPTime
from utils.logger import Logger

logger = Logger.logger


def isnan(x):
    return str(x) == 'nan'


class Play(object):
    def __init__(self, play_row):
        # 0: quarter, 1: 本节倒计时, 2: 客队action, 3: 客队score, 4: 比分, 5:主队score, 6:主队action
        self.play_row = play_row
        self.quarter = play_row.quarter
        self.time = MPTime(play_row.Time)
        tmp = play_row.values.tolist()
        if self.get_len() != 3:
            self.home = False if isnan(tmp[6]) else True
        self.action = tmp[2] if isnan(tmp[6]) else tmp[6]
        self.score = int(tmp[3]) if not isnan(tmp[3]) else (int(tmp[5]) if not isnan(tmp[5]) else 0)
        self.board = None if isnan(tmp[4]) else tmp[4]

    def get_len(self):
        return (~self.play_row.isna()).sum()

    def __repr__(self):
        string = ""
        string += f"quarter: {self.quarter}"
        string += f"\taction: {self.action}"
        if self.score:
            string += f"\t{'home team' if self.home else 'away team'} scores: {self.score} points"
        if self.board:
            string += f"\t{self.board}"
        return string

    def miss_score(self):
        if 'free throw' in self.action:
            return 1
        elif '2-pt' in self.action:
            return 2
        elif '3-pt' in self.action:
            return 3
        elif 'no shot' in self.action:
            return 1

    def action_type(self):
        if 'Jump' in self.action:
            return 'jump ball'
        if 'makes' in self.action:
            return 'makes'
        if 'misses' in self.action:
            return 'misses'
        if 'Offensive rebound' in self.action:
            return 'ORB'
        if 'Defensive rebound' in self.action:
            return 'DRB'
        if 'enters' in self.action:
            return 'switch'
        if 'timeout' in self.action:
            return 'timeout'
        if 'foul' in self.action and 'offensive' not in self.action:
            return 'PF'
        if 'Turnover' in self.action:
            return 'TOV'
        if 'Violation by' in self.action:
            return 'violation'
        if 'Instant' in self.action:
            return 'instant'
        if 'ejected' in self.action:
            return 'ejected'
        if 'Defensive three seconds' in self.action:
            return 'defensive three seconds'
        if 'quarter' in self.action:
            return 'quarter'
        logger.info(f"unknown action type: {self.action}")

    def action_stat(self, action_type):
        if action_type == 'instant':
            if 'Challenge' in self.action:  # 教练挑战    挑战球队0客1主
                return 'team', {'coach challenge': 1}
            else:  # 录像回放    0客1主
                return 'official', {'replay': 1}
        if action_type == 'ejected':
            return 'player', {self.action.split(' ')[0]: {'EJT': 1}}
        if action_type == 'Defensive three seconds':
            return 'player', {self.action.split(' ')[-1]: {'D3S': 1}}
        if action_type == 'violation':
            if 'Team' in self.action:
                return 'team', {self.action.split(' ')[-1]: {'D3S': 1}}




