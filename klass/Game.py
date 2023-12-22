from klass.Play import Play







if __name__ == "__main__":
    import os

    import pandas as pd

    from utils.Iteration import iter_df

    season_dir = "/Users/sunyiwu/Documents/personal/stat/stat_data/games/pbp/2022_2023"
    regular_summary = os.path.join(season_dir, "season_summary_regular.csv")
    summary_df = pd.read_csv(regular_summary)

    for i, row in iter_df(summary_df):
        date = row.Date
        game_record = os.path.join(season_dir, "regular", f"{date}.csv")
        game_df = pd.read_csv(game_record)
        for play_index, play_row in iter_df(game_df):
            play = Play(play_row)
            print(play)
            print(play.action_type())
        break

