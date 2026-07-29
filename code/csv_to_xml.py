"""
csv_to_xml.py
Converts ds_main.csv (TISP dataset) into XML conforming to tisp_schema.xsd.

USAGE:
    python csv_to_xml.py data/raw/ds_main.csv xml/tisp_full.xml [--sample 3000]

Real ds_main.csv uses semicolon (;) delimiter.
Composite scores (trust, comm_freq, populism) are computed from their
constituent TISP items before writing to XML.
"""
import sys
import argparse
import numpy as np
import pandas as pd
from xml.sax.saxutils import escape

# ---------- Item lists (real TISP column names) ----------
TRUST_SCI_ITEMS = [
    "TRUST_SCI_expert", "TRUST_SCI_honest", "TRUST_SCI_concerned",
    "TRUST_SCI_open", "TRUST_SCI_intellig", "TRUST_SCI_ethical",
    "TRUST_SCI_improve", "TRUST_SCI_trans", "TRUST_SCI_qualified",
    "TRUST_SCI_sincere", "TRUST_SCI_otherint", "TRUST_SCI_otherviews",
]

SCIPOP_ITEMS = [
    "SCIPOP_common", "SCIPOP_good", "SCIPOP_advantage", "SCIPOP_cahoots",
    "SCIPOP_influence", "SCIPOP_involved", "SCIPOP_lifeexp", "SCIPOP_rely",
]

SCIINFO_COLS = [
    "SCIINFO_newspapersmags", "SCIINFO_tvradio", "SCIINFO_newswebsitesapps",
    "SCIINFO_videospodcasts", "SCIINFO_filmsseries", "SCIINFO_books",
    "SCIINFO_socialmedia", "SCIINFO_messengers", "SCIINFO_museumszoos",
    "SCIINFO_rlconversations",
]

SCIINFO_CHANNEL_NAMES = {
    "SCIINFO_newspapersmags":   "Newspapers",
    "SCIINFO_tvradio":          "Television",
    "SCIINFO_newswebsitesapps": "Online News Sites",
    "SCIINFO_videospodcasts":   "Other",
    "SCIINFO_filmsseries":      "Other",
    "SCIINFO_books":            "Scientific Journals",
    "SCIINFO_socialmedia":      "Social Media",
    "SCIINFO_messengers":       "Family/Friends",
    "SCIINFO_museumszoos":      "Other",
    "SCIINFO_rlconversations":  "Family/Friends",
}

CLIM_POLSUPPORT_ITEMS = [
    "CLIM_POLSUPPORT_fueltax", "CLIM_POLSUPPORT_publictransport",
    "CLIM_POLSUPPORT_sustenergy", "CLIM_POLSUPPORT_protection",
    "CLIM_POLSUPPORT_foodtax",
]

GENDER_MAP = {1: "male", 2: "female", 3: "other", 4: "prefer_not_to_say"}

RESIDENCE_MAP = {1: "urban", 2: "urban", 3: "suburban", 4: "rural", 5: "rural"}

COUNTRY_INCOME_MAP = {
    "ALB": "upper_middle_income", "ARG": "upper_middle_income",
    "AUS": "high_income",         "AUT": "high_income",
    "BEL": "high_income",         "BGD": "lower_middle_income",
    "BRA": "upper_middle_income", "CAN": "high_income",
    "CHE": "high_income",         "CHL": "upper_middle_income",
    "CHN": "upper_middle_income", "COL": "upper_middle_income",
    "CZE": "high_income",         "DEU": "high_income",
    "DNK": "high_income",         "EGY": "lower_middle_income",
    "ESP": "high_income",         "ETH": "low_income",
    "FIN": "high_income",         "FRA": "high_income",
    "GBR": "high_income",         "GHA": "lower_middle_income",
    "GRC": "high_income",         "HUN": "high_income",
    "IDN": "lower_middle_income", "IND": "lower_middle_income",
    "IRL": "high_income",         "IRN": "lower_middle_income",
    "ISR": "high_income",         "ITA": "high_income",
    "JPN": "high_income",         "KEN": "lower_middle_income",
    "KOR": "high_income",         "MAR": "lower_middle_income",
    "MEX": "upper_middle_income", "MYS": "upper_middle_income",
    "NGA": "lower_middle_income", "NLD": "high_income",
    "NOR": "high_income",         "NZL": "high_income",
    "PAK": "lower_middle_income", "PHL": "lower_middle_income",
    "POL": "high_income",         "PRT": "high_income",
    "ROU": "upper_middle_income", "RUS": "upper_middle_income",
    "SAU": "high_income",         "SEN": "lower_middle_income",
    "SGP": "high_income",         "SRB": "upper_middle_income",
    "SVK": "high_income",         "SVN": "high_income",
    "SWE": "high_income",         "THA": "upper_middle_income",
    "TUR": "upper_middle_income", "TZA": "low_income",
    "UGA": "low_income",          "UKR": "lower_middle_income",
    "URY": "high_income",         "USA": "high_income",
    "VNM": "lower_middle_income", "ZAF": "upper_middle_income",
    "ZMB": "lower_middle_income", "BWA": "upper_middle_income",
    "CMR": "lower_middle_income", "ECU": "upper_middle_income",
    "PER": "upper_middle_income", "CIV": "lower_middle_income",
}


def clamp_likert(val, default="3.00"):
    """Convert a value to a clamped [1, 5] decimal string for XSD LikertScoreType."""
    try:
        f = float(str(val).replace(",", "."))
        if np.isnan(f) or f < 0:
            return default
        return f"{max(1.0, min(5.0, f)):.2f}"
    except Exception:
        return default


def row_mean(row, cols, default="3.00"):
    """Compute mean of named columns for one row dict, clamped to [1, 5]."""
    vals = []
    for c in cols:
        try:
            v = float(str(row.get(c, "")).replace(",", "."))
            if not np.isnan(v) and v >= 1:
                vals.append(v)
        except Exception:
            pass
    return clamp_likert(np.mean(vals)) if vals else default


def map_gender(val):
    try:
        return GENDER_MAP.get(int(float(str(val))), "other")
    except Exception:
        return "other"


def map_residence(val):
    try:
        return RESIDENCE_MAP.get(int(float(str(val))), "urban")
    except Exception:
        return "urban"


def get_primary_channel(row, sciinfo_present):
    best_val, best_col = -1, None
    for c in sciinfo_present:
        try:
            v = float(str(row.get(c, "")).replace(",", "."))
            if v > best_val:
                best_val, best_col = v, c
        except Exception:
            pass
    return SCIINFO_CHANNEL_NAMES.get(best_col, "Other") if best_col else "Other"


def convert(in_path, out_path, sample=None):
    df = pd.read_csv(in_path, sep=";", low_memory=False, encoding="utf-8-sig", encoding_errors="replace")
    df = df.replace(-99, np.nan).replace("-99", np.nan)
    if sample:
        df = df.head(sample)

    sciinfo_present = [c for c in SCIINFO_COLS if c in df.columns]
    trust_present   = [c for c in TRUST_SCI_ITEMS if c in df.columns]
    scipop_present  = [c for c in SCIPOP_ITEMS if c in df.columns]
    clim_present    = [c for c in CLIM_POLSUPPORT_ITEMS if c in df.columns]

    rows = df.to_dict("records")

    with open(out_path, "w", encoding="utf-8") as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write('<tisp:TISP_Dataset xmlns:tisp="http://group7.tisp.org/schema">\n')
        out.write("  <tisp:Metadata>\n")
        out.write("    <tisp:DatasetName>TISP: Trust in Science and Science-Related Populism</tisp:DatasetName>\n")
        out.write("    <tisp:SourceCitation>Mede, N. G., Cologna, V., et al. (2025). Scientific Data, 12, 114.</tisp:SourceCitation>\n")
        out.write("    <tisp:CollectionPeriod><tisp:Start>2022-11</tisp:Start><tisp:End>2023-08</tisp:End></tisp:CollectionPeriod>\n")
        out.write(f"    <tisp:SampleSize>{len(rows)}</tisp:SampleSize>\n")
        out.write("    <tisp:CountryCount>68</tisp:CountryCount>\n")
        out.write("    <tisp:License>CC BY 4.0</tisp:License>\n")
        out.write("    <tisp:Repository>https://osf.io/5c3qd</tisp:Repository>\n")
        out.write("  </tisp:Metadata>\n")
        out.write("  <tisp:Respondents>\n")

        for row in rows:
            _id_val = (row.get("ID_QUALTRICS") or row.get("ResponseId") or
                       row.get("id") or row.get("ID") or "UNKNOWN")
            rid     = escape(str(_id_val))
            country = escape(str(row.get("COUNTRY_CODE", "UNK") or "UNK").strip())
            gender  = map_gender(row.get("DEM_GENDER", ""))
            age_grp = escape(str(row.get("DEM_AGEGRP", "") or ""))
            edu     = escape(str(row.get("DEM_EDU", "") or ""))
            residence     = map_residence(row.get("DEM_RESIDENCE", ""))
            income_grp    = escape(str(row.get("DEM_INCOME", "") or ""))
            country_income = COUNTRY_INCOME_MAP.get(country, "upper_middle_income")
            trust_mean  = row_mean(row, trust_present)
            popul_mean  = row_mean(row, scipop_present)
            comm_freq   = row_mean(row, sciinfo_present)
            sci_know    = clamp_likert(row.get("TRUST_METHOD", "3"), "3.00")
            primary     = get_primary_channel(row, sciinfo_present)
            clim_att    = clamp_likert(row.get("CLIM_TRUST", "3"), "3.00")
            clim_pol    = row_mean(row, clim_present)
            pol_align   = escape(str(row.get("DEM_POL_right", "") or ""))
            religiosity = clamp_likert(row.get("DEM_RELIGIOUS", "3"), "3.00")

            out.write(f'    <tisp:Respondent id="{rid}" country="{country}">\n')
            out.write("      <tisp:Demographics>\n")
            out.write(f"        <tisp:Gender>{gender}</tisp:Gender>\n")
            out.write(f"        <tisp:AgeGroup>{age_grp}</tisp:AgeGroup>\n")
            out.write(f"        <tisp:Education>{edu}</tisp:Education>\n")
            out.write(f"        <tisp:Residence>{residence}</tisp:Residence>\n")
            out.write(f"        <tisp:IncomeGroup>{income_grp}</tisp:IncomeGroup>\n")
            out.write(f"        <tisp:CountryIncomeGroup>{country_income}</tisp:CountryIncomeGroup>\n")
            out.write("      </tisp:Demographics>\n")
            out.write(f"      <tisp:Trust_Scale><tisp:overall>{trust_mean}</tisp:overall></tisp:Trust_Scale>\n")
            out.write(f"      <tisp:Populism><tisp:overall>{popul_mean}</tisp:overall></tisp:Populism>\n")
            out.write("      <tisp:Communication>\n")
            out.write(f"        <tisp:Channel><tisp:name>{primary}</tisp:name><tisp:usageFrequency>{comm_freq}</tisp:usageFrequency></tisp:Channel>\n")
            out.write(f"        <tisp:primary>{primary}</tisp:primary>\n")
            out.write(f"        <tisp:frequency>{comm_freq}</tisp:frequency>\n")
            out.write(f"        <tisp:scienceKnowledge>{sci_know}</tisp:scienceKnowledge>\n")
            out.write("      </tisp:Communication>\n")
            out.write("      <tisp:Climate>\n")
            out.write(f"        <tisp:attitude>{clim_att}</tisp:attitude>\n")
            out.write(f"        <tisp:policySupport>{clim_pol}</tisp:policySupport>\n")
            out.write("      </tisp:Climate>\n")
            out.write("      <tisp:PoliticalReligious>\n")
            out.write(f"        <tisp:politicalAlignment>{pol_align}</tisp:politicalAlignment>\n")
            out.write(f"        <tisp:religiosity>{religiosity}</tisp:religiosity>\n")
            out.write("      </tisp:PoliticalReligious>\n")
            out.write("    </tisp:Respondent>\n")

        out.write("  </tisp:Respondents>\n")
        out.write("</tisp:TISP_Dataset>\n")

    print(f"Wrote {len(rows)} respondents to {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("xml_path")
    ap.add_argument("--sample", type=int, default=None,
                    help="Limit to first N rows (3000 recommended for schema demo)")
    args = ap.parse_args()
    convert(args.csv_path, args.xml_path, args.sample)
