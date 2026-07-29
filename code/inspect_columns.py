"""Run this FIRST the moment ds_main.csv lands. Auto-detects the real delimiter
(TISP, from a European R-based consortium, commonly ships semicolon-delimited
CSVs rather than comma-delimited) instead of crashing on a hardcoded comma."""
import sys
import csv
import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else "ds_main.csv"

# --- Step 1: show the raw bytes of the first 3 lines so we can SEE the real structure ---
print("=== Raw first 3 lines (look at what separates fields) ===")
with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
    for i, line in enumerate(f):
        if i >= 3:
            break
        print(f"Line {i}: {line[:300]!r}")

# --- Step 2: sniff the delimiter ---
with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
    sample = f.read(8192)
try:
    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    detected_sep = dialect.delimiter
    print(f"\n=== csv.Sniffer detected delimiter: {detected_sep!r} ===")
except csv.Error:
    detected_sep = None
    print("\n=== csv.Sniffer could not detect a delimiter — will try candidates manually ===")

# --- Step 3: try candidates in order, report which one actually works ---
candidates = [detected_sep, ",", ";", "\t", "|"]
candidates = [c for c in dict.fromkeys(candidates) if c]  # dedupe, drop None

df = None
used_sep = None
for sep in candidates:
    try:
        test = pd.read_csv(path, sep=sep, nrows=5, engine="python", on_bad_lines="warn")
        if test.shape[1] > 1:  # more than one column = real delimiter found
            df = pd.read_csv(path, sep=sep, nrows=500, engine="python", on_bad_lines="warn", encoding="utf-8-sig")
            used_sep = sep
            break
    except Exception as e:
        print(f"  sep={sep!r} failed: {e}")

if df is None:
    print("\nCould not auto-parse with any candidate delimiter.")
    print("Paste the 'Raw first 3 lines' output above back to Claude — the exact")
    print("character between fields will be visible there even if this script can't detect it.")
    sys.exit(1)

print(f"\n=== SUCCESS with separator {used_sep!r} ===")
print(f"Shape (first 500 rows read): {df.shape}")
print(f"\nAll {len(df.columns)} columns:")
for c in df.columns:
    print(" -", c)

print("\nLikely key columns (containing keywords):")
keywords = ["country", "trust", "populis", "gender", "age", "educ", "channel",
            "media", "climate", "polic", "polit", "relig", "income", "id", "weight"]
for kw in keywords:
    matches = [c for c in df.columns if kw.lower() in c.lower()]
    if matches:
        print(f"  [{kw}] -> {matches}")

print(f"\n>>> IMPORTANT: use sep={used_sep!r} in csv_to_xml.py and analysis.py's")
print(">>> pd.read_csv() calls too — update the load()/convert() functions in both.")

# --- Step 4: check for comma-as-decimal-separator (common alongside semicolon delimiters) ---
if used_sep != ",":
    import re
    decimal_comma_hits = 0
    checked = 0
    for col in df.columns:
        sample_vals = df[col].dropna().astype(str).head(20)
        for v in sample_vals:
            checked += 1
            if re.fullmatch(r"-?\d+,\d+", v.strip()):
                decimal_comma_hits += 1
    if checked and decimal_comma_hits / checked > 0.05:
        print(f"\n>>> WARNING: detected comma-as-decimal-separator values (e.g. '3,2' instead of '3.2').")
        print(f">>> Add decimal=',' to every pd.read_csv() call, or pass --decimal ',' to csv_to_xml.py/analysis.py.")
