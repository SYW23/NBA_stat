from bs4 import BeautifulSoup, Comment

from tqdm import tqdm

import pandas as pd

from config.urls import url_config
from config import player_homepage_table_names, storage_config
from data_source.utils.utils import get_code


def parse_table(table):
    table_titles = table.find_all('thead')[0]
    table_heads = table_titles.find_all('tr')[-1]
    cols = [x.text for x in table_heads.find_all('th')]
    # print(cols, len(cols))

    contents = []
    table_rows = table.find_all('tbody')[0]
    table_rows = table_rows.find_all('tr')
    for table_row in table_rows:
        first_col = table_row.find_all('th')[0]
        first_item = [first_col.text]

        table_items = table_row.find_all('td')
        contents.append(first_item + [x.text for x in table_items])

    df = pd.DataFrame(contents)
    df.columns = cols
    return df


def main():
    letters = [chr(x) for x in range(97, 123)]
    letters.pop(23)

    for index, letter in enumerate(letters[9:10]):
        # 首字母URL
        letter_url = f"{url_config['bbr']['player']}/{letter}"
        letter_page = get_code(letter_url, 'UTF-8')
        letter_player_rows = letter_page.find('table', class_='stats_table').find_all('tr')[1:]

        for ix, letter_player_row in tqdm(enumerate(letter_player_rows[52:53])):
            player_basic_inf = letter_player_row.find_all('td')
            if len(player_basic_inf) > 0:
                # player name
                player = letter_player_row.find_all('th')[0].a.text
                player_url = f"{url_config['bbr']['root']}{letter_player_row.find_all('th')[0].a.attrs['href']}"
                player_page = get_code(player_url, 'UTF-8')

                player_code = player_url.split('/')[-1][:-5]
                player_basic_infs = [player] + [x.get_text().strip() for x in player_basic_inf]
                print(player_basic_infs)
                last_season = int(player_basic_infs[2])
                print(last_season)

                dfs = {}
                for table_name in player_homepage_table_names:
                    tables_level = player_page.find_all('div', id=table_name)[0]
                    tables = tables_level.find_all('table')
                    if not tables:
                        comments = tables_level.find_all(text=lambda text: isinstance(text, Comment))
                        reformat = BeautifulSoup(comments[0], "html.parser")
                        tables = reformat.find_all('table')

                    for table in tables:
                        table_id = table.get('id')
                        df = parse_table(table)
                        dfs[table_id] = df
                print(len(dfs))



                # player_page = get_code(player_url, 'UTF-8')
                # seasons = player_page.find('table', id='per_game').find_all('tr')
                # season_titles, seasons = seasons[0], seasons[1:]
                # season_titles = [x.text for x in season_titles.find_all('th')]
                # print(season_titles)
                #
                # for ind, season in enumerate(seasons):
                #     if season.find_all('th'):
                #         th = season.find_all('th')[0]
                #         print(th)
                #     else:
                #         continue

            break
        break


if __name__ == "__main__":
    main()
