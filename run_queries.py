from saxonche import PySaxonProcessor

with PySaxonProcessor(license=False) as proc:
    doc = proc.parse_xml(xml_file_name="xml/tisp_full.xml")

    print("=" * 60)
    print("XPATH — low-trust, social-media-primary respondents")
    print("=" * 60)
    xq1 = proc.new_xquery_processor()
    xq1.set_query_content('''
    declare namespace tisp = "http://group7.tisp.org/schema";
    //tisp:Respondent[tisp:Trust_Scale/tisp:overall < 3 and tisp:Communication/tisp:primary = 'Social Media']
    ''')
    xq1.set_context(xdm_item=doc)
    print(xq1.run_query_to_string()[:2000])  # first 2000 chars, it'll be long

    print("\n" + "=" * 60)
    print("XQUERY — mean trust and N per country")
    print("=" * 60)
    xq2 = proc.new_xquery_processor()
    xq2.set_query_content('''
    declare namespace tisp = "http://group7.tisp.org/schema";
    for $country in distinct-values(//tisp:Respondent/@country)
    let $resp := //tisp:Respondent[@country = $country]
    let $meanTrust := avg($resp/tisp:Trust_Scale/tisp:overall)
    order by $meanTrust descending
    return
      <CountrySummary country="{$country}">
        <MeanTrust>{ round($meanTrust * 100) div 100 }</MeanTrust>
        <N>{ count($resp) }</N>
      </CountrySummary>
    ''')
    xq2.set_context(xdm_item=doc)
    print(xq2.run_query_to_string())