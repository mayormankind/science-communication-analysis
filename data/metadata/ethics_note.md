# Ethics and Data Provenance Note

## Dataset
**Name:** TISP — Trust in Science and Science-Related Populism  
**Version used:** ds_main.csv (cleaned, cross-national wave)  
**N:** 71,922 respondents | **Countries:** 68  

## Source Citation
Mede, N. G., Cologna, V., Schäfer, M. S., Besley, J., Guenther, L., Linden, S. van der,
... & Zollo, F. (2025). TISP: A cross-national dataset on trust in science and
science-related populism. *Scientific Data*, 12, 114.
https://doi.org/10.1038/s41597-025-04491-3

## Repository
OSF: https://osf.io/5c3qd  
The dataset is publicly archived under a **CC BY 4.0** licence; redistribution
requires attribution to the original authors.

## Ethical Compliance
- **Survey ethics:** Data were collected by the TISP consortium under national
  IRB/ethics board approvals in each participating country (2022–2023). Participation
  was voluntary and informed consent was obtained from all respondents.
- **Anonymisation:** The published ds_main.csv contains no names, email addresses,
  or other direct identifiers. Respondents are identified only by a Qualtrics
  response ID that is not linkable to personal records by third parties.
- **Secondary analysis:** This project performs secondary analysis of a publicly
  released, de-identified dataset. No additional ethics approval is required under
  standard academic guidelines for publicly available data.

## Data Handling in This Project
- `data/raw/ds_main.csv` is **not committed to this repository** (gitignored) to
  comply with the dataset licence, which requires attribution rather than
  redistribution of a full copy.
- Users wishing to reproduce this analysis must download ds_main.csv directly from
  https://osf.io/5c3qd and place it at `data/raw/ds_main.csv`.
- The generated XML (`xml/tisp_full.xml`) contains a 3,000-respondent demo sample
  only and is committed for XPath/XQuery demonstration purposes.

## Variables Used
| Variable | Source column(s) | Role |
|----------|-----------------|------|
| trust | TRUST_SCI_expert … TRUST_SCI_otherviews (12 items, mean) | Primary outcome |
| comm_freq | SCIINFO_* (10 items, mean) | Key predictor |
| primary_channel | SCIINFO_* (argmax column) | Grouping variable (ANOVA) |
| knowledge | TRUST_METHOD | Mediator (SEM) |
| climate_policy | CLIM_POLSUPPORT_* (5 items, mean) | Supplementary outcome |
| populism | SCIPOP_* (8 items, mean) | Supplementary predictor |
| country_income_group | World Bank 2022-23 classification (hardcoded) | Level-2 covariate |
| country | COUNTRY_CODE | Grouping / mapping |
