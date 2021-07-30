import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from util import getCode, writeToPickle, LoadPickle
import re
import pandas as pd
import numpy as np


awards = ['mvp', 'roy', 'dpoy', 'smoy', 'mip']
cols = ['Rank', 'Player', 'Age', 'Tm', 'First', 'Pts Won', 'Pts Max', 'Share',
        'G', 'MP', 'PTS', 'TRB', 'AST', 'STL', 'BLK', 'FG%', '3P%', 'FT%', 'WS', 'WS/48']
for i in range(2):
    for season in range(2021, 2022):
        url = 'https://www.basketball-reference.com/awards/awards_%d.html' % season
        soup = getCode(url, 'UTF-8')
        rows = soup.find_all('div', class_='table_container')[i].find_all('tr')[1:]
        df = pd.DataFrame(columns=cols)
        for row in rows:
            ths = row.find_all('th')
            if len(ths) == 1:
                tds = row.find_all('td')
                data = np.array([ths[0].text] + [tds[0].a.attrs['href'].split('/')[-1][:-5]] + [td.text for td in tds[1:]]).reshape((1, -1))
                data = pd.DataFrame(data, columns=cols)
                df = df.append(data.iloc[0])
        df.to_csv('./data/awards/%d_%s_awards_share.csv' % (season, awards[i]), index=False)
