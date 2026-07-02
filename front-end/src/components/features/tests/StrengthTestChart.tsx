import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { components } from '@/api/schema'

type ExerciseHistory = components['schemas']['ExerciseHistory']

interface StrengthTestChartProps {
  exercise: ExerciseHistory
}

/** Short day/month label for the x-axis, e.g. "26 jun". */
function shortDate(value: string): string {
  return new Date(value).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })
}

/** A small line chart of one exercise's recent test results (kg), with the current
 *  target load drawn as a horizontal reference line. */
function StrengthTestChart({ exercise }: StrengthTestChartProps) {
  const target = exercise.target_weight_kg
  const data = exercise.history.map((point) => ({
    date: shortDate(point.performed_at),
    weight: point.actual_weight_kg,
  }))

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickMargin={8} />
          <YAxis
            stroke="#94a3b8"
            fontSize={12}
            // Include the target in the range so its line is always visible.
            domain={[
              (dataMin: number) => Math.floor(Math.min(dataMin, target ?? dataMin) - 2),
              (dataMax: number) => Math.ceil(Math.max(dataMax, target ?? dataMax) + 2),
            ]}
            tickFormatter={(value: number) => value.toFixed(0)}
            width={40}
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
          {target != null && (
            <ReferenceLine
              y={target}
              stroke="#34d399"
              strokeDasharray="4 4"
              label={{
                value: `Objetivo ${target} kg`,
                position: 'insideTopRight',
                fill: '#34d399',
                fontSize: 11,
              }}
            />
          )}
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

export default StrengthTestChart
