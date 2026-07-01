import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { components } from '@/api/schema'

type SpeedTestLog = components['schemas']['SpeedTestLogSummaryResponse']

/** The team's target 25 m time band (seconds), shaded as a horizontal band. */
const GOAL_MIN_SECONDS = 12.5
const GOAL_MAX_SECONDS = 13

interface SpeedTestChartProps {
  // Oldest first, so the line reads left-to-right.
  logs: SpeedTestLog[]
}

/** Short day/month label for the x-axis, e.g. "26 jun". */
function shortDate(value: string): string {
  return new Date(value).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })
}

/** A small line chart of the athlete's recent 25 m speed-test times (s), with the
 *  team's target time band shaded. */
function SpeedTestChart({ logs }: SpeedTestChartProps) {
  const data = logs.map((log) => ({
    date: shortDate(log.performed_at),
    seconds: log.seconds,
  }))

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickMargin={8} />
          <YAxis
            stroke="#94a3b8"
            fontSize={12}
            // Include the goal band in the range so it's always visible.
            domain={[
              (dataMin: number) => Math.min(dataMin, GOAL_MIN_SECONDS) - 1,
              (dataMax: number) => Math.max(dataMax, GOAL_MAX_SECONDS) + 1,
            ]}
            tickFormatter={(value: number) => value.toFixed(1)}
            width={48}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '0.5rem',
              color: '#e2e8f0',
            }}
            labelStyle={{ color: '#94a3b8' }}
            formatter={(value: number) => [`${value} s`, 'Tiempo']}
          />
          <ReferenceArea
            y1={GOAL_MIN_SECONDS}
            y2={GOAL_MAX_SECONDS}
            fill="#34d399"
            fillOpacity={0.15}
            stroke="#34d399"
            strokeOpacity={0.4}
            strokeDasharray="4 4"
            label={{
              value: `Objetivo ${GOAL_MIN_SECONDS}–${GOAL_MAX_SECONDS} s`,
              position: 'insideTopRight',
              fill: '#34d399',
              fontSize: 12,
            }}
          />
          <Line
            type="monotone"
            dataKey="seconds"
            stroke="#818cf8"
            strokeWidth={2}
            dot={{ r: 3, fill: '#818cf8' }}
            activeDot={{ r: 5 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default SpeedTestChart
