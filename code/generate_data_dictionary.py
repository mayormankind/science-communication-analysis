"""
generate_data_dictionary.py
Builds the metadata / data-dictionary file required by the rubric
(Dataset Acquisition & Documentation, 15%).

USAGE:
    python3 generate_data_dictionary.py path/to/ds_main.csv data/metadata/data_dictionary.csv

Produces a CSV with: column_name, dtype, n_missing, pct_missing, n_unique,
example_values, proposed_role (for our analysis).
"""
import sys
import pandas as pd

def build_dictionary(csv_path, out_path, sep=";"):
    df = pd.read_csv(csv_path, sep=sep, low_memory=False, encoding="utf-8-sig", encoding_errors="replace")
    rows = []
    for col in df.columns:
        s = df[col]
        n_missing = s.isna().sum()
        rows.append({
            "column_name": col,
            "dtype": str(s.dtype),
            "n_missing": n_missing,
            "pct_missing": round(100 * n_missing / len(s), 2),
            "n_unique": s.nunique(dropna=True),
            "example_values": "; ".join(map(str, s.dropna().unique()[:3])),
            "proposed_role": "",  # fill in manually: demographic / trust_item / outcome / etc.
        })
    out = pd.DataFrame(rows)
    out.to_csv(out_path, index=False)
    print(f"Data dictionary written to {out_path} ({len(out)} columns documented).")
    print("\nNext step: open this CSV and fill in 'proposed_role' for each variable")
    print("you actually use in the analysis (leave the rest — TISP has ~200+ columns")
    print("and you only need to document the ~20 you're using in depth).")

if __name__ == "__main__":
    # USAGE: python3 generate_data_dictionary.py ds_main.csv out.csv [sep]
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/ds_main.csv"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "data/metadata/data_dictionary.csv"
    sep = sys.argv[3] if len(sys.argv) > 3 else ";"
    build_dictionary(csv_path, out_path, sep)
