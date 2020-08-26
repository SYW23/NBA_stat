import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pickle
from util import playerShootingSpots
import os
import matplotlib.animation as animation
plt.rcParams['animation.ffmpeg_path'] = r'C:/Program Files (x86)/ffmpeg/bin/ffmpeg.exe'
plt.close('all')
#%%
marginX = 5
marginY = 10
regularOrPlayoffs = ['regular', 'playoff']
colors = {'CLE':'#FF8C00', 'MIA':'#FF0000', 'LAL':'#800080', 'GSW':'#FFD700', 'SAC':'#8A2BE2', 'POR':'#8B0000',
          'SAS':'#031016', 'MIL':'#006400', 'SEA':'#228B22', 'BOS':'#06683C', 'DEN':'#191970', 'NYK':'#FFA500',
          'OKC':'#0371AE', 'HOU':'#FF2121', 'ATL':'#B22222', 'MIN':'#0000CD', 'DET':'#DC143C', 'LAC':'#4169E1',
          'UTA':'#FF6347', 'CHI':'#FF000D', 'MEM':'#4E518B', 'TOR':'#740B13', 'PHI':'#AF0932', 'WAS':'#023064',
          'DAL':'#026AB3', 'PHO':'#CE4E10', 'NJN':'#1E1E1E', 'ORL':'#0175B8', 'PAC':'#053C7C', 'NOP':'#002B5B',
          'CHH':'#4682B4', 'NOH':'#4682B4', 'VAN':'#4E518B', 'IND':'#002D62', 'CHO':'#017C95', 'CHA':'#017C95',
          'BRK':'#1E1E1E', 'NOK':'#4682B4'}

f = open('./data/playerBasicInformation.pickle', 'rb')
playerInf = pickle.load(f)
f.close()

player = []
for i in playerInf[1:]:
    playerName, playerMark = i[0],i[1].split('/')[-1].rstrip('.html')
    playerName = playerName.replace(' ', '')
    playerName = playerName.replace('-', '')
    if i[2] and i[3]:
        if int(i[6]) >= 1997 and os.path.exists('./data/players/%s' % playerMark):
            player.append([playerName, playerMark])

regularOrPlayoff = 1
for i in player:
    print("starting analysing %s's games ..." % i[0])
    circles, seasons = playerShootingSpots(i[0], i[1], marginX, marginY, colors, regularOrPlayoffs[regularOrPlayoff])
    assert len(seasons) == len(circles[0]) == len(circles[1])
    numSeason = len(circles[0])
    #%%
    if 0:
        court = mpimg.imread('nbahalfcourt.png')
        fig = plt.figure()
        plt.imshow(court)
        
        fps, dpi = 1, 100
        metadata = dict(title='Movie Test', artist='Matplotlib',comment='Movie support!')
        writer = animation.FFMpegWriter(fps=fps, metadata=metadata)
        with writer.saving(fig, './%sResults/playerShootingSpots_gif/%s_%s.mp4' % (regularOrPlayoffs[regularOrPlayoff], i[0], i[1]), dpi):
            plt.ion()
            ax = plt.gcf().gca()
            plt.axis('off')
            s = 0
            while s < numSeason:
                print('赛季%d' % (s+1))
                teams = ', '.join(seasons[s][1])
                for season in range(s+1):
                    for index, cir in enumerate(circles[0][season]):
                        ax.add_artist(cir)
                plt.title('%s-%s    %s' % (str(seasons[s][0]), str(seasons[s][0]+1), teams))
                plt.imshow(court)
                # plt.pause(0.1)
                writer.grab_frame()
                if s == numSeason - 1:
                    writer.grab_frame()
                    writer.grab_frame()
                    writer.grab_frame()
                ax.cla()
                plt.axis('off')
                s += 1
            
            plt.imshow(court)
            # plt.savefig('./%sResults/playerShootingSpots/%s_%s.jpg' % (regularOrPlayoffs[regularOrPlayoff], i[0], i[1]), dpi = 500)
        os.system('ffmpeg -i ./%sResults/playerShootingSpots_gif/%s_%s.mp4 ./%sResults/playerShootingSpots_gif/%s_%s.gif' % (regularOrPlayoffs[regularOrPlayoff], i[0], i[1], regularOrPlayoffs[regularOrPlayoff], i[0], i[1]))
    plt.close('all')
    print('\tDone')
