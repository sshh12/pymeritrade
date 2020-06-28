import pandas as pd


def parse_date_cols(df, cols):
    df = df.copy()
    for date_key in cols:
        df[date_key] = pd.to_datetime(df[date_key] * 1000 * 1000)
    return df
