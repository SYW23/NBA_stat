def iter_df(df):
    for i, row in df.iterrows():
        yield [i, row]
