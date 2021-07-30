import sys
sys.path.append('../')
import os
from Game_nba import Game_nba
from klasses.Game import Game
from util import writeToPickle, LoadPickle, gameMark_nba2bbr
from tqdm import tqdm


chr_dict = {192: 'A', 193: 'A', 194: 'A', 195: 'A', 196: 'A', 197: 'A', 199: 'C',
            200: 'E', 201: 'E', 202: 'E', 203: 'E', 204: 'I', 205: 'I', 206: 'I',
            207: 'I', 208: 'D', 209: 'N', 210: 'O', 211: 'O', 212: 'O', 213: 'O',
            214: 'O', 217: 'U', 218: 'U', 219: 'U', 220: 'U', 221: 'Y', 222: 'P',
            223: 'ss', 224: 'a', 225: 'a', 226: 'a', 227: 'a', 228: 'a', 229: 'a',
            231: 'c', 232: 'e', 233: 'e', 234: 'e', 235: 'e', 236: 'i', 237: 'i',
            238: 'i', 239: 'i', 241: 'n', 242: 'o', 243: 'o', 244: 'o', 245: 'o', 
            246: 'o', 249: 'u', 250: 'u', 251: 'u', 252: 'u', 253: 'y', 254: 'p',
            255: 'y', 256: 'A', 257: 'a', 258: 'A', 259: 'a', 260: 'A', 261: 'a',
            262: 'C', 263: 'c', 264: 'C', 265: 'c', 266: 'C', 267: 'c', 268: 'C',
            269: 'c', 270: 'D', 271: 'd', 272: 'D', 273: 'd', 274: 'E', 275: 'e',
            276: 'E', 277: 'e', 278: 'E', 279: 'e', 280: 'E', 281: 'e', 282: 'E',
            283: 'e', 284: 'G', 285: 'g', 286: 'G', 287: 'g', 288: 'G', 289: 'g',
            290: 'G', 291: 'g', 292: 'H', 293: 'h', 294: 'H', 295: 'h', 296: 'I',
            297: 'i', 298: 'I', 299: 'i', 300: 'I', 301: 'i', 302: 'I', 303: 'i',
            304: 'I', 305: 'i', 306: 'J', 307: 'j', 308: 'J', 309: 'j', 310: 'K',
            311: 'k', 312: 'k', 313: 'L', 314: 'l', 315: 'L', 316: 'l', 317: 'L',
            318: 'l', 319: 'L', 320: 'l', 321: 'L', 322: 'l', 323: 'N', 324: 'n',
            325: 'N', 326: 'n', 327: 'N', 328: 'n', 329: 'n', 330: 'N', 331: 'n',
            332: 'O', 333: 'o', 334: 'O', 335: 'o', 336: 'O', 337: 'o', 340: 'R',
            341: 'r', 342: 'R', 343: 'r', 344: 'R', 345: 'r', 346: 'S', 347: 's',
            348: 'S', 349: 's', 350: 'S', 351: 's', 352: 'S', 353: 's', 354: 'T',
            355: 't', 356: 'T', 357: 't', 358: 'T', 359: 't', 360: 'U', 361: 'u',
            362: 'U', 363: 'u', 364: 'U', 365: 'u', 366: 'U', 367: 'u', 368: 'U',
            369: 'u', 370: 'U', 371: 'u', 372: 'W', 373: 'w', 374: 'Y', 375: 'y',
            376: 'Y', 377: 'Z', 378: 'z', 379: 'Z', 380: 'z', 381: 'Z', 382: 'z'}


def ixs(tar, L):
    # print(tar, L)
    if isinstance(tar, str):
        res = []
        for i, x in enumerate(L):
            if x == tar:
                res.append(i)
        return res
    else:
        res = []
        for i, x in enumerate(L[0]):
            if x == tar[0] and L[1][i] == tar[1]:
                res.append(i)
        return res


def adjust(ns):
    if ns[1] == 'L�pez':
        ns[1] = 'Lopez'
    elif ns[1] == 'Fel�cio':
        ns[1] = 'Felicio'
    elif ns[1] == 'Hernang�mez':
        ns[1] = 'Hernangomez'
    elif ns[1] == 'Laprov�ttola':
        ns[1] = 'Laprovittola'
    elif ns[1] == "N'Diaye":
        ns[1] = "N'diaye"
    elif ns[1] == "N'Dong":
        ns[1] = 'Ndong'
    elif ns[1] == 'Zhizhi':
        ns[1] = 'Zhi-zhi'
    elif ns[1] == 'Fern�ndez':
        ns[1] = 'Fernandez'
    elif ns[1] == 'Labissi�re':
        ns[1] = 'Labissiere'
    elif ns[0] == 'J.R.':
        ns[0] = 'JR'
    elif ns[1] == 'Ilunga-Mbenga':
        ns[1] = 'Mbenga'
    elif ns[1] == 'Waller-Prince':
        ns[1] = 'Prince'
    elif ns == ['Steve', 'Smith']:
        ns = ['Steven', 'Smith']
    elif ns == ['Jakob', 'Poltl']:
        ns = ['Jakob', 'Poeltl']
    elif ns == ['Yao', 'Ming'] or ns == ['Ha', 'Seung-Jin'] or ns == ['Yi', 'Jianlian'] or ns == ['Sun', 'Yue']:
        ns[0], ns[1] = ns[1], ns[0]
    elif ns == ['Nen�', 'Hil�rio']:
        ns = ['Nene', 'Hilario']
    elif ns == ['Ronald', 'Murray']:
        ns = ['Flip', 'Murray']
    elif ns == ['Luigi', 'Datome']:
        ns = ['Gigi', 'Datome']
    elif ns == ['Eugene', 'Jeter']:
        ns = ['Pooh', 'Jeter']
    elif ns == ['Peter', 'John', 'Ramos']:
        ns = ['Peter John', 'Ramos']
    elif ns == ['Juan', 'Carlos', 'Navarro']:
        ns = ['Juan Carlos', 'Navarro']
    elif ns == ['James', 'Michael', 'McAdoo']:
        ns = ['James Michael', 'McAdoo']
    if ns == ['Hamady', "N'diaye"]:
        ns[1] = 'Ndiaye'
    return ns


#%%
b2n_dict = LoadPickle('D:/sunyiwu/stat/stats_nba/b2n_dict.pickle')
n2b_dict = LoadPickle('D:/sunyiwu/stat/stats_nba/n2b_dict.pickle')
pm2pn_nba = LoadPickle('D:/sunyiwu/stat/stats_nba/plyrNo_NBA.pickle')
pm2pn = LoadPickle('D:/sunyiwu/stat/data/playermark2playername.pickle')
predir = 'D:/sunyiwu/stat/data_nba/origin/'
bbrdir = 'D:/sunyiwu/stat/data/seasons/'
for season in range(2020, 2021):
    ss = '%d_%d' % (season, season + 1)
    gms = [x for x in os.listdir(predir + ss) if '_003' not in x and '_005' not in x]
    for gm in tqdm(gms):
        gm_bbr = gameMark_nba2bbr(gm, ss)
        # print(gm, gm_bbr)
        # print(gm, ss)
        game = Game_nba(gm, ss)
        if game.nba_actions:
            plyrs = [[[x['personId'] for x in list(game.stats['awayTeam']['players']) if x['statistics']['minutes']],
                      [x['firstName'] for x in list(game.stats['awayTeam']['players']) if x['statistics']['minutes']],
                      [x['familyName'] if ' ' not in x['familyName'] else x['familyName'].split(' ')[0] for x in list(game.stats['awayTeam']['players']) if x['statistics']['minutes']]],
                     [[x['personId'] for x in list(game.stats['homeTeam']['players']) if x['statistics']['minutes']],
                      [x['firstName'] for x in list(game.stats['homeTeam']['players']) if x['statistics']['minutes']],
                      [x['familyName'] if ' ' not in x['familyName'] else x['familyName'].split(' ')[0] for x in list(game.stats['homeTeam']['players']) if x['statistics']['minutes']]]]
            
            game_bbr = Game(gm_bbr, 'regular' if '_002' in gm else 'playoffs')
            plyrs_bbr = game_bbr.teamplyrs()
            plyrs_bbr = [[x for x in plyrs_bbr[0]], [x for x in plyrs_bbr[-1]]]
            
            for i in range(2):
                for p in plyrs_bbr[i]:
                    if p in pm2pn:
                        pn = pm2pn[p]
                        ns = pn.split(' ')
                        tmp = []
                        for ix in range(len(ns)):
                            for x, s in enumerate(ns[ix]):
                                if not (97 <= ord(s) <= 122 or 65 <= ord(s) <= 90) and ord(s) not in [65533, 46, 45, 39]:
                                    tmp.append(s)
                            for s in tmp:
                                ns[ix] = ns[ix].replace(s, chr_dict[ord(s)])
                        
                        ns = adjust(ns)
                        ix = ixs(ns[1], plyrs[i][-1])
                        
                        if len(ix) > 1:    # familyName重复
                            ix = ixs(ns, plyrs[i][-2:])
                        
                        if len(ix) == 1:    # 匹配
                            assert ns[0][0] == plyrs[i][1][ix[0]][0]
                            if p not in b2n_dict:
                                b2n_dict[p] = plyrs[i][0][ix[0]]
                                n2b_dict[plyrs[i][0][ix[0]]] = p
                                pm2pn_nba[plyrs[i][0][ix[0]]] = plyrs[i][1][ix[0]] + ' ' + plyrs[i][2][ix[0]]
                            else:
                                assert b2n_dict[p] == plyrs[i][0][ix[0]]
                                assert n2b_dict[plyrs[i][0][ix[0]]] == p
                        elif len(ix) > 1:
                            print('姓重复', game.gm, ns)
                        else:
                            if len(plyrs_bbr[i]) == len(plyrs[i][0]):
                                print('未匹配到')
                                print(game.gm, ns)
                                print(len(plyrs_bbr[i]), len(plyrs[i][0]))
                                print(plyrs_bbr[i])
                                for l in plyrs[i]:
                                    print(l)
                                raise KeyError

writeToPickle('b2n_dict.pickle', b2n_dict)
writeToPickle('n2b_dict.pickle', n2b_dict)
writeToPickle('plyrNo_NBA.pickle', pm2pn_nba)












