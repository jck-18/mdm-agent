import pandas as pd
from pathlib import Path

def load_csvs(data_dir="data"):
    records = []
    for csv_file in Path(data_dir).glob("*.csv"):
        df = pd.read_csv(csv_file)
        for _, row in df.iterrows():
            records.append({
                "attribute": row["attribute"],
                "variant": row["variant"],
                "value": row["value"]
            })
    return records

if __name__ == "__main__":
    data = load_csvs()
    print(data[:5])  # sample output
