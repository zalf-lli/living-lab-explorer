import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

export const STORAGE_KEY = 'll-explorer-lang'

export function normalizeLanguage(lang) {
  return lang?.toLowerCase().startsWith('de') ? 'de' : 'en'
}

function getInitialLanguage() {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved) return normalizeLanguage(saved)
  } catch {
    // Ignore storage access issues and fall back to the browser language.
  }
  return normalizeLanguage(window.navigator.language)
}

const resources = {
  en: {
    translation: {
      app: {
        metadataErrorTitle: 'Failed to load Living Lab metadata.',
      },
      common: {
        loading: 'Loading...',
        loadingMap: 'Loading map...',
        language: 'Language',
        preliminaryDataBadge: 'Preliminary data / Vorlaeufige Daten',
      },
      header: {
        title: 'Living Lab Explorer',
      },
      landing: {
        eyebrow: 'Living Labs',
        title: 'Five Regions. Real-World Practice.',
        body:
          'In five living labs, we test innovative approaches together with practitioners on the ground. Pick a site on the map to explore its conditions, ambitions and progress.',
        listTitle: 'Living Labs',
      },
      kpi: {
        land_area_cropland_ha: 'Cropland area',
        farms_count: 'Number of farms',
        farm_avg_size_ha: 'Average farm size',
        organic_pct: 'Share of organic farming',
        n_surplus_kg_ha: 'Nitrogen surplus',
        p_surplus_kg_ha: 'Phosphorus surplus',
        groundwater_abstraction_1000m3: 'Groundwater abstraction (non-public supply)',
        agr_ch4_kt: 'Agricultural CH4 emissions',
        agr_n2o_kt: 'Agricultural N2O emissions',
        forest_area_ha: 'Forest area',
        natura2000_ha: 'Natura 2000 area',
        nature_reserves_ha: 'Nature reserves area',
        sealed_surface_pct: 'Share of sealed surface',
        population_total: 'Total population',
        gdp_per_capita_eur: 'GDP per capita',
        unemployment_rate_pct: 'Unemployment rate',
        household_income_eur: 'Disposable household income per capita',
      },
      statPanel: {
        pendingReviewTitle: 'Pending review',
        pendingReviewBody: 'Some indicators for this Living Lab are still pending expert review and data verification.',
        source: 'Source: Destatis GENESIS-Online, table {{tableId}}, retrieved {{date}}',
        sourceRegionalstatistik: 'Source: Regionalstatistik.de, table {{tableId}}, retrieved {{date}}',
        viewSource: 'View source',
        sourcesToggle: 'Sources',
        errorTitle: 'Statistics are temporarily unavailable.',
        errorBody: 'Reload the page - if this keeps happening, the data source may be temporarily unreachable.',
      },
      layers: {
        agriculture: 'Agriculture',
        climate: 'Climate',
        soil: 'Soil',
        economic: 'Socio-economic',
        landscape: 'Landscape',
        protectedAreas: 'Protected Areas',
      },
      legend: {
        agriculture: {
          arable: 'Arable',
          forest: 'Forest',
          grassland: 'Grassland',
          settlement: 'Settlement',
          water: 'Water',
        },
        climate: {
          arable: 'Very warm',
          forest: 'Temperate',
          grassland: 'Warm',
          settlement: 'Cool',
          water: 'Water / cold',
        },
        soil: {
          soilPolygons: 'BUEK soil polygons',
          specialAreas: 'Water / special areas',
          note: 'Legend shows the dominant semantic soil groups for this Living Lab; raw BUEK IDs stay in the data only as provenance.',
        },
        economic: {
          arable: 'High output',
          forest: 'Low intensity',
          grassland: 'Medium',
          settlement: 'Built-up',
          water: 'N/A',
        },
        protectedAreas: {
          note: 'Conservation sites intersecting this Living Lab region. Full polygon boundaries are shown, so sites extend beyond the region outline and designations may overlap. Source: BfN (FFH and bird sanctuaries 2019, nature reserves 2023) - not suitable for planning purposes.',
          empty: 'No protected areas intersect this Living Lab region.',
        },
      },
      charts: {
        agriculture: {
          title: 'Crop Type Composition',
          unit: '% area',
          bars: {
            winterWheat: 'Winter wheat',
            maize: 'Maize',
            winterBarley: 'Winter barley',
            sugarBeet: 'Sugar beet',
            otherCrops: 'Other crops',
          },
        },
        climate: {
          title: 'Mean Monthly Temp.',
          unit: 'deg C',
          bars: {
            jan: 'Jan',
            mar: 'Mar',
            may: 'May',
            jul: 'Jul',
            sep: 'Sep',
            nov: 'Nov',
          },
        },
        soil: {
          title: 'Soil Type Distribution',
          unit: '% area',
          bars: {
            sandyLoam: 'Sandy loam',
            loam: 'Loam',
            clayLoam: 'Clay loam',
            peat: 'Peat',
            other: 'Other',
          },
        },
        economic: {
          title: 'Farm Size Distribution',
          unit: '% farms',
          bars: {
            under10: '< 10 ha',
            from10To50: '10-50 ha',
            from50To200: '50-200 ha',
            over200: '> 200 ha',
          },
        },
        landscape: {
          title: 'Land Cover Distribution',
          unit: '% area',
          bars: {
            cropland: 'Cropland',
            forest: 'Forest',
            grassland: 'Grassland',
            settlement: 'Settlement',
            water: 'Water',
          },
        },
      },
      barChart: {
        source: 'Source: placeholder data - {{unit}}',
      },
      textBlock: {
        placeholder: 'Narrative text placeholder - landscape context, research focus, key challenges',
      },
      map: {
        loadError: 'Failed to load map data. Check the browser console.',
        soilLoading: 'Loading soil polygons for this Living Lab...',
        soilLoadError: 'Soil data could not be loaded for this Living Lab.',
        protectedAreasLoading: 'Loading protected areas for this Living Lab...',
        protectedAreasError: 'Protected areas data could not be loaded for this Living Lab.',
        placeholder: 'Interactive map (Leaflet + PMTiles) lands in Phase 3',
        layerComingSoon: 'Layer coming soon',
        dataUnavailable: 'Data for this tab is not available yet.',
        info: {
          tooltip: 'Map sources & attribution',
          basemap: 'Basemap',
          dataSource: 'Data layer',
          license: 'License',
          viewSource: 'View source',
          noSource: 'No additional layer is currently active. Basemap data shown above.',
        },
        soilTooltip: {
          type: 'Type',
          waterArea: 'Water area',
          specialArea: 'Special area',
          group: 'Group',
          legendUnit: 'Detailed unit',
          secondaryType: 'Secondary soil type',
          parentMaterial: 'Parent material',
          profile: 'Profile',
        },
        protectedAreasTooltip: {
          designation: 'Designation',
          area: 'Area',
          areaUnit: 'ha',
          established: 'Established',
          authority: 'Authority',
        },
      },
      llDetail: {
        loading: 'Loading Living Lab...',
        unknown: 'Unknown Living Lab: "{{slug}}"',
        designOption: 'Design option:',
        optionA: 'Option A',
        optionASub: 'Split Screen',
        optionADesc: 'Map fixed left - data panel scrolls right',
        optionB: 'Option B',
        optionBSub: 'Stacked',
        optionBDesc: 'Full-width sections - map then data below',
        wireframeNote: 'Wireframe prototype - placeholder data',
        layerTabsHint: 'Click the tabs to explore different socio-environmental features.',
        distributionTitle: '{{layer}} - distribution',
        aboutLandscape: 'About this Landscape',
        researchFocus: 'Research Focus',
        socioEconomicContext: 'Socio-economic Context',
        compareTitle: 'Compare with another Living Lab',
        compareCompactTitle: 'Want to compare with another Living Lab?',
        compareBody: 'Secondary feature - select any two LLs to view side-by-side metrics',
        compareAction: 'Compare',
        compareCompactAction: 'Add for comparison',
      },
    },
  },
  de: {
    translation: {
      app: {
        metadataErrorTitle: 'Living-Lab-Metadaten konnten nicht geladen werden.',
      },
      common: {
        loading: 'Wird geladen...',
        loadingMap: 'Karte wird geladen...',
        language: 'Sprache',
        preliminaryDataBadge: 'Preliminary data / Vorlaeufige Daten',
      },
      header: {
        title: 'Reallabore Explorer',
      },
      landing: {
        eyebrow: 'Reallabore',
        title: 'Fuenf Regionen. Echte Praxis.',
        body:
          'In fuenf Reallaboren erproben wir innovative Ansaetze gemeinsam mit Praxisakteuren vor Ort. Waehlen Sie einen Standort auf der Karte, um Rahmenbedingungen, Ziele und Fortschritte zu erkunden.',
        listTitle: 'Reallabore',
      },
      kpi: {
        land_area_cropland_ha: 'Ackerland',
        farms_count: 'Anzahl Betriebe',
        farm_avg_size_ha: 'Durchschnittliche Betriebsgroesse',
        organic_pct: 'Anteil oekologischer Landbau',
        n_surplus_kg_ha: 'Stickstoffueberschuss',
        p_surplus_kg_ha: 'Phosphorueberschuss',
        groundwater_abstraction_1000m3: 'Grundwasserentnahme (nichtoeffentliche Versorgung)',
        agr_ch4_kt: 'CH4-Emissionen Landwirtschaft',
        agr_n2o_kt: 'N2O-Emissionen Landwirtschaft',
        forest_area_ha: 'Waldflaeche',
        natura2000_ha: 'Natura-2000-Flaeche',
        nature_reserves_ha: 'Naturschutzgebietsflaeche',
        sealed_surface_pct: 'Anteil versiegelter Flaeche',
        population_total: 'Bevoelkerung insgesamt',
        gdp_per_capita_eur: 'Bruttoinlandsprodukt je Einwohner',
        unemployment_rate_pct: 'Arbeitslosenquote',
        household_income_eur: 'Verfuegbares Einkommen je Einwohner',
      },
      statPanel: {
        pendingReviewTitle: 'In Pruefung',
        pendingReviewBody: 'Einige Indikatoren fuer dieses Living Lab befinden sich noch in der fachlichen Pruefung.',
        source: 'Quelle: Destatis GENESIS-Online, Tabelle {{tableId}}, abgerufen am {{date}}',
        sourceRegionalstatistik: 'Quelle: Regionalstatistik.de, Tabelle {{tableId}}, abgerufen am {{date}}',
        viewSource: 'Quelle ansehen',
        sourcesToggle: 'Quellen',
        errorTitle: 'Statistiken sind voruebergehend nicht verfuegbar.',
        errorBody: 'Seite neu laden - falls das Problem bestehen bleibt, ist die Datenquelle moeglicherweise voruebergehend nicht erreichbar.',
      },
      layers: {
        agriculture: 'Landwirtschaft',
        climate: 'Klima',
        soil: 'Boden',
        economic: 'Soziooekonomie',
        landscape: 'Landschaft',
        protectedAreas: 'Schutzgebiete',
      },
      legend: {
        agriculture: {
          arable: 'Ackerland',
          forest: 'Wald',
          grassland: 'Gruenland',
          settlement: 'Siedlung',
          water: 'Wasser',
        },
        climate: {
          arable: 'Sehr warm',
          forest: 'Gemaessigt',
          grassland: 'Warm',
          settlement: 'Kuehl',
          water: 'Wasser / kalt',
        },
        soil: {
          soilPolygons: 'BUEK-Bodenpolygone',
          specialAreas: 'Gewaesser / Sonderflaechen',
          note: 'Die Legende zeigt die dominanten Bodengruppen dieses Living Labs; Farben folgen der semantischen Hauptgruppe, waehrend Detailangaben erst im Tooltip erscheinen.',
        },
        economic: {
          arable: 'Hoher Output',
          forest: 'Geringe Intensitaet',
          grassland: 'Mittel',
          settlement: 'Bebaut',
          water: 'k. A.',
        },
        protectedAreas: {
          note: 'Schutzgebiete, die diese Reallabor-Region schneiden. Es werden vollstaendige Polygongrenzen gezeigt, daher reichen Gebiete ueber den Regionsumriss hinaus und Ueberlagerungen sind moeglich. Quelle: BfN (FFH und Vogelschutz 2019, Naturschutzgebiete 2023) - nicht fuer Planungszwecke geeignet.',
          empty: 'Keine Schutzgebiete schneiden diese Reallabor-Region.',
        },
      },
      charts: {
        agriculture: {
          title: 'Anbauverteilung',
          unit: '% Flaeche',
          bars: {
            winterWheat: 'Winterweizen',
            maize: 'Mais',
            winterBarley: 'Wintergerste',
            sugarBeet: 'Zuckerrueben',
            otherCrops: 'Sonstige Kulturen',
          },
        },
        climate: {
          title: 'Mittlere Monatstemperatur',
          unit: 'Grad C',
          bars: {
            jan: 'Jan',
            mar: 'Mar',
            may: 'Mai',
            jul: 'Jul',
            sep: 'Sep',
            nov: 'Nov',
          },
        },
        soil: {
          title: 'Verteilung der Bodentypen',
          unit: '% Flaeche',
          bars: {
            sandyLoam: 'Sandiger Lehm',
            loam: 'Lehm',
            clayLoam: 'Toniger Lehm',
            peat: 'Torf',
            other: 'Sonstige',
          },
        },
        economic: {
          title: 'Verteilung der Betriebsgroessen',
          unit: '% Betriebe',
          bars: {
            under10: '< 10 ha',
            from10To50: '10-50 ha',
            from50To200: '50-200 ha',
            over200: '> 200 ha',
          },
        },
        landscape: {
          title: 'Landbedeckungsverteilung',
          unit: '% Flaeche',
          bars: {
            cropland: 'Ackerland',
            forest: 'Wald',
            grassland: 'Gruenland',
            settlement: 'Siedlung',
            water: 'Wasser',
          },
        },
      },
      barChart: {
        source: 'Quelle: Platzhalterdaten - {{unit}}',
      },
      textBlock: {
        placeholder: 'Textplatzhalter - Landschaftskontext, Forschungsfokus, zentrale Herausforderungen',
      },
      map: {
        loadError: 'Kartendaten konnten nicht geladen werden. Bitte Browser-Konsole pruefen.',
        soilLoading: 'Bodenpolygone fuer dieses Living Lab werden geladen...',
        soilLoadError: 'Die Bodendaten fuer dieses Living Lab konnten nicht geladen werden.',
        protectedAreasLoading: 'Schutzgebiete fuer dieses Living Lab werden geladen...',
        protectedAreasError: 'Die Schutzgebietsdaten fuer dieses Living Lab konnten nicht geladen werden.',
        placeholder: 'Interaktive Karte (Leaflet + PMTiles) folgt in Phase 3',
        layerComingSoon: 'Ebene folgt in Kuerze',
        dataUnavailable: 'Daten fuer diese Ebene sind noch nicht verfuegbar.',
        info: {
          tooltip: 'Kartenquellen & Nachweise',
          basemap: 'Hintergrundkarte',
          dataSource: 'Datenebene',
          license: 'Lizenz',
          viewSource: 'Quelle anzeigen',
          noSource: 'Aktuell ist keine zusaetzliche Ebene aktiv. Es wird die Hintergrundkarte gezeigt.',
        },
        soilTooltip: {
          type: 'Typ',
          waterArea: 'Gewaesser',
          specialArea: 'Sonderflaeche',
          group: 'Gruppe',
          legendUnit: 'Detaileinheit',
          secondaryType: 'Sekundaerer Bodentyp',
          parentMaterial: 'Ausgangsmaterial',
          profile: 'Profil',
        },
        protectedAreasTooltip: {
          designation: 'Schutzgebietstyp',
          area: 'Flaeche',
          areaUnit: 'ha',
          established: 'Eingerichtet',
          authority: 'Behoerde',
        },
      },
      llDetail: {
        loading: 'Living Lab wird geladen...',
        unknown: 'Unbekanntes Living Lab: "{{slug}}"',
        designOption: 'Designoption:',
        optionA: 'Option A',
        optionASub: 'Geteilter Bildschirm',
        optionADesc: 'Karte links fixiert - Datenbereich scrollt rechts',
        optionB: 'Option B',
        optionBSub: 'Gestapelt',
        optionBDesc: 'Abschnitte in voller Breite - Karte oben, Daten darunter',
        wireframeNote: 'Wireframe-Prototyp - Platzhalterdaten',
        layerTabsHint: 'Klicken Sie auf die Tabs, um verschiedene sozio-oekologische Merkmale zu erkunden.',
        distributionTitle: '{{layer}} - Verteilung',
        aboutLandscape: 'Ueber diese Landschaft',
        researchFocus: 'Forschungsfokus',
        socioEconomicContext: 'Soziooekonomischer Kontext',
        compareTitle: 'Mit einem anderen Living Lab vergleichen',
        compareCompactTitle: 'Mit einem anderen Living Lab vergleichen?',
        compareBody: 'Sekundaere Funktion - zwei Living Labs fuer einen Seitenvergleich auswaehlen',
        compareAction: 'Vergleichen',
        compareCompactAction: 'Zum Vergleich hinzufuegen',
      },
    },
  },
}

i18n.use(initReactI18next).init({
  resources,
  lng: getInitialLanguage(),
  fallbackLng: 'en',
  supportedLngs: ['en', 'de'],
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
