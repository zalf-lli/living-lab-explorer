"""
Export a catalogue of all planned Destatis variables to CSV for expert review.
No API calls — purely a reference document.

Output:  data/destatis_variables_catalogue.csv
Run:     python data-pipeline/python/export_variables.py
"""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

VARIABLES = [
    # group, key, table, label_en, label_de, unit_en, unit_de, notes_en
    # Agriculture
    ("Agriculture","land_area_total_km2","33111BJ001","Total area","Gesamtflaeche","km2","km2","Total administrative area of the Kreis"),
    ("Agriculture","land_area_agr_ha","33111BJ001","Agricultural area","Landwirtschaftliche Flaeche","ha","ha","Total area used for agriculture"),
    ("Agriculture","agriculture_pct","33111BJ001","Share of agricultural land","Anteil Landwirtschaftsflaeche","%","%","Agricultural area as % of total area (derived)"),
    ("Agriculture","land_area_cropland_ha","33111BJ002","Cropland area","Ackerland","ha","ha","Arable / cropland area"),
    ("Agriculture","land_area_grassland_ha","33111BJ002","Permanent grassland area","Dauergrunland","ha","ha","Permanent pastures and meadows"),
    ("Agriculture","land_area_vineyard_ha","33111BJ002","Vineyard area","Rebflaeche","ha","ha","Area planted with vines"),
    ("Agriculture","land_area_orchard_ha","33111BJ002","Orchard / permanent crops area","Obstanlagen und Baumschulflaeche","ha","ha","Fruit trees, nurseries and other permanent crops"),
    ("Agriculture","farms_count","41120BJ001","Number of farms","Anzahl Betriebe","count","Anzahl","Total number of agricultural holdings"),
    ("Agriculture","uaa_total_ha","41120BJ001","Utilised agricultural area (UAA)","Landwirtschaftlich genutzte Flaeche (LF)","ha","ha","Total UAA across all farms"),
    ("Agriculture","farm_avg_size_ha","41120BJ001","Average farm size","Durchschnittliche Betriebsgroesse","ha","ha","UAA / farms count (derived)"),
    ("Agriculture","farms_organic_count","41120BJ002","Organic farms","Oekologisch wirtschaftende Betriebe","count","Anzahl","Number of certified organic farms"),
    ("Agriculture","uaa_organic_ha","41120BJ002","Organic UAA","Oekologisch bewirtschaftete LF","ha","ha","UAA under organic management"),
    ("Agriculture","organic_pct","41120BJ002","Share of organic farming","Anteil oekologischer Landbau","%","%","Organic UAA as % of total UAA (derived)"),
    ("Agriculture","uaa_owner_ha","41120BJ003","Owner-operated UAA","Eigentumsflaeche","ha","ha","UAA farmed by the owner"),
    ("Agriculture","uaa_rented_ha","41120BJ003","Rented UAA","Pachtflaeche","ha","ha","UAA under tenancy/lease"),
    ("Agriculture","tenancy_rented_pct","41120BJ003","Share of rented land","Pachtanteil","%","%","Rented UAA as % of total UAA (derived)"),
    ("Agriculture","farms_lt5ha","41120BJ004","Farms < 5 ha","Betriebe unter 5 ha","count","Anzahl","Holdings with UAA below 5 ha"),
    ("Agriculture","farms_5_20ha","41120BJ004","Farms 5-20 ha","Betriebe 5-20 ha","count","Anzahl","Holdings with UAA 5 to 20 ha"),
    ("Agriculture","farms_20_50ha","41120BJ004","Farms 20-50 ha","Betriebe 20-50 ha","count","Anzahl","Holdings with UAA 20 to 50 ha"),
    ("Agriculture","farms_50_100ha","41120BJ004","Farms 50-100 ha","Betriebe 50-100 ha","count","Anzahl","Holdings with UAA 50 to 100 ha"),
    ("Agriculture","farms_gt100ha","41120BJ004","Farms > 100 ha","Betriebe ueber 100 ha","count","Anzahl","Holdings with UAA above 100 ha"),
    ("Agriculture","farm_labour_fte","41141BJ001","Farm labour (FTE)","Arbeitskraefte Landwirtschaft (VZE)","FTE","VZE","Full-time equivalent farm labour"),
    ("Agriculture","crop_cereals_ha","41243BJ001","Cereals area","Getreidflaeche","ha","ha","Area sown with cereals (wheat, rye, barley, etc.)"),
    ("Agriculture","crop_oilseed_ha","41243BJ001","Oilseed crops area","Oelfruechte","ha","ha","Rapeseed, sunflower and other oilseeds"),
    ("Agriculture","crop_sugar_beet_ha","41243BJ001","Sugar beet area","Zuckerrueben","ha","ha","Area under sugar beet"),
    ("Agriculture","crop_vegetables_ha","41243BJ001","Vegetables area","Gemuese","ha","ha","Open-field and glasshouse vegetables"),
    ("Agriculture","crop_maize_ha","41243BJ001","Maize area (grain + silage)","Mais (Koerner- und Silomais)","ha","ha","Total maize area"),
    ("Agriculture","livestock_gve_total","41330BJ001","Total livestock units (LU)","Gesamtviehbestand (GVE)","LU","GVE","All species expressed in livestock units"),
    ("Agriculture","livestock_gve_per_ha","41330BJ001","Livestock density","Viehbesatzdichte","LU/ha UAA","GVE/ha LF","LU per ha UAA (derived)"),
    ("Agriculture","livestock_cattle","41330BJ002","Cattle headcount","Rinder","head","Tiere","Total cattle including dairy cows"),
    ("Agriculture","livestock_dairy_cows","41330BJ002","Dairy cows","Milchkuehe","head","Tiere","Cows kept for milk production"),
    ("Agriculture","livestock_pigs","41330BJ003","Pig headcount","Schweine","head","Tiere","Total swine headcount"),
    ("Agriculture","livestock_poultry","41330BJ004","Poultry headcount","Gefluegel","head","Tiere","All poultry species"),
    ("Agriculture","n_surplus_kg_ha","41411BJ001","Nitrogen surplus","Stickstoffueberschuss","kg N/ha UAA","kg N/ha LF","N input minus N output per ha UAA"),
    ("Agriculture","p_surplus_kg_ha","41411BJ002","Phosphorus surplus","Phosphorueberschuss","kg P/ha UAA","kg P/ha LF","P input minus P output per ha UAA"),
    ("Agriculture","pesticide_sales_kg","41511BJ001","Pesticide sales","Pflanzenschutzmittelabsatz","kg active ingredient","kg Wirkstoff","Total pesticide active ingredients sold in Kreis"),
    ("Agriculture","irrigated_area_ha","41612BJ001","Irrigated area","Bewaesserte Flaeche","ha","ha","Area receiving supplementary irrigation"),
    ("Agriculture","irrigation_water_m3","41612BJ001","Irrigation water volume","Bewaesserungswassermenge","m3","m3","Total volume of water applied for irrigation"),
    ("Agriculture","land_price_eur_ha","61111KJ001","Agricultural land price","Kaufwert landwirtschaftlicher Flaechen","EUR/ha","EUR/ha","Average price per ha of sold agricultural land"),
    ("Agriculture","farm_rent_eur_ha","61511KJ001","Average farm rent","Durchschnittliche Pacht","EUR/ha","EUR/ha","Average annual rent per ha of leased agricultural land"),
    # Environment
    ("Environment","forest_area_ha","33111BJ003","Forest area","Waldflaeche","ha","ha","Total forest and woodland area"),
    ("Environment","forest_public_pct","33111BJ003","Share of public forest","Anteil oeffentlicher Wald","%","%","Forest owned by state/municipality as % of total forest"),
    ("Environment","natura2000_ha","32121BJ001","Natura 2000 area","Natura-2000-Flaeche","ha","ha","Area designated under EU Habitats or Birds Directive"),
    ("Environment","nature_reserves_ha","32141BJ001","Nature reserves area","Naturschutzgebietsflaeche","ha","ha","Strictly protected nature reserve area"),
    ("Environment","landscape_protection_ha","32141BJ001","Landscape protection area","Landschaftsschutzgebietsflaeche","ha","ha","Less-strict landscape protection zones"),
    ("Environment","agr_ch4_kt","32411BJ001","Agricultural CH4 emissions","CH4-Emissionen Landwirtschaft","kt CO2eq","kt CO2aeq","Methane from livestock and manure management"),
    ("Environment","agr_n2o_kt","32411BJ001","Agricultural N2O emissions","N2O-Emissionen Landwirtschaft","kt CO2eq","kt CO2aeq","Nitrous oxide from soils and fertiliser application"),
    ("Environment","groundwater_nitrate_mg_l","32221BJ001","Nitrate in groundwater","Nitrat im Grundwasser","mg NO3/l","mg NO3/l","Average nitrate concentration at monitoring stations"),
    ("Environment","settlement_area_ha","33111BJ004","Settlement and transport area","Siedlungs- und Verkehrsflaeche","ha","ha","Built-up land including roads and railways"),
    ("Environment","sealed_surface_pct","33111BJ004","Share of sealed surface","Anteil versiegelter Flaeche","%","%","Sealed/impervious surface as % of total area"),
    # Social
    ("Social","population_total","12411KJ002","Total population","Bevoelkerung insgesamt","persons","Personen","Resident population at year-end"),
    ("Social","population_density_per_km2","12411KJ002","Population density","Bevoelkerungsdichte","persons/km2","Einw./km2","Population per km2 (derived)"),
    ("Social","births","12411KJ003","Live births","Lebendgeborene","count","Anzahl","Number of live births per year"),
    ("Social","deaths","12411KJ003","Deaths","Gestorbene","count","Anzahl","Number of deaths per year"),
    ("Social","natural_balance","12411KJ003","Natural population balance","Natuerlicher Bevoelkerungssaldo","persons","Personen","Births minus deaths"),
    ("Social","net_migration","12411KJ004","Net migration","Wanderungssaldo","persons","Personen","In-migrants minus out-migrants"),
    ("Social","pop_under18_pct","12411KJ006","Share of population under 18","Anteil unter 18 Jahren","%","%","Children and youth as % of total population"),
    ("Social","pop_65plus_pct","12411KJ006","Share of population 65+","Anteil 65 Jahre und aelter","%","%","Elderly population share - indicator of rural ageing"),
    ("Social","pop_working_age_pct","12411KJ006","Share of working-age population (18-64)","Anteil Bevoelkerung im erwerbsfaehigen Alter","%","%","Population aged 18-64 as % of total"),
    ("Social","foreign_nationals_pct","12411KJ007","Share of foreign nationals","Auslaenderanteil","%","%","Non-German residents as % of total population"),
    ("Social","gdp_per_capita_eur","82111KJ001","GDP per capita","Bruttoinlandsprodukt je Einwohner","EUR","EUR","Gross domestic product per resident"),
    ("Social","gva_agriculture_pct","82111KJ002","GVA share of agriculture","Anteil Landwirtschaft an Bruttowertschoepfung","%","%","Agriculture, forestry and fishing share of total GVA"),
    ("Social","gva_industry_pct","82111KJ002","GVA share of industry","Anteil Industrie an Bruttowertschoepfung","%","%","Manufacturing and mining share of total GVA"),
    ("Social","gva_services_pct","82111KJ002","GVA share of services","Anteil Dienstleistungen an Bruttowertschoepfung","%","%","Services share of total GVA"),
    ("Social","household_income_eur","82521KJ001","Disposable household income per capita","Verfuegbares Einkommen je Einwohner","EUR","EUR","Net income available to households per resident"),
    ("Social","unemployment_rate_pct","13211KJ002","Unemployment rate","Arbeitslosenquote","%","%","Unemployed as % of civilian labour force"),
    ("Social","unemployment_youth_pct","13211KJ003","Youth unemployment rate (15-25)","Jugendarbeitslosenquote (15-25 Jahre)","%","%","Unemployed aged 15-25 as % of that age group"),
    ("Social","commuters_in","23111KJ001","In-commuters","Einpendler","persons","Personen","Workers commuting into the Kreis"),
    ("Social","commuters_out","23111KJ001","Out-commuters","Auspendler","persons","Personen","Workers commuting out of the Kreis"),
    ("Social","commuter_balance","23111KJ001","Commuter balance","Pendlersaldo","persons","Personen","In-commuters minus out-commuters (derived)"),
]

fields = ["group","variable_key","genesis_table","label_en","label_de",
          "unit_en","unit_de","notes_en","include_yn","priority_1_3","expert_comments"]

out = DATA / "destatis_variables_catalogue.csv"
with out.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for g,k,t,le,ld,ue,ud,n in VARIABLES:
        writer.writerow({"group":g,"variable_key":k,"genesis_table":t,
                         "label_en":le,"label_de":ld,"unit_en":ue,"unit_de":ud,
                         "notes_en":n,"include_yn":"","priority_1_3":"","expert_comments":""})

print(f"[done] {len(VARIABLES)} variables -> {out}")
