import pickle
import numpy as np
from PIL import Image
import os
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from util import playerOnOrOffPlusMinus
from pylab import *

regularOrPlayoffs = ['regular', 'playoff']
HomeOrAts = [[4, 5], [2, 1]]    # 主，客

f = open('./data/playerBasicInformation.pickle', 'rb')
playerInf = pickle.load(f)
f.close()
players = []
for i in playerInf[1:]:
    playerName, playerMark = i[0],i[1].split('/')[-1].rstrip('.html')
    playerName = playerName.replace(' ', '')
    playerName = playerName.replace('-', '')
    playerDir = playerName + '_' + playerMark
    if i[2] and i[3]:
        if int(i[6]) >= 1997 and os.path.exists('./data/players/%s' % playerDir):
            players.append([playerName, playerMark, playerDir])

for i in players[35:36]:
    print("starting analysing %s's games ..." % i[0], end='')
    playerOnOrOffPlusMinus(i[0], i[1], i[2], HomeOrAts)
    
    
    
    
    
    
    