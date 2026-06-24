import { Repeat } from 'lucide-react'

import type { components } from '@/api/schema'

import { formatDuration } from './cardioFormat'

type CardioItemResponse = components['schemas']['CardioItemResponse']
type IntervalResponse = components['schemas']['IntervalResponse']

function intervalLabel(interval: IntervalResponse): string {
  const duration = formatDuration(interval.duration_seconds)
  if (interval.kind === 'rest') return `${duration} descanso`
  return interval.intensity_pct != null ? `${duration} · ${interval.intensity_pct}%` : duration
}

/** Render one cardio item on the detail page: a note as plain text, or a block as
 *  its round (the ordered intervals) with its repeat count and trailing rest. */
function CardioItemView({ item }: { item: CardioItemResponse }) {
  if (item.kind === 'note') {
    return <p className="text-sm text-slate-400">{item.text}</p>
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
        <Repeat size={14} className="text-indigo-400" />
        {item.repeats > 1 ? `Repetir ${item.repeats} veces` : 'Una vez'}
      </div>
      <ol className="mt-3 flex list-decimal flex-col gap-1 pl-5 text-sm text-slate-300 marker:text-slate-500">
        {item.intervals.map((interval) => (
          <li key={interval.id} className={interval.kind === 'rest' ? 'text-slate-400' : ''}>
            {intervalLabel(interval)}
          </li>
        ))}
      </ol>
      {item.rest_seconds != null && item.rest_seconds > 0 && (
        <p className="mt-3 text-sm text-slate-400">
          Después: {formatDuration(item.rest_seconds)} de descanso
        </p>
      )}
    </div>
  )
}

export default CardioItemView
