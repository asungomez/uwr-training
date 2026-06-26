import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { components } from '@/api/schema'

type BodyweightLog = components['schemas']['BodyweightLogResponse']

interface BodyweightChartProps {
  // Oldest first, so the line reads left-to-right.
  logs: BodyweightLog[]
}

/** Short day/month label for the x-axis, e.g. "26 jun". */
function shortDate(value: string): string {
  return new Date(value).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })
}

/** A small line chart of the athlete's recent body-weight measurements (kg). */
function BodyweightChart({ logs }: BodyweightChartProps) {
  const data = logs.map((log) => ({
    date: shortDate(log.recorded_at),
    weight: log.weight_kg,
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
            domain={['dataMin - 1', 'dataMax + 1']}
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
            formatter={(value: number) => [`${value} kg`, 'Peso']}
          />
          <Line
            type="monotone"
            dataKey="weight"
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

export default BodyweightChart
