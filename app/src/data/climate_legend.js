// Generated from data-pipeline/sources/sources.yaml (chelsa-climate) and data/climate_color_breaks.json.
// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.
export const CLIMATE_VARIABLES = [
  {
    "id": "gdd",
    "family": "heat",
    "unit": {
      "en": "°C·d",
      "de": "°C·d"
    },
    "deltaUnit": {
      "en": "°C·d",
      "de": "°C·d"
    },
    "labelKey": "climate.variable.gdd",
    "legendNoteKey": "legend.climate.note.gdd"
  },
  {
    "id": "bio1",
    "family": "heat",
    "unit": {
      "en": "°C",
      "de": "°C"
    },
    "deltaUnit": {
      "en": "°C",
      "de": "°C"
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
        "en": "< 1801.0 °C·d",
        "de": "< 1801,0 °C·d",
        "color": "#fce3da"
      },
      {
        "value": "b1",
        "en": "1801.0 – 1962.0 °C·d",
        "de": "1801,0 – 1962,0 °C·d",
        "color": "#eb5b25"
      },
      {
        "value": "b2",
        "en": "1962.0 – 2043.0 °C·d",
        "de": "1962,0 – 2043,0 °C·d",
        "color": "#dc4b14"
      },
      {
        "value": "b3",
        "en": "> 2043.0 °C·d",
        "de": "> 2043,0 °C·d",
        "color": "#bb3f11"
      }
    ],
    "change": {
      "2041_2070": [
        {
          "value": "b0",
          "en": "< +619.0 °C·d",
          "de": "< +619,0 °C·d",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+619.0 – +634.0 °C·d",
          "de": "+619,0 – +634,0 °C·d",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+634.0 – +650.0 °C·d",
          "de": "+634,0 – +650,0 °C·d",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+650.0 – +670.0 °C·d",
          "de": "+650,0 – +670,0 °C·d",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +670.0 °C·d",
          "de": "> +670,0 °C·d",
          "color": "#9f350e"
        }
      ],
      "2071_2100": [
        {
          "value": "b0",
          "en": "< +1082.0 °C·d",
          "de": "< +1082,0 °C·d",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+1082.0 – +1107.0 °C·d",
          "de": "+1082,0 – +1107,0 °C·d",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+1107.0 – +1133.0 °C·d",
          "de": "+1107,0 – +1133,0 °C·d",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+1133.0 – +1153.0 °C·d",
          "de": "+1133,0 – +1153,0 °C·d",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +1153.0 °C·d",
          "de": "> +1153,0 °C·d",
          "color": "#9f350e"
        }
      ]
    }
  },
  "bio1": {
    "baseline": [
      {
        "value": "b0",
        "en": "< 8.8 °C",
        "de": "< 8,8 °C",
        "color": "#fce3da"
      },
      {
        "value": "b1",
        "en": "8.8 – 9.2 °C",
        "de": "8,8 – 9,2 °C",
        "color": "#eb5b25"
      },
      {
        "value": "b2",
        "en": "9.2 – 9.4 °C",
        "de": "9,2 – 9,4 °C",
        "color": "#dc4b14"
      },
      {
        "value": "b3",
        "en": "> 9.4 °C",
        "de": "> 9,4 °C",
        "color": "#bb3f11"
      }
    ],
    "change": {
      "2041_2070": [
        {
          "value": "b0",
          "en": "< +2.5 °C",
          "de": "< +2,5 °C",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+2.5 – +2.6 °C",
          "de": "+2,5 – +2,6 °C",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+2.6 – +2.7 °C",
          "de": "+2,6 – +2,7 °C",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+2.7 – +2.8 °C",
          "de": "+2,7 – +2,8 °C",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +2.8 °C",
          "de": "> +2,8 °C",
          "color": "#9f350e"
        }
      ],
      "2071_2100": [
        {
          "value": "b0",
          "en": "< +3.9 °C",
          "de": "< +3,9 °C",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+3.9 – +4.0 °C",
          "de": "+3,9 – +4,0 °C",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+4.0 – +4.1 °C",
          "de": "+4,0 – +4,1 °C",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+4.1 – +4.2 °C",
          "de": "+4,1 – +4,2 °C",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +4.2 °C",
          "de": "> +4,2 °C",
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
        "en": "595.0 – 644.0 mm",
        "de": "595,0 – 644,0 mm",
        "color": "#008581"
      },
      {
        "value": "b2",
        "en": "644.0 – 804.0 mm",
        "de": "644,0 – 804,0 mm",
        "color": "#005754"
      },
      {
        "value": "b3",
        "en": "> 804.0 mm",
        "de": "> 804,0 mm",
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
        "en": "< 184.0 mm",
        "de": "< 184,0 mm",
        "color": "#00b3ad"
      },
      {
        "value": "b1",
        "en": "184.0 – 196.0 mm",
        "de": "184,0 – 196,0 mm",
        "color": "#008581"
      },
      {
        "value": "b2",
        "en": "196.0 – 216.0 mm",
        "de": "196,0 – 216,0 mm",
        "color": "#005754"
      },
      {
        "value": "b3",
        "en": "> 216.0 mm",
        "de": "> 216,0 mm",
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
