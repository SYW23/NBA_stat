#!/usr/bin/python
# -*- coding:utf8 -*-

# fout type 犯规类型
ft = ['Excess timeout tech foul', 'Shooting foul', 'Teamfoul', 'Taunting technical foul',
      'Double personal foul', 'Inbound foul', 'Punching foul', 'Personal take foul',
      'Personal block foul', 'Away from play foul', 'Hanging tech foul', 'Unknown foul',
      'Loose ball foul', 'Shooting block foul', 'Elbow foul', 'Offensive foul',
      'Non unsport tech foul', 'Double technical foul', 'Personal foul', 'Delay tech foul',
      'Offensive charge foul', 'Ill def tech foul']

# turnover type 失误类型
to = ['lane violation.', 'inbound', 'out of bounds', 'traveling', 'dbl dribble', '5 sec',
      'double personal', 'turnover', 'lane violation', 'isolation violation', 'swinging elbows',
      'off goaltending', 'out of bounds lost ball', 'score in opp. basket', 'jump ball violation',
      'enter basket from below', '3 sec', '3 second', 'jump ball violation.', 'step out of bounds',
      '10 second', 'stolen pass', '8 sec', 'illegal assist', 'shot clock', 'bad pass', 'post up',
      '5 sec inbounds', 'discontinued dribble', 'punched ball', 'offensive goaltending', 'double dribble',
      'illegal pick', 'offensive foul', 'back court', 'palming', 'poss. lost ball', 'no', 'lost ball',
      'illegal screen', 'isolation violation.', 'kicked ball']


# 行为字典
bh = {'JB': '跳球', 'BP': '球权', 'MK': '得分', 'AST': '助攻', 'MS': '投失', 'BLK': '盖帽', 'ORB': '前场篮板',
      'DRB': '后场篮板', 'SWT': '换人', 'OTO': '官方暂停', 'STO': '短暂停', 'FTO': '长暂停',
      'ETT': '失误：空叫暂停', 'ETO': '技术犯规：空叫暂停', 'TF': '技术犯规', 'D3T': '违例：防守三秒',
      'CPH': '进攻路径犯规', 'FF1': '一级恶意犯规', 'FF2': '二级恶意犯规', 'PF': '犯规', 'TOV': '失误',
      'STL': '抢断', 'TVL': '球队违例', 'PVL': '球员违例', 'CCH': '教练挑战', 'IRP': '录像回放',
      'EJT': '驱逐出场', 'D3S': '违例：防守三秒'}
