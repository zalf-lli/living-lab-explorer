// Generated from data-pipeline/sources/sources.yaml (chelsa-climate) and data/climate_color_breaks.json.
// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.
export const CLIMATE_VARIABLES = [
  {
    "id": "gdd",
    "family": "heat",
    "unit": {
      "en": "degC-day",
      "de": "degC-Tag"
    },
    "deltaUnit": {
      "en": "degC-day",
      "de": "degC-Tag"
    },
    "labelKey": "climate.variable.gdd",
    "legendNoteKey": "legend.climate.note.gdd"
  },
  {
    "id": "bio1",
    "family": "heat",
    "unit": {
      "en": "degC",
      "de": "degC"
    },
    "deltaUnit": {
      "en": "degC",
      "de": "degC"
    },
    "labelKey": "climate.variable.bio1",
    "legendNoteKey": "legend.climate.note.bio1"
  },
  {
    "id": "bio12",
    "family": "water",
    "unit": {
      "en": "mm",
      "de": "mm"
    },
    "deltaUnit": {
      "en": "%",
      "de": "%"
    },
    "labelKey": "climate.variable.bio12",
    "legendNoteKey": "legend.climate.note.bio12"
  },
  {
    "id": "bio18",
    "family": "water",
    "unit": {
      "en": "mm",
      "de": "mm"
    },
    "deltaUnit": {
      "en": "%",
      "de": "%"
    },
    "labelKey": "climate.variable.bio18",
    "legendNoteKey": "legend.climate.note.bio18"
  }
]

export const CLIMATE_LEGEND = {
  "gdd": {
    "baseline": [
      {
        "value": "b0",
        "en": "< 1827.0 degC-day",
        "de": "< 1827,0 degC-Tag",
        "color": "#fce3da"
      },
      {
        "value": "b1",
        "en": "1827.0 – 1996.0 degC-day",
        "de": "1827,0 – 1996,0 degC-Tag",
        "color": "#eb5b25"
      },
      {
        "value": "b2",
        "en": "1996.0 – 2066.0 degC-day",
        "de": "1996,0 – 2066,0 degC-Tag",
        "color": "#dc4b14"
      },
      {
        "value": "b3",
        "en": "> 2066.0 degC-day",
        "de": "> 2066,0 degC-Tag",
        "color": "#bb3f11"
      }
    ],
    "change": [
      {
        "value": "b0",
        "en": "< +647.0 degC-day",
        "de": "< +647,0 degC-Tag",
        "color": "#fce3da"
      },
      {
        "value": "b1",
        "en": "+647.0 – +822.0 degC-day",
        "de": "+647,0 – +822,0 degC-Tag",
        "color": "#eb5b25"
      },
      {
        "value": "b2",
        "en": "+822.0 – +1129.0 degC-day",
        "de": "+822,0 – +1129,0 degC-Tag",
        "color": "#dc4b14"
      },
      {
        "value": "b3",
        "en": "> +1129.0 degC-day",
        "de": "> +1129,0 degC-Tag",
        "color": "#bb3f11"
      }
    ]
  },
  "bio1": {
    "baseline": [
      {
        "value": "b0",
        "en": "< 8.9 degC",
        "de": "< 8,9 degC",
        "color": "#fce3da"
      },
      {
        "value": "b1",
        "en": "8.9 – 9.4 degC",
        "de": "8,9 – 9,4 degC",
        "color": "#eb5b25"
      },
      {
        "value": "b2",
        "en": "9.4 – 9.6 degC",
        "de": "9,4 – 9,6 degC",
        "color": "#dc4b14"
      },
      {
        "value": "b3",
        "en": "> 9.6 degC",
        "de": "> 9,6 degC",
        "color": "#bb3f11"
      }
    ],
    "change": [
      {
        "value": "b0",
        "en": "< +2.6 degC",
        "de": "< +2,6 degC",
        "color": "#fce3da"
      },
      {
        "value": "b1",
        "en": "+2.6 – +3.3 degC",
        "de": "+2,6 – +3,3 degC",
        "color": "#eb5b25"
      },
      {
        "value": "b2",
        "en": "+3.3 – +4.0 degC",
        "de": "+3,3 – +4,0 degC",
        "color": "#dc4b14"
      },
      {
        "value": "b3",
        "en": "> +4.0 degC",
        "de": "> +4,0 degC",
        "color": "#bb3f11"
      }
    ]
  },
  "bio12": {
    "baseline": [
      {
        "value": "b0",
        "en": "< 595.0 mm",
        "de": "< 595,0 mm",
        "color": "#00b3ad"
      },
      {
        "value": "b1",
        "en": "595.0 – 623.0 mm",
        "de": "595,0 – 623,0 mm",
        "color": "#008581"
      },
      {
        "value": "b2",
        "en": "623.0 – 788.0 mm",
        "de": "623,0 – 788,0 mm",
        "color": "#005754"
      },
      {
        "value": "b3",
        "en": "> 788.0 mm",
        "de": "> 788,0 mm",
        "color": "#00413f"
      }
    ],
    "change": [
      {
        "value": "b0",
        "en": "< +1.5 %",
        "de": "< +1,5 %",
        "color": "#00b3ad"
      },
      {
        "value": "b1",
        "en": "+1.5 – +2.0 %",
        "de": "+1,5 – +2,0 %",
        "color": "#008581"
      },
      {
        "value": "b2",
        "en": "+2.0 – +3.0 %",
        "de": "+2,0 – +3,0 %",
        "color": "#005754"
      },
      {
        "value": "b3",
        "en": "> +3.0 %",
        "de": "> +3,0 %",
        "color": "#00413f"
      }
    ]
  },
  "bio18": {
    "baseline": [
      {
        "value": "b0",
        "en": "< 185.0 mm",
        "de": "< 185,0 mm",
        "color": "#00b3ad"
      },
      {
        "value": "b1",
        "en": "185.0 – 192.0 mm",
        "de": "185,0 – 192,0 mm",
        "color": "#008581"
      },
      {
        "value": "b2",
        "en": "192.0 – 212.0 mm",
        "de": "192,0 – 212,0 mm",
        "color": "#005754"
      },
      {
        "value": "b3",
        "en": "> 212.0 mm",
        "de": "> 212,0 mm",
        "color": "#00413f"
      }
    ],
    "change": [
      {
        "value": "b0",
        "en": "< -6.5 %",
        "de": "< -6,5 %",
        "color": "#00b3ad"
      },
      {
        "value": "b1",
        "en": "-6.5 – -5.5 %",
        "de": "-6,5 – -5,5 %",
        "color": "#008581"
      },
      {
        "value": "b2",
        "en": "-5.5 – -5.0 %",
        "de": "-5,5 – -5,0 %",
        "color": "#005754"
      },
      {
        "value": "b3",
        "en": "> -5.0 %",
        "de": "> -5,0 %",
        "color": "#00413f"
      }
    ]
  }
}

export const CLIMATE_RAMP_SHAPE = {
  "gdd": {
    "baseline": "sequential",
    "change": "sequential"
  },
  "bio1": {
    "baseline": "sequential",
    "change": "sequential"
  },
  "bio12": {
    "baseline": "sequential",
    "change": "sequential"
  },
  "bio18": {
    "baseline": "sequential",
    "change": "sequential"
  }
}
