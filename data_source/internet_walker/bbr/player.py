import os
import time

from bs4 import BeautifulSoup, Comment
from tqdm import tqdm

import pandas as pd

from config.urls import url_config
from config import player_homepage_table_names, storage_config, gamelog_titles
from data_source.utils.code_parser import parse_table
from data_source.utils.utils import get_code
from utils.logger import Logger

logger = Logger.logger


# todo: update logic (only update those of players which may have updates)


def match_titles(df):
    ori_cols = list(df.columns)
    for gamelog_title in gamelog_titles:
        if len(ori_cols) == len(gamelog_title):
            df.columns = gamelog_title
            return df
    logger.info(f"No matched gamelog_title, length={len(ori_cols)}: {ori_cols}")


def concat_dfs(summary_df, df):
    df = match_titles(df)
    if summary_df is None:
        summary_df = df
    else:
        old_cols = list(summary_df.columns)
        new_cols = list(df.columns)

        if len(old_cols) != len(new_cols):
            if len(old_cols) < len(new_cols):
                additions = set(new_cols) - set(old_cols)
                for addition in additions:
                    summary_df[addition] = float('nan')
                summary_df = summary_df[new_cols]
            else:
                additions = set(old_cols) - set(new_cols)
                for addition in additions:
                    df[addition] = float('nan')
                df = df[old_cols]

        summary_df = pd.concat([summary_df, df])
    return summary_df


def main():
    letters = [chr(x) for x in range(97, 123)]    # 【a-z】
    letters.pop(23)    # no name starts with 'x'

    start_with_letter = 0
    for index, letter in enumerate(letters):
        if index < start_with_letter:
            continue
        # first letter of player name
        letter_url = f"{url_config['bbr']['player']}/{letter}"
        letter_page = get_code(letter_url, 'UTF-8')
        letter_players = letter_page.find('table', class_='stats_table').find_all('tr')
        letter_player_cols, letter_players = letter_players[0], letter_players[1:]
        letter_player_cols = [x.text for x in letter_player_cols.find_all('th')]

        start_with = 0
        for ix, letter_player_row in tqdm(enumerate(letter_players)):
            if ix < start_with:
                continue
            player_basic_inf = letter_player_row.find_all('td')
            if len(player_basic_inf) > 0:
                # player name
                player = letter_player_row.find_all('th')[0].a.text
                logger.info(f"============ {index:02d}/{len(letters)}/{letter} | {ix:03d}/{len(letter_players)}/{player} ============")
                player_url = f"{url_config['bbr']['root']}{letter_player_row.find_all('th')[0].a.attrs['href']}"
                player_page = get_code(player_url, 'UTF-8')

                player_code = player_url.split('/')[-1][:-5]
                player_basic_infs = [player] + [x.get_text().strip() for x in player_basic_inf]

                # storage
                player_folder = os.path.join(storage_config["game_player_inf"], player_code[1:3], player_code)
                os.makedirs(player_folder, exist_ok=True)
                df = pd.DataFrame([player_basic_infs])
                df.columns = letter_player_cols
                df.to_csv(os.path.join(player_folder, "basic_inf.csv"), index=False)

                # 球员主页所有表格整理
                regular_seasons, playoff_seasons = [], []
                for table_name in player_homepage_table_names:
                    tables_level = player_page.find_all('div', id=table_name)
                    if tables_level:
                        tables_level = tables_level[0]
                    else:
                        continue
                    tables = tables_level.find_all('table')
                    if not tables:
                        comments = tables_level.find_all(text=lambda text: isinstance(text, Comment))
                        reformat = BeautifulSoup(comments[0], "html.parser")
                        tables = reformat.find_all('table')

                    for table in tables:
                        try:
                            table_id = table.get('id')
                            if table_id in ["per_game", "playoffs_per_game"]:
                                first_cols, df = parse_table(table, return_first_cols=True)
                                if table_id == "per_game":
                                    regular_seasons = first_cols
                                else:
                                    playoff_seasons = first_cols
                            else:
                                df = parse_table(table)
                            if df is not None:
                                df.to_csv(os.path.join(player_folder, f"{table_id}.csv"), index=False)
                        except Exception as e:
                            logger.info(f"Caught error whiling parsing tabel {table_id}: {str(e)}")
                            raise KeyError

                # 球员所有赛季每场比赛技术统计整理
                all_seasons = sorted(list(set(regular_seasons) | set(playoff_seasons)))
                logger.info(f"career seasons: {len(all_seasons)}, regular seasons: {len(regular_seasons)}, playoff seasons: {len(playoff_seasons)}")
                regular_games_df, playoff_games_df = None, None
                for season in all_seasons:
                    if season.endswith("/aba/"):
                        continue
                    logger.info(f"season: {int(season.split('/')[-1]) - 1}-{season.split('/')[-1]}")
                    season_url = f"{url_config['bbr']['root']}{season}"
                    season_page = get_code(season_url, 'UTF-8')

                    tables_level = season_page.find_all('div', class_='table_wrapper')
                    for ind, table_level in enumerate(tables_level):
                        if len(tables_level) == 2 and ind == 0 and season not in regular_seasons:
                            continue    # 该赛季常规赛全部缺席，跳过
                        if len(tables_level) == 2 and ind == 1 and season not in playoff_seasons:
                            continue    # 该赛季季后赛全部缺席，跳过
                        table_id = table_level.get('id')
                        table = table_level.find_all('table')
                        if not table:
                            comments = table_level.find_all(text=lambda text: isinstance(text, Comment))
                            reformat = BeautifulSoup(comments[0], "html.parser")
                            table = reformat.find_all('table')[0]
                        else:
                            table = table[0]
                        df = parse_table(table, eliminate_class="thead")
                        if "playoffs" in table_id:
                            playoff_games_df = concat_dfs(playoff_games_df, df)
                        else:
                            regular_games_df = concat_dfs(regular_games_df, df)

                    time.sleep(2)
                if regular_games_df is not None:
                    regular_games_df.to_csv(os.path.join(player_folder, "regular_games.csv"), index=False)
                if playoff_games_df is not None:
                    playoff_games_df.to_csv(os.path.join(player_folder, "playoff_games.csv"), index=False)


if __name__ == "__main__":
    main()
