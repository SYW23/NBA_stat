import os
import argparse
import re
import time

from tqdm import tqdm

import pandas as pd

from data_source.utils.code_parser import parse_table
from data_source.utils.utils import get_code
from config import storage_config, url_config, rof_note, boxscore_quarters
from utils.save_and_load import write2pickle
from utils.logger import Logger

logger = Logger.logger


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_season", type=int, default=2016, help="pbp starts from 1996-1997 season")
    parser.add_argument("--end_season", type=int, default=2023)
    parser.add_argument("--ignore_exists", default=False, action="store_true")
    arguments = parser.parse_args()
    return arguments


def initial_dir(season_dir):
    if not os.path.exists(season_dir):
        os.mkdir(season_dir)
    regular_dir = os.path.join(season_dir, "regular")
    if not os.path.exists(regular_dir):
        os.mkdir(regular_dir)
    playoff_dir = os.path.join(season_dir, "playoff")
    if not os.path.exists(playoff_dir):
        os.mkdir(playoff_dir)


def process_single_game(boxscore_page):
    boxscores = []
    scores = boxscore_page.find('div', class_='scorebox')
    teams = [x.a.attrs['href'].split('/')[2] for x in scores.find_all('strong')]  # 客主队
    ss = [int(x.text) for x in scores.find_all('div', class_='score')]  # 比赛最终比分

    wl_re = re.compile('<div>\d+-\d+</div>')
    wl = [x[5:-6] for x in re.findall(wl_re, str(scores))]  # 当场比赛结束后球队战绩
    if not wl:
        wl = ['', '']
    boxscores.append(dict({teams[0]: [ss[0], wl[0]], teams[1]: [ss[1], wl[1]]}))

    for time_range in boxscore_quarters:
        quarter_dfs = []
        for side in range(2):
            table = boxscore_page.find('table', id=f"box-{teams[side]}-{time_range}")
            if not table:
                continue
            df = parse_table(table, eliminate_class="thead")
            quarter_dfs.append(df)
        if quarter_dfs:
            boxscores.append(quarter_dfs)

    return boxscores


def main(arguments):
    for season in range(arguments.start_season + 1, arguments.end_season + 2):
        logger.info('=' * 50)
        season_code = f"{season - 1}_{season}"
        logger.info(f"Starting to record season '{season_code}'!")
        season_dir = os.path.join(storage_config["game_boxscore"], f"{season_code}")
        logger.info(f"storing path: {season_dir}")
        initial_dir(season_dir)

        season_url = f"{url_config['bbr']['league']}/NBA_{season}_games.html"
        season_games = get_code(season_url, 'UTF-8')
        months = season_games.find_all('div', class_='filter')[0].find_all('a')
        month_urls = [url_config['bbr']['root'] + x.attrs['href'] for x in months]
        logger.info(f"The season has {len(month_urls)} months.")

        rof, summary_cols = 0, None
        for index, month_url in enumerate(month_urls):
            if month_url == 'https://www.basketball-reference.com/leagues/NBA_2020_games-september.html':
                rof = 1
            # 月份
            logger.info(f"\tstarting to record month {month_url.split('/')[-1].split('-')[1][:3].upper()}")
            month_page = get_code(month_url, 'UTF-8')
            game_table = month_page.find('table', class_='stats_table').find_all('tr')
            titles, game_table = game_table[0], game_table[1:]

            summary_cols = [x.get_text().strip() for x in titles.find_all('th')]
            n_summary_cols = len(summary_cols)

            for game in tqdm(game_table):
                game_items = game.find_all('td')
                # %%
                if len(game_items) > 0:
                    assert len(game_items) == n_summary_cols - 1
                    # 比赛基本信息
                    date = game.find_all('th')[0].attrs['csk']
                    play_in = game_items[-1].get_text().strip()
                    if play_in == "Play-In Game":    # 定位附加赛
                        if not rof:
                            logger.info('switch to Playoffs')
                            rof = 1
                    # 判断比赛是否已保存
                    save_file = os.path.join(season_dir, rof_note[rof], f"{date}.pkl")
                    if True and arguments.ignore_exists or not os.path.exists(save_file):
                        # 比赛详细过程
                        if not game_items[-5].a:
                            continue
                        try:
                            boxscore_url = f"{url_config['bbr']['root']}{game_items[-5].a.attrs['href']}"
                            boxscore_page = get_code(boxscore_url, 'UTF-8')

                            boxscores = process_single_game(boxscore_page)
                            write2pickle(save_file, boxscores)
                            # 保存单场比赛数据
                            time.sleep(2)
                        except Exception as e:
                            logger.info(f"caught unexpected error: {str(e)}, {game}")
                else:
                    ths = game.find_all('th')
                    if len(ths) == 1 and ths[0].get_text().strip() == 'Playoffs':
                        # 找到季后赛分割线
                        logger.info('switch to Playoffs')
                        rof = 1
        print('=' * 50)


def list_2csv(lst, cols):
    df = pd.DataFrame(lst)
    df.columns = cols
    return df


if __name__ == "__main__":
    args = get_args()
    main(args)
