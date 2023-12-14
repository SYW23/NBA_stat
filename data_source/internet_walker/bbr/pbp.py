import os
import argparse
import time

from tqdm import tqdm

import pandas as pd

from data_source.utils.utils import getCode
from config import storage_config, url_config, rof_note
from utils.logger import Logger

logger = Logger.logger


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_season", type=int, default=2009, help="pbp starts from 1996-1997 season")
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


def fetch_player_code_from_url(a):
    return a.attrs['href'].split('/')[-1].rstrip('.html')


def process_single_game(plays):
    game_process = []
    quarter = 0
    cols = None
    for play in plays:
        th_plays = play.find_all('th')
        td_plays = play.find_all('td')
        if len(th_plays) == 1:    # 定位节间
            quarter += 1
        elif cols is None and len(th_plays) == 6:    # 定位表头
            cols = [x.get_text().strip() for x in th_plays]
            cols = ['quarter'] + cols
        elif len(td_plays) == 2 or len(td_plays) == 6:
            assert quarter != 0
            play_record = [quarter]
            # 定位(start/end of quarter or common play or jump ball)
            for p in td_plays:
                aa = p.find_all('a')
                if aa:  # 存在player name，替换为player code
                    sentence_o = p.get_text().strip()
                    for a in aa:
                        if sentence_o == 'Technical foul by':
                            sentence_o = sentence_o + fetch_player_code_from_url(a)
                        elif sentence_o == 'ejected from game':
                            sentence_o = fetch_player_code_from_url(a) + sentence_o
                        elif a.attrs['href'] not in ['/players/T/Team.html', '/players/N/NULL.html']:
                            sentence_o = sentence_o.replace(a.string, fetch_player_code_from_url(a))
                        else:
                            if 'Jump ball' not in sentence_o:
                                logger.info(sentence_o)

                    play_record.append(sentence_o)
                else:
                    play_record.append(p.get_text().strip())
            game_process.append(play_record)
        else:
            if len(td_plays) == 1:
                game_process.append([quarter, td_plays[0].get_text().strip()])
            elif td_plays:
                logger.info([th_plays, td_plays])

    df = pd.DataFrame(game_process)
    df.columns = cols
    return df


def main(arguments):
    for season in range(arguments.start_season + 1, arguments.end_season + 2):
        logger.info('=' * 50)
        season_code = f"{season - 1}_{season}"
        logger.info(f"Starting to record season '{season_code}'!")
        season_dir = os.path.join(storage_config["game_pbp"], f"{season_code}")
        logger.info(f"storing path: {season_dir}")
        initial_dir(season_dir)

        season_summary_regular, season_summary_playoff = [], []
        season_url = f"{url_config['bbr']['league']}/NBA_{season}_games.html"
        season_games = getCode(season_url, 'UTF-8')
        months = season_games.find_all('div', class_='filter')[0].find_all('a')
        month_urls = [url_config['bbr']['root'] + x.attrs['href'] for x in months]
        logger.info(f"The season has {len(month_urls)} months.")

        rof, summary_cols = 0, None
        for index, monthURL in enumerate(month_urls):
            if monthURL == 'https://www.basketball-reference.com/leagues/NBA_2020_games-september.html':
                rof = 1
            # 月份
            logger.info(f"\tstarting to record month {monthURL.split('-')[-1][:3].upper()}")
            month_page = getCode(monthURL, 'UTF-8')
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
                    game_details = [date] + [x.get_text().strip() for x in game_items]
                    if game_details[-1] == "Play-In Game":    # 定位附加赛
                        rof = 1
                    # 判断比赛是否已保存
                    save_file = os.path.join(season_dir, rof_note[rof], f"{date}.csv")
                    if True and arguments.ignore_exists or not os.path.exists(save_file):
                        # 比赛详细过程
                        if not game_items[-5].a:
                            continue
                        try:
                            game_url = f"{url_config['bbr']['pbp']}/{game_items[-5].a.attrs['href'].lstrip('/boxscores')}"
                            game_page = getCode(game_url, 'UTF-8')
                            plays = game_page.find('table', class_='stats_table').find_all('tr')

                            df_game_process = process_single_game(plays)
                            # 保存单场比赛数据
                            df_game_process.to_csv(save_file, index=False)
                            time.sleep(3)
                        except Exception as e:
                            logger.info(f"caught unexpected error: {str(e)}, {game}")
                    # 更新赛季比赛列表
                    if rof:
                        season_summary_playoff.append(game_details)
                    else:
                        season_summary_regular.append(game_details)
                else:
                    ths = game.find_all('th')
                    if len(ths) == 1 and ths[0].get_text().strip() == 'Playoffs':
                        # 找到季后赛分割线
                        logger.info('switch to Playoffs')
                        rof = 1
        regular_df = list_2csv(season_summary_regular, summary_cols)
        playoff_df = list_2csv(season_summary_playoff, summary_cols)
        regular_df.to_csv(os.path.join(season_dir, f"season_summary_{rof_note[0]}.csv"), index=False)
        playoff_df.to_csv(os.path.join(season_dir, f"season_summary_{rof_note[1]}.csv"), index=False)
        print('=' * 50)


def list_2csv(lst, cols):
    df = pd.DataFrame(lst)
    df.columns = cols
    return df


if __name__ == "__main__":
    args = get_args()
    main(args)
