import { useTranslation } from 'react-i18next'
import { useChartData } from '../hooks/useChartData.js'
import { ChartLoading, ChartError, ChartEmpty, ChartSourceFooter } from './ChartStates.jsx'
import { CLIMATE_VARIABLES } from '../data/layers.js'
import { C } from '../theme.js'

// Fixed per-variable line colours (UI-5), reusing the exact hues already used by
// CLIMATE_HEAT_RAMP / CLIMATE_WATER_RAMP in layers.js - zero new hex codes.
const CLIMATE_LINE_COLORS = {
  gdd: C.orange,
  bio1: C.orangeDeep,
  bio12: C.teal,
  bio18: C.tealMid,
}
const CLIMATE_LINE_COLOR_CYCLE = [C.orange, C.orangeDeep, C.teal, C.tealMid]

export function LineChart({ layer, ll, compact = false, minHeightWhenEmpty }) {
  const { i18n } = useTranslation()
  const { data, loading, error } = useChartData(layer, ll?.slug)
  const lang = i18n.language?.startsWith('de') ? 'de' : 'en'
  const locale = i18n.language === 'de' ? 'de-DE' : 'en-US'

  if (loading) return <ChartLoading minHeight={minHeightWhenEmpty} />
  if (error) return <ChartError minHeight={minHeightWhenEmpty} />
  if (
    data == null ||
    !Array.isArray(data.lines) ||
    data.lines.length === 0 ||
    !Array.isArray(data.x_axis) ||
    data.x_axis.length === 0
  ) {
    if (minHeightWhenEmpty == null) return null
    return <ChartEmpty minHeight={minHeightWhenEmpty} />
  }

  const values = data.lines
    .flatMap((l) => l.points.map((p) => p.value))
    .filter((v) => Number.isFinite(v))

  if (values.length === 0) {
    if (minHeightWhenEmpty == null) return null
    return <ChartEmpty minHeight={minHeightWhenEmpty} />
  }

  const rawMin = Math.min(0, ...values)
  const rawMax = Math.max(0, ...values)
  const span = rawMax - rawMin || 1
  const min = rawMin - span * 0.1
  const max = rawMax + span * 0.1
  const yPct = (v) => ((max - v) / (max - min)) * 100

  const useIndexColor = CLIMATE_VARIABLES.length === data.lines.length
  const colorForLine = (index) =>
    useIndexColor
      ? (CLIMATE_LINE_COLORS[CLIMATE_VARIABLES[index]?.id] ?? CLIMATE_LINE_COLOR_CYCLE[index % 4])
      : CLIMATE_LINE_COLOR_CYCLE[index % 4]

  const unit = data.unit?.[lang] ?? data.unit?.en ?? ''

  return (
    <div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
        {data.lines.map((line, i) => (
          <div key={`legend-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: 4,
                background: colorForLine(i),
                flexShrink: 0,
              }}
            />
            <div style={{ fontSize: 11, color: C.black, opacity: 0.65 }}>
              {line.label?.[lang] ?? line.label?.en}
            </div>
          </div>
        ))}
      </div>

      <div style={{ position: 'relative', height: compact ? 150 : 200, width: '100%' }}>
        <div
          style={{
            position: 'absolute',
            top: `${yPct(0)}%`,
            left: 0,
            right: 0,
            height: 0,
            borderTop: `1px dashed ${C.mutedLight}`,
          }}
        />
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
          aria-hidden="true"
        >
          {data.lines.map((line, lineIndex) => {
            const [p0, p1] = line.points
            if (!Number.isFinite(p0?.value) || !Number.isFinite(p1?.value)) return null
            return (
              <polyline
                key={`line-${lineIndex}`}
                points={`25,${yPct(p0.value)} 75,${yPct(p1.value)}`}
                fill="none"
                stroke={colorForLine(lineIndex)}
                strokeWidth={2}
                vectorEffect="non-scaling-stroke"
              />
            )
          })}
        </svg>
        {data.lines.flatMap((line, lineIndex) =>
          line.points.map((point, pointIndex) => {
            if (!Number.isFinite(point?.value)) return null
            const x = pointIndex === 0 ? 25 : 75
            const y = yPct(point.value)
            const color = colorForLine(lineIndex)
            return (
              <div key={`${lineIndex}-${pointIndex}`}>
                <div
                  style={{
                    position: 'absolute',
                    left: `${x}%`,
                    top: `${y}%`,
                    width: 8,
                    height: 8,
                    borderRadius: 4,
                    background: color,
                    transform: 'translate(-50%, -50%)',
                  }}
                />
                <div
                  style={{
                    position: 'absolute',
                    left: `${x}%`,
                    top: `${y}%`,
                    transform: 'translate(-50%, -140%)',
                    fontSize: 11,
                    fontWeight: 700,
                    color,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {`${Number(point.value).toLocaleString(locale, {
                    signDisplay: 'exceptZero',
                    maximumFractionDigits: 1,
                  })}${unit}`}
                </div>
              </div>
            )
          })
        )}
      </div>

      <div style={{ display: 'flex' }}>
        <div
          style={{
            flex: 1,
            textAlign: 'center',
            fontSize: 11,
            color: C.black,
            opacity: 0.65,
            marginTop: 4,
          }}
        >
          {data.x_axis[0]?.label?.[lang] ?? data.x_axis[0]?.label?.en}
        </div>
        <div
          style={{
            flex: 1,
            textAlign: 'center',
            fontSize: 11,
            color: C.black,
            opacity: 0.65,
            marginTop: 4,
          }}
        >
          {data.x_axis[1]?.label?.[lang] ?? data.x_axis[1]?.label?.en}
        </div>
      </div>

      <ChartSourceFooter layer={layer} />
    </div>
  )
}
