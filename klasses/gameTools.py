#!/usr/bin/python
# -*- coding:utf8 -*-

# fout type 犯规类型
ft = ['Punching foul', 'Elbow foul', 'Double personal foul', 'Personal take foul', 'Shooting foul',
      'Personal block foul', 'Shooting block foul', 'Offensive foul', 'Technical foul', 'Personal foul',
      'Offensive charge foul', 'Away from play foul', 'Loose ball foul', 'Unknown foul', 'Inbound foul']
# Teamfoul最后一次出现是在1999-2000赛季，大部分为进攻犯规后的附加项（无失误附加说明，但仍记失误）
# 小部分是一种使对手获得一次技术发球的犯规，具体种类未知

# turnover type 失误类型
to = ['lost ball', 'illegal pick', 'lane violation.', 'punched ball', 'isolation violation', 'stolen pass',
      'post up', 'back court', 'out of bounds', 'step out of bounds', 'illegal screen', 'isolation violation.',
      '8 sec', 'off goaltending', 'discontinued dribble', 'double dribble', 'score in opp. basket', 'lane violation',
      '5 sec inbounds', 'no', 'palming', 'jump ball violation.', '3 sec', 'bad pass', 'out of bounds lost ball',
      'dbl dribble', '3 second', '5 sec', 'turnover', 'double personal', 'enter basket from below', 'poss. lost ball',
      'offensive goaltending', 'jump ball violation', 'inbound', 'kicked ball', '10 second', 'swinging elbows',
      'shot clock', 'illegal assist', 'offensive foul', 'traveling']

# violation type 违例类型
vl = ['kicked ball', 'violation', 'jump ball', 'def goaltending',
      'illegal defense', 'no', 'delay of game', 'lane', 'double lane']
# Violation by Team (def goaltending)最后一次出现是在1999-2000赛季，规则未知

# 行为字典
bh = {'JB': '跳球', 'BP': '球权', 'MK': '得分', 'AST': '助攻', 'MS': '投失', 'BLK': '盖帽', 'ORB': '前场篮板',
      'DRB': '后场篮板', 'SWT': '换人', 'OTO': '官方暂停', 'STO': '短暂停', 'FTO': '长暂停', 'ETT': '失误：空叫暂停',
      'ETO': '技术犯规：空叫暂停', 'TF': '技术犯规', 'FF1': '一级恶意犯规',
      'FF2': '二级恶意犯规', 'PF': '犯规', 'TOV': '失误', 'STL': '抢断', 'TVL': '球队违例', 'PVL': '球员违例',
      'CCH': '教练挑战', 'IRP': '录像回放', 'EJT': '驱逐出场', 'D3S': '违例：防守三秒', 'DTF': '双方技术犯规'}
# 无法从play-by-play看出教练挑战是否成功
