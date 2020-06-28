import pandas as pd
import re


def parse_date_cols(df, cols):
    df = df.copy()
    for date_key in cols:
        df[date_key] = pd.to_datetime(df[date_key] * 1000 * 1000)
    return df


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def clean_col_names(df):
    col_map = {col: camel_to_snake(col.replace("InLong", "")) for col in df.columns}
    return df.rename(columns=col_map)
