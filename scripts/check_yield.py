import pandas as pd
try:
    df = pd.read_excel("data/pg_deep.xlsx")
    total = len(df)
    with_mobile = df[df['Mobile'].notna() & (df['Mobile'] != "")].shape[0]
    print(f"Total Rows: {total}")
    print(f"With Mobile: {with_mobile}")
    print(f"Yield: {with_mobile/total*100:.1f}%")
except Exception as e:
    print(e)
