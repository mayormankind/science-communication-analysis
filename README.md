# Science Communication Channels and Public Trust: 68-Country Analysis

**Group 7** — XML/XSD Modelling | XPath/XQuery assessment

Uses the **TISP dataset** (Trust in Science and Science-Related Populism; Mede, Cologna et al., 2025, *Scientific Data* 12:114) — N = 71,922 respondents across 68 countries, collected Nov 2022–Aug 2023. Source: https://osf.io/5c3qd (CC BY 4.0).

## Research Question
How do science communication channels and demographic factors influence public trust in science across cultures?

## Repository Structure
```
data/
  raw/            ds_main.csv (NOT committed — see Data Access below)
  metadata/       data_dictionary.csv (generated)
code/
  inspect_columns.py          # Step 1: see real column names
  generate_data_dictionary.py # Step 2: build the metadata deliverable
  csv_to_xml.py                # Step 3: convert CSV -> schema-conformant XML
  analysis.py                  # Step 4: multi-level model, SEM, choropleth, ANOVA
xml/
  tisp_schema.xsd              # XSD schema for the dataset
  tisp_sample.xml              # Valid sample instance (3 respondents, hand-built)
  tisp_full.xml                # Generated from real data (NOT committed, regenerate locally)
  xpath_xquery_scripts.md      # Required XPath + XQuery scripts, with explanations
manuscript/
  manuscript.txt                # IMRAD manuscript source, 4,000-6,000 words (edit this)
  manuscript.docx / .pdf        # Generated via `pandoc manuscript.txt -o manuscript.docx`
  presentation_script.txt       # ~10-min spoken script for the MP4 recording
figures/
  trust_choropleth.html
  anova_channel_boxplot.png
requirements.txt
```

## Data Access
`ds_main.csv` (~40MB) is not committed to git (see `.gitignore`) — download it yourself from
https://osf.io/5c3qd/files/osfstorage → `01_data/survey-data/ds_main.csv` and place it at
`data/raw/ds_main.csv`. This keeps the repo light and matches the original CC BY 4.0 citation
requirement (we cite/link the source rather than redistribute a copy).

## Reproduction Steps
```bash
pip install -r requirements.txt

# Place ds_main.csv at data/raw/ds_main.csv first (see Data Access above)

# 1. Build the data dictionary
python code/generate_data_dictionary.py data/raw/ds_main.csv data/metadata/data_dictionary.csv

# 2. Convert to XML (3,000-row demo sufficient for XPath/XQuery demonstration)
python code/csv_to_xml.py data/raw/ds_main.csv xml/tisp_full.xml --sample 3000

# 3. Validate XML against XSD (should print True)
python -c "from lxml import etree; s=etree.XMLSchema(etree.parse('xml/tisp_schema.xsd')); print('VALID:', s.validate(etree.parse('xml/tisp_full.xml')))"

# 4. Run all analyses + generate figures
python code/analysis.py data/raw/ds_main.csv
```

## Submission Deliverables Index

| # | Deliverable | Location | Status |
|---|-------------|----------|--------|
| 1 | XSD schema | `xml/tisp_schema.xsd` | Done |
| 2 | XML instance (3,000-row sample) | `xml/tisp_full.xml` | Generated locally |
| 3 | XPath + XQuery scripts with explanations | `xml/xpath_xquery_scripts.md` | Done |
| 4 | Data dictionary CSV | `data/metadata/data_dictionary.csv` | Generated locally |
| 5 | Ethics & provenance note | `data/metadata/ethics_note.md` | Done |
| 6 | Conversion script | `code/csv_to_xml.py` | Done |
| 7 | Analysis script (MLM, SEM, choropleth, ANOVA) | `code/analysis.py` | Done |
| 8 | Choropleth HTML | `figures/trust_choropleth.html` | Generated locally |
| 9 | ANOVA boxplot PNG | `figures/anova_channel_boxplot.png` | Generated locally |
| 10 | Descriptive table CSV | `figures/table1_descriptives.csv` | Generated locally |
| 11 | IMRAD manuscript (4,000+ words, no [[FILL:]] markers) | `manuscript/manuscript.txt` | Done |
| 12 | Presentation script (~1,350 words / ~10 min) | `manuscript/presentation_script.txt` | Done |

## Blockers Encountered and Resolutions

| Blocker | Resolution |
|---------|------------|
| TISP CSV uses `;` delimiter, not `,` | Added `sep=";"` to all `pd.read_csv()` calls |
| Trust/populism/comm_freq are multi-item scales, not single columns | Computed row-wise means of constituent TISP items (TRUST_SCI_*, SCIPOP_*, SCIINFO_*) |
| `primary_channel` is not a raw column | Derived via `idxmax()` across 10 SCIINFO_ frequency columns, mapped to XSD enum values |
| `country_income_group` is not in dataset | Hardcoded World Bank 2022-23 classification lookup dict (68 countries) |
| Gender/residence are numeric codes in the CSV | Mapped to XSD enum strings via lookup dictionaries (GENDER_MAP, RESIDENCE_MAP) |
| European decimal notation (`0,009204000`) causes pandas parse errors | Cleaned via `replace(-99, np.nan)` and `errors="coerce"` on numeric coercions |
| `UnicodeDecodeError` on `pd.read_csv()` — TISP has non-UTF-8 bytes in open-text response columns (Spanish/Arabic characters encoded as Latin-1) | Added `encoding="utf-8-sig", encoding_errors="replace"` to all three scripts: `generate_data_dictionary.py`, `analysis.py`, `csv_to_xml.py` |
| `idxmax()` raises `ValueError: Encountered all NA values` on rows where all 10 SCIINFO_ columns are missing | Added a row-level `notna().any(axis=1)` mask before calling `idxmax()`, assigning `"Other"` to all-NA rows |
| `PerformanceWarning: DataFrame is highly fragmented` on column assignments in `load()` | Refactored `load()` to compute all derived columns as plain Series then assemble them in a single `pd.DataFrame()` constructor call, followed by `.copy()` to defragment |

## Required Analyses (per assessment outline)
1. Multi-level regression — ICC for country-level variance in trust
2. SEM — mediation: communication frequency → knowledge → trust
3. Choropleth — mean trust score by country
4. One-way ANOVA — trust differences by primary communication channel

## XML/XSD Modelling
- `tisp_schema.xsd` models: `Respondent` (id, country, demographics), `Trust_Scale`, `Communication` (channels, frequency), `Climate` (attitudes, policy support), `Populism`, `PoliticalReligious`.
- Required XPath: `//Respondent[Trust_Scale/overall < 3 and Communication/primary='Social Media']` — see `xml/xpath_xquery_scripts.md`.
- Required XQuery: per-country mean trust score + dominant channel — see `xml/xpath_xquery_scripts.md`.

## Authors — Group 7
MAKINDE · MOYINOLUWA · NWACHUKWU · OLAKUNLE · OLORUNFUNMILAYO · OLORUNTOBI · OLUWARANTI

## License
Code: MIT. Data: CC BY 4.0 (TISP, Mede/Cologna et al. 2025) — cite original source, not redistributed here.
