# XPath / XQuery Scripts — Group 7 (TISP Dataset)

All expressions run against `tisp_sample.xml`, validated by `tisp_schema.xsd`.
Namespace prefix used below: `tisp = http://group7.tisp.org/schema`

## XPath

**1. Low-trust respondents who primarily use social media** (as specified in the assessment outline):
```xpath
//tisp:Respondent[tisp:Trust_Scale/tisp:overall < 3 and tisp:Communication/tisp:primary = 'Social Media']
```
Returns respondents R000001 and R000003 in the sample — both low-trust, social-media-primary users, consistent with the mediation hypothesis (frequent informal-channel use associates with lower trust and higher populist attitudes).

**2. All respondents from high-income countries with high climate policy support:**
```xpath
//tisp:Respondent[tisp:Demographics/tisp:CountryIncomeGroup = 'high_income' and tisp:Climate/tisp:policySupport >= 4]
```

**3. Respondent IDs and countries only (projection):**
```xpath
//tisp:Respondent/@id | //tisp:Respondent/@country
```

**4. Average trust score computation target (used inside XQuery below), selecting the node set:**
```xpath
//tisp:Respondent/tisp:Trust_Scale/tisp:overall
```

**5. Respondents where populism score exceeds trust score (populist-leaning):**
```xpath
//tisp:Respondent[tisp:Populism/tisp:overall > tisp:Trust_Scale/tisp:overall]
```

**6. Schema validation check — items outside the permitted Likert range (should return empty on valid data):**
```xpath
//tisp:Item[. < 1 or . > 5]
```

## XQuery

**1. Per-country mean trust score and dominant communication channel** (as specified in the assessment outline):
```xquery
xquery version "3.1";
declare namespace tisp = "http://group7.tisp.org/schema";

for $country in distinct-values(//tisp:Respondent/@country)
let $resp := //tisp:Respondent[@country = $country]
let $meanTrust := avg($resp/tisp:Trust_Scale/tisp:overall)
let $channels := $resp/tisp:Communication/tisp:primary
let $dominant := (
  for $c in distinct-values($channels)
  order by count($channels[. = $c]) descending
  return $c
)[1]
order by $meanTrust descending
return
  <CountrySummary country="{$country}">
    <MeanTrust>{ round($meanTrust * 100) div 100 }</MeanTrust>
    <DominantChannel>{ $dominant }</DominantChannel>
    <N>{ count($resp) }</N>
  </CountrySummary>
```

**2. Country-income-group comparison table (feeds Results Table 1):**
```xquery
xquery version "3.1";
declare namespace tisp = "http://group7.tisp.org/schema";

for $grp in distinct-values(//tisp:Respondent/tisp:Demographics/tisp:CountryIncomeGroup)
let $resp := //tisp:Respondent[tisp:Demographics/tisp:CountryIncomeGroup = $grp]
return
  <IncomeGroupSummary group="{$grp}">
    <N>{ count($resp) }</N>
    <MeanTrust>{ round(avg($resp/tisp:Trust_Scale/tisp:overall) * 100) div 100 }</MeanTrust>
    <MeanPopulism>{ round(avg($resp/tisp:Populism/tisp:overall) * 100) div 100 }</MeanPopulism>
    <MeanClimateSupport>{ round(avg($resp/tisp:Climate/tisp:policySupport) * 100) div 100 }</MeanClimateSupport>
  </IncomeGroupSummary>
```

**3. Validation query — flags respondents with missing mandatory Trust_Scale/overall (data-quality check for the metadata report):**
```xquery
xquery version "3.1";
declare namespace tisp = "http://group7.tisp.org/schema";

for $r in //tisp:Respondent
where empty($r/tisp:Trust_Scale/tisp:overall)
return $r/@id
```

## Notes for the group
- These are run with **Saxon** or **BaseX** (both free; BaseX has a GUI and is the easiest to demo on camera for the presentation).
- Once the real `ds_main.csv` is converted to XML (script provided in `/code/csv_to_xml.py`), re-run these unchanged — they operate on the schema structure, not on sample-specific values.
- Query 1 (XQuery) directly answers the assignment's required XQuery task; Query 1 (XPath) directly answers the assignment's required XPath task — cite both by line number in your Methods section.
