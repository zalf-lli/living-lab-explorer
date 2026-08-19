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
        "en": "< 1735.0 °C·d",
        "de": "< 1735,0 °C·d",
        "color": "#fce3da"
      },
      {
        "value": "b1",
        "en": "1735.0 – 1888.0 °C·d",
        "de": "1735,0 – 1888,0 °C·d",
        "color": "#eb5b25"
      },
      {
        "value": "b2",
        "en": "1888.0 – 2025.0 °C·d",
        "de": "1888,0 – 2025,0 °C·d",
        "color": "#dc4b14"
      },
      {
        "value": "b3",
        "en": "> 2025.0 °C·d",
        "de": "> 2025,0 °C·d",
        "color": "#bb3f11"
      }
    ],
    "change": {
      "2041_2070": [
        {
          "value": "b0",
          "en": "< +615.0 °C·d",
          "de": "< +615,0 °C·d",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+615.0 – +628.0 °C·d",
          "de": "+615,0 – +628,0 °C·d",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+628.0 – +643.0 °C·d",
          "de": "+628,0 – +643,0 °C·d",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+643.0 – +655.0 °C·d",
          "de": "+643,0 – +655,0 °C·d",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +655.0 °C·d",
          "de": "> +655,0 °C·d",
          "color": "#9f350e"
        }
      ],
      "2071_2100": [
        {
          "value": "b0",
          "en": "< +1072.0 °C·d",
          "de": "< +1072,0 °C·d",
          "color": "#fce3da"
        },
        {
          "value": "b1",
          "en": "+1072.0 – +1098.0 °C·d",
          "de": "+1072,0 – +1098,0 °C·d",
          "color": "#eb5b25"
        },
        {
          "value": "b2",
          "en": "+1098.0 – +1122.0 °C·d",
          "de": "+1098,0 – +1122,0 °C·d",
          "color": "#dc4b14"
        },
        {
          "value": "b3",
          "en": "+1122.0 – +1140.0 °C·d",
          "de": "+1122,0 – +1140,0 °C·d",
          "color": "#bb3f11"
        },
        {
          "value": "b4",
          "en": "> +1140.0 °C·d",
          "de": "> +1140,0 °C·d",
          "color": "#9f350e"
        }
      ]
    }
  },
  "bio1": {
    "baseline": [
      {
        "value": "b0",
        "en": "< 8.6 °C",
        "de": "< 8,6 °C",
        "color": "#fce3da"
      },
      {
        "value": "b1",
        "en": "8.6 – 9.1 °C",
        "de": "8,6 – 9,1 °C",
        "color": "#eb5b25"
      },
      {
        "value": "b2",
        "en": "9.1 – 9.4 °C",
        "de": "9,1 – 9,4 °C",
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
        "en": "< 589.0 mm",
        "de": "< 589,0 mm",
        "color": "#00b3ad"
      },
      {
        "value": "b1",
        "en": "589.0 – 741.0 mm",
        "de": "589,0 – 741,0 mm",
        "color": "#008581"
      },
      {
        "value": "b2",
        "en": "741.0 – 844.0 mm",
        "de": "741,0 – 844,0 mm",
        "color": "#005754"
      },
      {
        "value": "b3",
        "en": "> 844.0 mm",
        "de": "> 844,0 mm",
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
        "en": "184.0 – 202.0 mm",
        "de": "184,0 – 202,0 mm",
        "color": "#008581"
      },
      {
        "value": "b2",
        "en": "202.0 – 225.0 mm",
        "de": "202,0 – 225,0 mm",
        "color": "#005754"
      },
      {
        "value": "b3",
        "en": "> 225.0 mm",
        "de": "> 225,0 mm",
        "color": "#00413f"
      }
    ],
    "change": {
      "2041_2070": [
        {
          "value": "b0",
          "en": "< -6.0 %",
          "de": "< -6,0 %",
          "color": "#00b3ad"
        },
        {
          "value": "b1",
          "en": "-6.0 – -5.5 %",
          "de": "-6,0 – -5,5 %",
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
          "en": "-5.0 – -4.5 %",
          "de": "-5,0 – -4,5 %",
          "color": "#00413f"
        },
        {
          "value": "b4",
          "en": "> -4.5 %",
          "de": "> -4,5 %",
          "color": "#00312f"
        }
      ],
      "2071_2100": [
        {
          "value": "b0",
          "en": "< -9.0 %",
          "de": "< -9,0 %",
          "color": "#00b3ad"
        },
        {
          "value": "b1",
          "en": "-9.0 – -8.5 %",
          "de": "-9,0 – -8,5 %",
          "color": "#008581"
        },
        {
          "value": "b2",
          "en": "-8.5 – -8.0 %",
          "de": "-8,5 – -8,0 %",
          "color": "#005754"
        },
        {
          "value": "b3",
          "en": "-8.0 – -5.5 %",
          "de": "-8,0 – -5,5 %",
          "color": "#00413f"
        },
        {
          "value": "b4",
          "en": "> -5.5 %",
          "de": "> -5,5 %",
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
