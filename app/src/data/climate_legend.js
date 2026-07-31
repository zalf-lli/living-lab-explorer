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
    "change": {
      "2041_2070": [
        {
          "value": "b0",
          "en": "< +621.0 degC-day",
          "de": "< +621,0 degC-Tag",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+621.0 – +638.0 degC-day",
          "de": "+621,0 – +638,0 degC-Tag",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+638.0 – +654.0 degC-day",
          "de": "+638,0 – +654,0 degC-Tag",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+654.0 – +675.0 degC-day",
          "de": "+654,0 – +675,0 degC-Tag",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +675.0 degC-day",
          "de": "> +675,0 degC-Tag",
          "color": "#9f350e"
        }
      ],
      "2071_2100": [
        {
          "value": "b0",
          "en": "< +1086.0 degC-day",
          "de": "< +1086,0 degC-Tag",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+1086.0 – +1114.0 degC-day",
          "de": "+1086,0 – +1114,0 degC-Tag",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+1114.0 – +1139.0 degC-day",
          "de": "+1114,0 – +1139,0 degC-Tag",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+1139.0 – +1161.0 degC-day",
          "de": "+1139,0 – +1161,0 degC-Tag",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +1161.0 degC-day",
          "de": "> +1161,0 degC-Tag",
          "color": "#9f350e"
        }
      ]
    }
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
    "change": {
      "2041_2070": [
        {
          "value": "b0",
          "en": "< +2.5 degC",
          "de": "< +2,5 degC",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+2.5 – +2.6 degC",
          "de": "+2,5 – +2,6 degC",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+2.6 – +2.7 degC",
          "de": "+2,6 – +2,7 degC",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+2.7 – +2.8 degC",
          "de": "+2,7 – +2,8 degC",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +2.8 degC",
          "de": "> +2,8 degC",
          "color": "#9f350e"
        }
      ],
      "2071_2100": [
        {
          "value": "b0",
          "en": "< +3.9 degC",
          "de": "< +3,9 degC",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+3.9 – +4.0 degC",
          "de": "+3,9 – +4,0 degC",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+4.0 – +4.1 degC",
          "de": "+4,0 – +4,1 degC",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+4.1 – +4.2 degC",
          "de": "+4,1 – +4,2 degC",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +4.2 degC",
          "de": "> +4,2 degC",
          "color": "#9f350e"
        }
      ]
    }
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
    "change": {
      "2041_2070": [
        {
          "value": "b0",
          "en": "< +1.0 %",
          "de": "< +1,0 %",
          "color": "#00b3ad"
        },
        {
          "value": "b1",
          "en": "+1.0 – +1.5 %",
          "de": "+1,0 – +1,5 %",
          "color": "#008581"
        },
        {
          "value": "b2",
          "en": "+1.5 – +2.0 %",
          "de": "+1,5 – +2,0 %",
          "color": "#005754"
        },
        {
          "value": "b3",
          "en": "+2.0 – +2.5 %",
          "de": "+2,0 – +2,5 %",
          "color": "#00413f"
        },
        {
          "value": "b4",
          "en": "> +2.5 %",
          "de": "> +2,5 %",
          "color": "#00312f"
        }
      ],
      "2071_2100": [
        {
          "value": "b0",
          "en": "< +2.5 %",
          "de": "< +2,5 %",
          "color": "#00b3ad"
        },
        {
          "value": "b1",
          "en": "+2.5 – +3.0 %",
          "de": "+2,5 – +3,0 %",
          "color": "#008581"
        },
        {
          "value": "b2",
          "en": "+3.0 – +3.5 %",
          "de": "+3,0 – +3,5 %",
          "color": "#005754"
        },
        {
          "value": "b3",
          "en": "+3.5 – +4.0 %",
          "de": "+3,5 – +4,0 %",
          "color": "#00413f"
        },
        {
          "value": "b4",
          "en": "> +4.0 %",
          "de": "> +4,0 %",
          "color": "#00312f"
        }
      ]
    }
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
    "change": {
      "2041_2070": [
        {
          "value": "b0",
          "en": "< -5.5 %",
          "de": "< -5,5 %",
          "color": "#00b3ad"
        },
        {
          "value": "b1",
          "en": "-5.5 – -5.0 %",
          "de": "-5,5 – -5,0 %",
          "color": "#008581"
        },
        {
          "value": "b2",
          "en": "-5.0 – -4.5 %",
          "de": "-5,0 – -4,5 %",
          "color": "#005754"
        },
        {
          "value": "b3",
          "en": "-4.5 – -4.0 %",
          "de": "-4,5 – -4,0 %",
          "color": "#00413f"
        },
        {
          "value": "b4",
          "en": "> -4.0 %",
          "de": "> -4,0 %",
          "color": "#00312f"
        }
      ],
      "2071_2100": [
        {
          "value": "b0",
          "en": "< -8.5 %",
          "de": "< -8,5 %",
          "color": "#00b3ad"
        },
        {
          "value": "b1",
          "en": "-8.5 – -8.0 %",
          "de": "-8,5 – -8,0 %",
          "color": "#008581"
        },
        {
          "value": "b2",
          "en": "-8.0 – -5.5 %",
          "de": "-8,0 – -5,5 %",
          "color": "#005754"
        },
        {
          "value": "b3",
          "en": "-5.5 – -5.0 %",
          "de": "-5,5 – -5,0 %",
          "color": "#00413f"
        },
        {
          "value": "b4",
          "en": "> -5.0 %",
          "de": "> -5,0 %",
          "color": "#00312f"
        }
      ]
    }
  }
}

export const CLIMATE_RAMP_SHAPE = {
  "gdd": {
    "baseline": "sequential",
    "change": {
      "2041_2070": "sequential",
      "2071_2100": "sequential"
    }
  },
  "bio1": {
    "baseline": "sequential",
    "change": {
      "2041_2070": "sequential",
      "2071_2100": "sequential"
    }
  },
  "bio12": {
    "baseline": "sequential",
    "change": {
      "2041_2070": "sequential",
      "2071_2100": "sequential"
    }
  },
  "bio18": {
    "baseline": "sequential",
    "change": {
      "2041_2070": "sequential",
      "2071_2100": "sequential"
    }
  }
}
