// Placeholder chart data per thematic layer. In Phase 4 these values will be
// computed per-LL from the geodata pipeline; for now they match the wireframe
// so the UI port stays faithful.

export const CHART_DATA = {
  agriculture: {
    bars: [
      { key: 'arableLand', v: 58, c: '#c2e077' },
      { key: 'forest', v: 22, c: '#276d4e' },
      { key: 'grassland', v: 14, c: '#83d2af' },
      { key: 'settlement', v: 4, c: '#b5ad9e' },
      { key: 'water', v: 2, c: '#8ffffc' },
    ],
  },
  climate: {
    bars: [
      { key: 'jan', v: 1, c: '#00b3ad' },
      { key: 'mar', v: 6, c: '#5ec597' },
      { key: 'may', v: 14, c: '#c2e077' },
      { key: 'jul', v: 19, c: '#f29673' },
      { key: 'sep', v: 14, c: '#c2e077' },
      { key: 'nov', v: 5, c: '#5ec597' },
    ],
  },
  soil: {
    bars: [
      { key: 'sandyLoam', v: 42, c: '#d4b483' },
      { key: 'loam', v: 28, c: '#c4a870' },
      { key: 'clayLoam', v: 18, c: '#8a6a3e' },
      { key: 'peat', v: 8, c: '#5a3e28' },
      { key: 'other', v: 4, c: '#b0a090' },
    ],
  },
  economic: {
    bars: [
      { key: 'under10', v: 24, c: '#eb5b25' },
      { key: 'from10To50', v: 31, c: '#dc4b14' },
      { key: 'from50To200', v: 28, c: '#bb3f11' },
      { key: 'over200', v: 17, c: '#7e2b0c' },
    ],
  },
}
