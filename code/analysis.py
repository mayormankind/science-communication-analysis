"""
analysis.py — Group 7: Science Communication Channels and Public Trust
Required Analyses (per assessment outline):
  1. Multi-level regression: ICC for country-level variance in trust
  2. SEM: mediation (comm. frequency -> knowledge -> trust)
  3. Geographic visualisation: choropleth of trust scores
  4. ANOVA: trust differences by primary information source

COLUMN NOTES (real ds_main.csv, sep=';'):
  Trust in scientists  : mean of TRUST_SCI_* (12 items, 1-5 Likert)
  Science knowledge    : TRUST_METHOD (trust in the scientific method — proxy)
  Comm. frequency      : mean of SCIINFO_* (10 channel-frequency items)
  Primary channel      : column with highest per-row SCIINFO_ score
  Country income group : World Bank classification (hardcoded lookup dict)
"""
import sys
import os
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

def load(path):
    df = pd.read_csv(path, sep=";", low_memory=False, encoding="utf-8-sig", encoding_errors="replace")
    df = df.replace(-99, np.nan).replace("-99", np.nan)

    # --- Trust in scientists: 12-item Likert mean ---
    trust_present = [c for c in TRUST_SCI_ITEMS if c in df.columns]
    df[trust_present] = df[trust_present].apply(pd.to_numeric, errors="coerce")
    trust_scores = df[trust_present].mean(axis=1)

    # --- Science knowledge proxy: TRUST_METHOD (single item, 1-5) ---
    knowledge = pd.to_numeric(df["TRUST_METHOD"], errors="coerce") if "TRUST_METHOD" in df.columns else pd.Series(np.nan, index=df.index)

    # --- Communication frequency: mean of 10 SCIINFO_ items ---
    sciinfo_present = [c for c in SCIINFO_COLS if c in df.columns]
    df[sciinfo_present] = df[sciinfo_present].apply(pd.to_numeric, errors="coerce")
    comm_freq = df[sciinfo_present].mean(axis=1)

    # --- Primary channel: SCIINFO_ column with highest per-row score ---
    # Handle rows where all SCIINFO values are NA (idxmax would raise ValueError)
    sciinfo_df = df[sciinfo_present].copy()
    has_any = sciinfo_df.notna().any(axis=1)
    argmax_col = pd.Series(index=df.index, dtype=object)
    if has_any.any():
        argmax_col[has_any] = sciinfo_df.loc[has_any].idxmax(axis=1)
    primary_channel = argmax_col.map(SCIINFO_CHANNEL_NAMES).fillna("Other")

    # --- Country code ---
    country = df["COUNTRY_CODE"].astype(str).str.strip()

    # --- Country income group (World Bank 2022-23 classification) ---
    country_income_group = country.map(COUNTRY_INCOME_MAP).fillna("upper_middle_income")

    # --- Climate policy support: mean of 5 items ---
    clim_present = [c for c in CLIM_POLSUPPORT_ITEMS if c in df.columns]
    df[clim_present] = df[clim_present].apply(pd.to_numeric, errors="coerce")
    climate_policy = df[clim_present].mean(axis=1)

    # Assemble analytic columns into a clean DataFrame (avoids fragmentation warning)
    analytic_df = pd.DataFrame({
        "trust": trust_scores,
        "knowledge": knowledge,
        "comm_freq": comm_freq,
        "primary_channel": primary_channel,
        "country": country,
        "country_income_group": country_income_group,
        "climate_policy": climate_policy,
    })

    analytic = analytic_df.dropna(subset=["trust", "country", "comm_freq", "knowledge"])
    print(f"Total rows loaded: {len(df)}")
    print(f"Analytic sample (non-missing trust/comm_freq/knowledge): {len(analytic)}")
    print(f"Countries represented: {analytic['country'].nunique()}")
    return analytic


# ---------- 1. Multi-level model + ICC ----------
def multilevel_model(df):
    model = smf.mixedlm("trust ~ comm_freq + knowledge", df, groups=df["country"])
    result = model.fit(reml=True)
    var_country = float(result.cov_re.iloc[0, 0])
    var_resid = float(result.scale)
    icc = var_country / (var_country + var_resid)
    print("\n=== Multi-level model (trust ~ comm_freq + knowledge, random intercept: country) ===")
    print(result.summary())
    print(f"\nICC (country-level variance share) = {icc:.3f}")
    return result, icc


# ---------- 2. SEM mediation ----------
def sem_mediation(df):
    try:
        from semopy import Model
    except ImportError:
        print("semopy not installed — run: pip install semopy --break-system-packages")
        return None
    desc = """
    knowledge ~ comm_freq
    trust ~ knowledge + comm_freq
    """
    model = Model(desc)
    model.fit(df[["comm_freq", "knowledge", "trust"]].dropna())
    est = model.inspect()
    print("\n=== SEM mediation (comm_freq -> knowledge -> trust) ===")
    print(est)

    try:
        a = est.loc[(est["lval"] == "knowledge") & (est["rval"] == "comm_freq"), "Estimate"].values[0]
        b = est.loc[(est["lval"] == "trust") & (est["rval"] == "knowledge"), "Estimate"].values[0]
        c_direct = est.loc[(est["lval"] == "trust") & (est["rval"] == "comm_freq"), "Estimate"].values[0]
        indirect = a * b
        print(f"\nPath a (comm_freq->knowledge) = {a:.4f}")
        print(f"Path b (knowledge->trust)     = {b:.4f}")
        print(f"Direct effect c'              = {c_direct:.4f}")
        print(f"Indirect effect a*b           = {indirect:.4f}")
        print(f"Total effect                  = {c_direct + indirect:.4f}")
    except (IndexError, KeyError) as e:
        print(f"Could not extract path coefficients: {e}")
        a = b = c_direct = indirect = None
    return est, a, b, c_direct, indirect


# ---------- 3. Choropleth ----------
def choropleth(df, out_html="figures/trust_choropleth.html"):
    import plotly.express as px
    os.makedirs("figures", exist_ok=True)
    country_means = df.groupby("country", as_index=False)["trust"].mean()
    country_means.columns = ["country", "mean_trust"]
    fig = px.choropleth(
        country_means, locations="country", color="mean_trust",
        color_continuous_scale="RdYlBu",
        locationmode="ISO-3",
        title="Mean Trust in Scientists by Country (TISP, N=71,922, 68 Countries)",
        labels={"mean_trust": "Mean Trust (1-5)"},
    )
    fig.write_html(out_html)
    print(f"\nChoropleth written to {out_html}")
    print("\nTop 10 highest-trust countries:")
    print(country_means.sort_values("mean_trust", ascending=False).head(10).to_string(index=False))
    print("\nBottom 10 lowest-trust countries:")
    print(country_means.sort_values("mean_trust").head(10).to_string(index=False))
    return country_means


# ---------- 4. ANOVA ----------
def anova_by_channel(df):
    groups = [g["trust"].dropna().values for _, g in df.groupby("primary_channel")]
    groups = [g for g in groups if len(g) > 1]
    f_stat, p_val = stats.f_oneway(*groups)
    print("\n=== One-way ANOVA: trust ~ primary_channel ===")
    print(f"F = {f_stat:.3f}, p = {p_val:.4g}")
    print("\nGroup means:")
    print(df.groupby("primary_channel")["trust"].agg(["mean", "count"]).to_string())

    os.makedirs("figures", exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    df.boxplot(column="trust", by="primary_channel", ax=ax, rot=35)
    plt.title("Trust in Scientists by Primary Communication Channel")
    plt.suptitle("")
    plt.tight_layout()
    plt.savefig("figures/anova_channel_boxplot.png", dpi=150)
    print("Boxplot saved to figures/anova_channel_boxplot.png")
    return f_stat, p_val


# ---------- 5. Descriptive table by income group ----------
def descriptives_by_income(df):
    os.makedirs("figures", exist_ok=True)
    tbl = df.groupby("country_income_group")["trust"].describe().round(3)
    tbl.to_csv("figures/table1_descriptives.csv")
    print("\n=== Table 1 - Trust descriptives by country income group ===")
    print(tbl.to_string())
    print("Saved to figures/table1_descriptives.csv")
    return tbl


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/ds_main.csv"
    df = load(path)

    print(f"\nPrimary channel distribution:\n{df['primary_channel'].value_counts().to_string()}")
    print(f"\nCountry income group distribution:\n{df['country_income_group'].value_counts().to_string()}")

    multilevel_model(df)
    sem_mediation(df)
    choropleth(df)
    anova_by_channel(df)
    descriptives_by_income(df)
